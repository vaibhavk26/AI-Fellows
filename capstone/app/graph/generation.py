"""LangGraph workflow for curriculum-grounded question generation."""

from __future__ import annotations

from dataclasses import dataclass
import re
import time
from decimal import Decimal
from pathlib import Path
from typing import Any, TypedDict
from uuid import UUID, uuid4

from langgraph.graph import END, StateGraph
from openai import RateLimitError
from sqlalchemy.orm import Session

from app.agents.generation import (
    ChatModel,
    build_generation_prompt,
    build_grounding_retry_prompt,
    build_numerical_retry_prompt,
    create_chat_model,
    parse_generation_response,
)
from app.api.schemas.question import QuestionGenerationRequest
from app.core.config import get_settings
from app.db.models.curriculum import Chapter, Subject, Topic
from app.db.models.question import Question, QuestionSourceReference, QuestionValidationResult
from app.rag.pipeline import FaissStore, RetrievalResult
from app.services.numerical import parse_numeric_answer
from app.services.calculation import calculate_formula


class WorkflowError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


class GeneratedQuestion(TypedDict, total=False):
    question_text: str
    options: list[dict[str, str]] | None
    correct_answer: str
    expected_answer: str
    explanation: str
    learning_objective: str
    difficulty: str
    question_type: str
    formula: str | None
    quantities: dict[str, str] | None


class ValidationSummary(TypedDict):
    question_id: UUID
    status: str
    curriculum_relevance: bool
    answer_correctness: bool
    difficulty_match: bool
    type_match: bool
    duplicate_check: bool
    learning_objective_alignment: bool
    failure_reasons: list[str]


class WorkflowState(TypedDict, total=False):
    request: QuestionGenerationRequest
    user_id: UUID
    workflow_run_id: str
    context: list[RetrievalResult]
    generated: list[GeneratedQuestion]
    validations: list[ValidationSummary]
    questions: list[Question]


