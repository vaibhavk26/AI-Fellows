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
    formula: str | None = None
    quantities: dict[str, str] | None = None


def build_generation_prompt(
    request: QuestionGenerationRequest,
    context: str,
    avoid_questions: list[str] | None = None,
) -> str:
    avoid_section = ""
    if avoid_questions:
        avoid_section = "\nDo not repeat any of these existing questions:\n- " + "\n- ".join(avoid_questions)
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
must both contain the same numeric answer, optionally followed by a unit. Also
return `formula` and a `quantities` object containing every variable and its value
with unit, for example `formula: "Q = I * t"`, `quantities: {{"I": "0.6 A", "t": "4 min"}}`.
Numerical questions must be solvable using only `+`, `-`, `*`, `/`, `**`, parentheses,
numeric constants, and the named variables in `quantities`. Do not use trigonometric,
logarithmic, root, or other functions. Write answers in plain decimal or scientific notation
(for example, `1.24e8 m/s`), never symbols such as `×`, `^`, or `°`.
Do not include markdown or extra text.
{avoid_section}

CURRICULUM CONTEXT:
{context}
"""


def build_numerical_retry_prompt(
    request: QuestionGenerationRequest,
    context: str,
    previous_questions: list[dict],
) -> str:
    return f"""Your previous numerical-question response failed deterministic validation. Replace every
invalid item with a fully valid Grade 10 numerical question and return exactly {request.number_of_questions}
question(s) as a JSON object with a `questions` array and no markdown.

For every question, include:
- `question_type`: `numerical`
- `options`: null
- `correct_answer` and `expected_answer`: the same numeric answer with optional unit
- `formula`: an arithmetic formula using only named variables, `+`, `-`, `*`, `/`, `**`,
  parentheses, and numeric constants; do not use trigonometry or other functions
- `quantities`: an object mapping every formula variable to its numeric value and unit

The formula and quantities must independently calculate the provided answer. Use plain decimal or
scientific notation such as `1.24e8 m/s`; never use `×`, `^`, or `°`. Do not invent missing values;
use only the curriculum context.

PREVIOUS RESPONSE:
{json.dumps(previous_questions)}

CURRICULUM CONTEXT:
{context}
"""


def build_grounding_retry_prompt(
    request: QuestionGenerationRequest,
    context: str,
    previous_questions: list[dict],
) -> str:
    return f"""Your previous Grade 10 question response was not sufficiently grounded in the supplied
curriculum context. Replace every invalid item and return exactly {request.number_of_questions} {request.question_type}
question(s) as a JSON object with a `questions` array and no markdown.

Every replacement must use at least two meaningful terms that occur in the curriculum context. Do not
introduce concepts, facts, formulas, or terminology absent from that context. Preserve these request
requirements exactly: difficulty `{request.difficulty}`, question_type `{request.question_type}`, and marks `{request.marks}`.
Keep the full JSON structure required for the question type, including four non-empty MCQ options when applicable.

PREVIOUS RESPONSE:
{json.dumps(previous_questions)}

CURRICULUM CONTEXT:
{context}
"""


def create_chat_model(max_tokens: int | None = None) -> ChatModel:
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
        request_timeout=settings.llm_timeout_seconds,
        max_tokens=max_tokens if max_tokens is not None else settings.llm_max_tokens,
        max_retries=0,
        # openai/gpt-oss is a reasoning model; without this it can spend the entire
        # completion budget on hidden reasoning tokens and return empty content.
        model_kwargs={"reasoning_effort": "low"},
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
