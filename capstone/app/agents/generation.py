"""LLM-backed question generation for the MVP workflow."""

import json
import re
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field

from app.api.schemas.question import QuestionGenerationRequest


class ChatModel(Protocol):
    def invoke(self, prompt: str) -> object: ...


class GeneratedQuestionPayload(BaseModel):
    """Typed boundary for provider output before workflow validation."""

    model_config = ConfigDict(extra="ignore")

    question_text: str = Field(min_length=1)
    options: object | None = None
    correct_answer: str = ""
    expected_answer: str = ""
    explanation: str = ""
    learning_objective: str = ""
    difficulty: str = ""
    question_type: str = ""


def build_generation_prompt(request: QuestionGenerationRequest, context: str) -> str:
    return f"""Generate exactly {request.number_of_questions} Grade 10 {request.question_type} question(s).
Difficulty: {request.difficulty}
Marks: {request.marks}
Bloom level: {request.bloom_level or 'understand'}

Use only the curriculum context below. Return a JSON object with a `questions` array.
Each item must contain: question_text, options, correct_answer, expected_answer,
explanation, learning_objective, difficulty, question_type.
For MCQ: options must be a JSON array of exactly four objects with keys A, B, C, and D,
not a keyed JSON object. Every option text must be non-empty. `correct_answer` and `expected_answer` must both be
the same option key (for example, "A"), never a numeric answer or option text.
The numeric or textual answer belongs in the selected option's `text` field.
For numerical: options must be null, and `correct_answer` and `expected_answer`
must both contain the same numeric answer, optionally followed by a unit.
Do not include markdown or extra text.

CURRICULUM CONTEXT:
{context}
"""


def create_chat_model() -> ChatModel:
    from app.core.config import get_settings
    from langchain_openai import ChatOpenAI

    settings = get_settings()
    if settings.llm_provider != "groq" or not settings.groq_api_key:
        raise RuntimeError("Groq provider is not configured")
    return ChatOpenAI(
        model=settings.llm_model,
        temperature=0,
        openai_api_key=settings.groq_api_key,
        openai_api_base=settings.llm_base_url,
    )


def parse_generation_response(response: object) -> list[dict]:
    content = getattr(response, "content", response)
    if not isinstance(content, str):
        raise ValueError("LLM response content must be text")
    content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content.strip(), flags=re.IGNORECASE)
    payload = json.loads(content)
    questions = payload.get("questions") if isinstance(payload, dict) else payload
    if not isinstance(questions, list):
        raise ValueError("LLM response must contain a questions array")
    try:
        return [GeneratedQuestionPayload.model_validate(question).model_dump() for question in questions]
    except Exception as exc:
        raise ValueError("LLM response contains an invalid question structure") from exc