@dataclass
class QuestionGenerationWorkflow:
    database: Session
    request: QuestionGenerationRequest
    user_id: UUID
    model: ChatModel | None = None
    store: FaissStore | None = None
    commit: bool = True
    avoid_question_texts: list[str] | None = None

    @staticmethod
    def _normalize_options(options: object) -> list[dict[str, str]] | None:
        if isinstance(options, dict):
            return [{"key": key, "text": str(options[key])} for key in ("A", "B", "C", "D") if key in options]
        if isinstance(options, list):
            normalized: list[dict[str, str]] = []
            for option in options:
                if not isinstance(option, dict):
                    continue
                if "key" in option and "text" in option:
                    normalized.append({"key": str(option["key"]).strip().upper(), "text": str(option["text"]).strip()})
                elif len(option) == 1:
                    key, text = next(iter(option.items()))
                    normalized.append({"key": str(key).strip().upper(), "text": str(text).strip()})
            order = {key: index for index, key in enumerate(("A", "B", "C", "D"))}
            return sorted(normalized, key=lambda option: order.get(option["key"], len(order)))
        return None

    @classmethod
    def _normalize_generated_item(cls, item: GeneratedQuestion) -> GeneratedQuestion:
        normalized = dict(item)
        normalized["options"] = cls._normalize_options(item.get("options"))
        if str(item.get("question_type", "")).casefold() == "mcq":
            normalized["question_type"] = "mcq"
            normalized["correct_answer"] = str(item.get("correct_answer", "")).strip().upper()
            normalized["expected_answer"] = str(item.get("expected_answer", "")).strip().upper()
        else:
            normalized["question_type"] = str(item.get("question_type", "")).strip().casefold()
            normalized["correct_answer"] = " ".join(str(item.get("correct_answer", "")).strip().casefold().split())
            normalized["expected_answer"] = " ".join(str(item.get("expected_answer", "")).strip().casefold().split())
            normalized["options"] = None
            normalized["formula"] = item.get("formula")
            normalized["quantities"] = item.get("quantities")
        return normalized

    def run(self) -> dict[str, Any]:
        graph = StateGraph(WorkflowState)
        graph.add_node("retrieve_context", self.retrieve_context)
        graph.add_node("generate_questions", self.generate_questions)
        graph.add_node("validate_questions", self.validate_questions)
        graph.add_node("save", self.save)
        graph.set_entry_point("retrieve_context")
        graph.add_edge("retrieve_context", "generate_questions")
        graph.add_edge("generate_questions", "validate_questions")
        graph.add_edge("validate_questions", "save")
        graph.add_edge("save", END)
        try:
            result = graph.compile().invoke({
                "request": self.request,
                "user_id": self.user_id,
                "workflow_run_id": str(uuid4()),
            })
            questions = result["questions"]
            validations = result["validations"]
            return {
                "questions": questions,
                "validation": validations,
                "meta": {
                    "requested": self.request.number_of_questions,
                    "validated": sum(item["status"] == "validated" for item in validations),
                    "rejected": sum(item["status"] == "rejected" for item in validations),
                },
            }
        except WorkflowError:
            self.database.rollback()
            raise
        except Exception as exc:
            self.database.rollback()
            raise WorkflowError("AI_PROVIDER_UNAVAILABLE", "Question generation could not be completed") from exc

    def retrieve_context(self, state: WorkflowState) -> WorkflowState:
        request = state["request"]
        subject = self.database.query(Subject).filter_by(id=request.subject_id, class_level=10).one_or_none()
        chapter = self.database.query(Chapter).filter_by(id=request.chapter_id, subject_id=request.subject_id).one_or_none()
        topic = None
        if request.topic_id:
            topic = self.database.query(Topic).filter_by(id=request.topic_id, chapter_id=request.chapter_id).one_or_none()
        if not subject or not chapter or (request.topic_id and not topic):
            raise WorkflowError("INVALID_CURRICULUM_SCOPE", "Chapter and topic must belong to the subject")
        store = self.store or FaissStore(Path(get_settings().vector_db_path))
        context = store.search(
            f"{chapter.name} {topic.name if topic else ''} {request.question_type} {request.difficulty}",
            limit=5, subject_id=subject.id, chapter_id=chapter.id, topic_id=topic.id if topic else None,
        )
        if not context:
            raise WorkflowError("VECTOR_STORE_UNAVAILABLE", "No curriculum context was found for this scope")
        return {**state, "context": context}

    def generate_questions(self, state: WorkflowState) -> WorkflowState:
        model = self.model or create_chat_model(max_tokens=self._estimate_max_tokens(state["request"]))
        context = "\n\n".join(item.text for item in state["context"])
        try:
            response = self._invoke_with_rate_limit_retry(
                model, build_generation_prompt(state["request"], context, self.avoid_question_texts)
            )
            generated = parse_generation_response(response)
            generated = [self._normalize_generated_item(item) for item in generated]
            if state["request"].question_type == "numerical" and any(
                not self._has_valid_numerical_calculation(item) for item in generated
            ):
                retry_response = self._invoke_with_rate_limit_retry(
                    model, build_numerical_retry_prompt(state["request"], context, generated)
                )
                generated = parse_generation_response(retry_response)
            generated = [self._normalize_generated_item(item) for item in generated]
            if any(not self._is_curriculum_relevant(item, state.get("context", [])) for item in generated):
                retry_response = self._invoke_with_rate_limit_retry(
                    model, build_grounding_retry_prompt(state["request"], context, generated)
                )
                generated = [
                    self._normalize_generated_item(item)
                    for item in parse_generation_response(retry_response)
                ]
        except RateLimitError as exc:
            raise WorkflowError(
                "AI_PROVIDER_RATE_LIMITED",
                "The Groq provider rate limit is still exceeded after retrying. Please wait about a "
                "minute, then try again with fewer questions.",
            ) from exc
        except Exception as exc:
            raise WorkflowError("AI_PROVIDER_UNAVAILABLE", "The Groq generation request failed") from exc
        if len(generated) != state["request"].number_of_questions:
            raise WorkflowError("AI_PROVIDER_UNAVAILABLE", "The provider returned an unexpected question count")
        return {**state, "generated": generated}

    @staticmethod
    def _estimate_max_tokens(request: QuestionGenerationRequest) -> int:
        settings = get_settings()
        per_question = 700 if request.question_type == "numerical" else 300
        estimated = 300 + per_question * request.number_of_questions
        return max(512, min(settings.llm_max_tokens, estimated))

    @staticmethod
    def _invoke_with_rate_limit_retry(model: ChatModel, prompt: str, *, max_attempts: int = 3) -> object:
        last_error: RateLimitError | None = None
        for attempt in range(max_attempts):
            try:
                return model.invoke(prompt)
            except RateLimitError as exc:
                last_error = exc
                if attempt < max_attempts - 1:
                    time.sleep(QuestionGenerationWorkflow._rate_limit_wait_seconds(exc))
        raise last_error

    @staticmethod
    def _rate_limit_wait_seconds(exc: RateLimitError) -> float:
        header_value = getattr(getattr(exc, "response", None), "headers", {}).get("retry-after")
        if header_value is None:
            match = re.search(r"try again in ([\d.]+)", str(exc))
            header_value = match.group(1) if match else None
        return min(float(header_value), 15.0) if header_value else 5.0

    @staticmethod
    def _has_valid_numerical_calculation(item: GeneratedQuestion) -> bool:
        correct_answer = parse_numeric_answer(str(item.get("correct_answer", "")).strip())
        expected_answer = parse_numeric_answer(str(item.get("expected_answer", "")).strip())
        formula = item.get("formula")
        quantities = item.get("quantities")
        if not correct_answer or not expected_answer or correct_answer != expected_answer:
            return False
        if not isinstance(formula, str) or not isinstance(quantities, dict):
            return False
        calculated = calculate_formula(formula, quantities)
        expected_value = expected_answer[0]
        return calculated is not None and abs(calculated - expected_value) <= max(
            abs(expected_value) * Decimal("0.0001"), Decimal("0.000001")
        )

    @staticmethod
    def _is_curriculum_relevant(item: GeneratedQuestion, context: list[RetrievalResult]) -> bool:
        stop_words = {
            "what", "which", "following", "calculate", "class", "students", "question",
            "answer", "using", "find", "the", "and", "from", "with", "does", "are",
        }
        context_terms = {
            term.casefold()
            for result in context
            for term in re.findall(r"[A-Za-z][A-Za-z0-9]+", result.text)
            if len(term) > 3 and term.casefold() not in stop_words
        }
        evidence_text = " ".join([
            str(item.get("question_text", "")),
            " ".join(str(option.get("text", "")) for option in item.get("options") or [] if isinstance(option, dict)),
            str(item.get("explanation", "")),
            str(item.get("learning_objective", "")),
        ])
        evidence_terms = set(re.findall(r"[A-Za-z][A-Za-z0-9]+", evidence_text.casefold())) - stop_words
        return not context_terms or len(context_terms.intersection(evidence_terms)) >= 2

    def validate_questions(self, state: WorkflowState) -> WorkflowState:
        request = state["request"]
        seen: set[str] = set()
        existing_texts = {
            " ".join(text.casefold().split())
            for (text,) in self.database.query(Question.question_text).filter(
                Question.subject_id == request.subject_id,
                Question.chapter_id == request.chapter_id,
                Question.topic_id == request.topic_id,
                Question.question_type == request.question_type,
                Question.difficulty == request.difficulty,
            ).all()
        } if getattr(self, "database", None) is not None else set()
        validations: list[ValidationSummary] = []
        for item in state["generated"]:
            item = self._normalize_generated_item(item)
            failures: list[str] = []
            question_text = str(item.get("question_text", "")).strip()
            question_type = item.get("question_type")
            difficulty = item.get("difficulty")
            options = self._normalize_options(item.get("options"))
            correct_answer = str(item.get("correct_answer", "")).strip()
            expected_answer = str(item.get("expected_answer", "")).strip()
            answer_correctness = bool(correct_answer and expected_answer)
            if request.question_type == "numerical":
                correct_value = parse_numeric_answer(correct_answer)
                expected_value = parse_numeric_answer(expected_answer)
                answer_correctness = bool(correct_value and expected_value and correct_value == expected_value)
            type_match = question_type == request.question_type
            difficulty_match = difficulty == request.difficulty
            if not question_text:
                failures.append("question_text is required")
            if not type_match:
                failures.append("question_type does not match the request")
            if not difficulty_match:
                failures.append("difficulty does not match the request")
            if request.question_type == "mcq":
                keys = [option.get("key") for option in options or [] if isinstance(option, dict)]
                option_texts = [str(option.get("text", "")).strip() for option in options or [] if isinstance(option, dict)]
                if (
                    keys != ["A", "B", "C", "D"]
                    or not all(option_texts)
                    or correct_answer not in keys
                    or expected_answer != correct_answer
                ):
                    answer_correctness = False
                    failures.append("MCQ must have four non-empty options and matching answer keys")
            else:
                if options is not None:
                    failures.append("numerical questions cannot have options")
                if not parse_numeric_answer(correct_answer) or not parse_numeric_answer(expected_answer):
                    answer_correctness = False
                    failures.append("numerical answers must contain a number and optional unit")
                formula = item.get("formula")
                quantities = item.get("quantities")
                calculated = calculate_formula(formula, quantities) if isinstance(formula, str) and isinstance(quantities, dict) else None
                expected_numeric = parse_numeric_answer(expected_answer)
                if calculated is None or expected_numeric is None:
                    answer_correctness = False
                    failures.append("numerical answer requires a safe formula and quantities")
                elif abs(calculated - expected_numeric[0]) > max(abs(expected_numeric[0]) * Decimal("0.0001"), Decimal("0.000001")):
                    answer_correctness = False
                    failures.append("calculated result does not match expected answer")
            if not answer_correctness:
                failures.append("answer data is incomplete")
            duplicate_key = " ".join(question_text.casefold().split())
            duplicate_check = bool(duplicate_key) and duplicate_key not in seen and duplicate_key not in existing_texts
            if not duplicate_check:
                failures.append("duplicate question")
            seen.add(duplicate_key)
            learning_objective_alignment = bool(str(item.get("learning_objective", "")).strip())
            if not learning_objective_alignment:
                failures.append("learning_objective is required")
            curriculum_relevance = self._is_curriculum_relevant(item, state.get("context", []))
            if not curriculum_relevance:
                failures.append("question is not grounded in retrieved curriculum context")
            validations.append({
                "question_id": UUID(int=0), "status": "validated" if not failures else "rejected",
                "curriculum_relevance": curriculum_relevance, "answer_correctness": answer_correctness,
                "difficulty_match": difficulty_match, "type_match": type_match,
                "duplicate_check": duplicate_check, "learning_objective_alignment": learning_objective_alignment,
                "failure_reasons": failures,
            })
        return {**state, "validations": validations}

    def save(self, state: WorkflowState) -> WorkflowState:
        request = state["request"]
        questions: list[Question] = []
        try:
            for item, validation in zip(state["generated"], state["validations"], strict=True):
                item = self._normalize_generated_item(item)
                options = item.get("options") if request.question_type == "mcq" else None
                if request.question_type == "mcq" and (
                    not isinstance(options, list)
                    or [option.get("key") for option in options if isinstance(option, dict)] != ["A", "B", "C", "D"]
                ):
                    options = [{"key": key, "text": ""} for key in ("A", "B", "C", "D")]
                question = Question(
                    subject_id=request.subject_id, chapter_id=request.chapter_id, topic_id=request.topic_id,
                    question_type=request.question_type, difficulty=request.difficulty, bloom_level=request.bloom_level,
                    marks=request.marks, question_text=str(item.get("question_text", "")), options=options,
                    correct_answer=str(item.get("correct_answer", "")), expected_answer=str(item.get("expected_answer", "")),
                    explanation=str(item.get("explanation", "")), learning_objective=str(item.get("learning_objective", "")),
                    status=validation["status"], created_by=state["user_id"],
                )
                self.database.add(question)
                questions.append(question)
            self.database.flush()
            for question, validation in zip(questions, state["validations"], strict=True):
                validation["question_id"] = question.id
                for result in state["context"]:
                    self.database.add(QuestionSourceReference(question_id=question.id, source_reference_id=result.source_reference_id, relevance_score=result.score))
                self.database.add(QuestionValidationResult(question_id=question.id, workflow_run_id=state["workflow_run_id"], status=validation["status"], curriculum_relevance=validation["curriculum_relevance"], answer_correctness=validation["answer_correctness"], difficulty_match=validation["difficulty_match"], type_match=validation["type_match"], duplicate_check=validation["duplicate_check"], learning_objective_alignment=validation["learning_objective_alignment"], failure_reasons=validation["failure_reasons"]))
            if self.commit:
                self.database.commit()
        except Exception as exc:
            self.database.rollback()
            raise WorkflowError("GENERATION_SAVE_FAILED", "Generated questions could not be saved") from exc
        return {**state, "questions": questions}
