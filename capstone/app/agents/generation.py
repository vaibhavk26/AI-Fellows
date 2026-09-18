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


# Arithmetically verified so the model can copy the pattern exactly: mu0/(2*pi) = 2.0e-7,
# so B = 2.0e-7 * I / r = 2.0e-7 * 2.0 / 0.04 = 1.0e-5 T; F = I*L*B = 3.0*0.4*0.05 = 0.06 N.
_NUMERICAL_WORKED_EXAMPLE = """Worked example of a fully self-consistent numerical question (the
formula, when evaluated with these exact quantities, reproduces the stated answer):
{
  "question_text": "A straight wire carries a current of 2.0 A. What is the magnetic field strength at a point 0.04 m from the wire?",
  "question_type": "numerical", "options": null,
  "correct_answer": "1.0e-5 T", "expected_answer": "1.0e-5 T",
  "explanation": "B = mu0 * I / (2 * pi * r) = 1.0e-5 T.",
  "learning_objective": "Apply the magnetic field formula for a long straight conductor.",
  "difficulty": "easy", "formula": "mu0*I/(2*pi*r)", "quantities": {"I": "2.0 A", "r": "0.04 m"}
}
A second example using only supplied quantities, no named constants:
{
  "question_text": "A 0.4 m wire carries 3.0 A in a 0.05 T field perpendicular to it. What force acts on the wire?",
  "question_type": "numerical", "options": null,
  "correct_answer": "0.06 N", "expected_answer": "0.06 N",
  "explanation": "F = I * L * B = 0.06 N.",
  "learning_objective": "Apply the force formula for a current-carrying conductor.",
  "difficulty": "easy", "formula": "I*L*B", "quantities": {"I": "3.0 A", "L": "0.4 m", "B": "0.05 T"}
}
Before finalizing each numerical question, mentally substitute your own `quantities` into your own
`formula` and confirm the result equals your stated `correct_answer`; adjust one of them if they disagree."""


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
logarithmic, root, or other functions. You may use these exact lowercase names directly in
`formula` without adding them to `quantities`: `pi`, `mu0` (permeability of free space),
`e0` (permittivity of free space), `c` (speed of light), `g` (9.8 m/s^2), `k` (Coulomb's
constant). Never write unicode symbols such as `π`, `μ0`, or `Ω`, and never use implicit
multiplication (`2πr` is invalid); always write an explicit `*` between every factor, for
example `mu0*I/(2*pi*r)`. Write answers in plain decimal or scientific notation
(for example, `1.24e8 m/s`), never symbols such as `×`, `^`, or `°`. A unit may be a single
symbol (`N`, `T`, `m`) or a product/quotient of symbols joined with `·` or `/` (for example
`N·m`, `m/s`).
{_NUMERICAL_WORKED_EXAMPLE if request.question_type == "numerical" else ""}
Return syntactically valid JSON: separate array items with a single comma directly between
the closing `}}` and the next opening `{{` (`}},{{`), never insert a stray quote character there.
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

For every question, include ALL of the following fields, even for items that only needed a
formula/quantities repair:
- `question_text`: the full question text
- `question_type`: `numerical`
- `options`: null
- `correct_answer` and `expected_answer`: the same numeric answer with optional unit
- `explanation`: a short explanation of the answer
- `learning_objective`: the learning objective this question assesses
- `difficulty`: `{request.difficulty}`
- `formula`: an arithmetic formula using only named variables, `+`, `-`, `*`, `/`, `**`,
  parentheses, and numeric constants; do not use trigonometry or other functions. You may
  use these exact lowercase names directly without adding them to `quantities`: `pi`, `mu0`,
  `e0`, `c`, `g`, `k`. Never write unicode symbols (`π`, `μ0`, `Ω`) or implicit multiplication
  (`2πr` is invalid); always write an explicit `*`, for example `mu0*I/(2*pi*r)`.
- `quantities`: an object mapping every formula variable to a SINGLE STRING combining its
  numeric value and unit, for example `{{"I": "5.0 A", "r": "0.02 m"}}`. Never use a nested
  object such as `{{"value": 5.0, "unit": "A"}}`; each quantity must be one plain string.

The formula and quantities must independently calculate the provided answer. Use plain decimal or
scientific notation such as `1.24e8 m/s`; never use `×`, `^`, or `°`. A unit may be a single symbol
or a product/quotient of symbols joined with `·` or `/` (for example `N·m`, `m/s`). Do not invent
missing values; use only the curriculum context. Do not omit `question_text`, `explanation`, or
`learning_objective` even when only the formula or quantities need correcting. Separate array items
with a single comma directly between the closing `}}` and the next opening `{{` (`}},{{`), never a
stray quote character.
{_NUMERICAL_WORKED_EXAMPLE}

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


def _repair_stray_quoted_braces(content: str) -> str:
    """Undo an observed gpt-oss quirk where a real `{` between array items gets wrapped in
    stray quotes (e.g. `}},"{","question_text":...`), reading as a one-character string
    instead of the start of the next object."""
    content = content.replace('"{"', "{").replace('"}"', "}")
    content = re.sub(r"\{\s*,", "{", content)
    content = re.sub(r",\s*\}", "}", content)
    return content


def parse_generation_response(response: object) -> list[dict]:
    content = getattr(response, "content", response)
    if not isinstance(content, str):
        raise ValueError("LLM response content must be text")
    content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content.strip(), flags=re.IGNORECASE)
    content = _repair_stray_quoted_braces(content)
    try:
        payload = json.loads(content)
        questions = payload.get("questions") if isinstance(payload, dict) else payload
        if not isinstance(questions, list):
            raise ValueError("LLM response must contain a questions array")
    except (json.JSONDecodeError, ValueError):
        # gpt-oss occasionally corrupts the punctuation between array items (stray quotes,
        # missing braces) in unpredictable shapes. Recover each individually well-formed
        # question object instead of failing the whole batch on one bad separator.
        questions = _extract_json_objects(content)
        if not questions:
            raise ValueError("LLM response must contain a questions array") from None
    questions = [_normalize_quantities(question) for question in questions if isinstance(question, dict)]
    try:
        return [GeneratedQuestionPayload.model_validate(question).model_dump() for question in questions]
    except Exception as exc:
        raise ValueError("LLM response contains an invalid question structure") from exc


def _extract_json_objects(content: str) -> list[dict]:
    """Recover top-level JSON objects even if the punctuation between them is corrupted.

    Scans for balanced `{...}` spans, respecting string literals and escapes, and parses
    each span independently. This is immune to whatever stray characters (extra quotes,
    missing commas, dropped braces) the model inserts between array items, since it never
    relies on that separator punctuation being well-formed.
    """
    array_start = content.find("[")
    scan_target = content[array_start + 1 :] if array_start != -1 else content
    objects: list[dict] = []
    depth = 0
    in_string = False
    escape = False
    start: int | None = None
    for index, char in enumerate(scan_target):
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
            continue
        if char == "{":
            if depth == 0:
                start = index
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0 and start is not None:
                try:
                    objects.append(json.loads(scan_target[start : index + 1]))
                except json.JSONDecodeError:
                    pass
                start = None
    return objects



def _normalize_quantities(question: dict) -> dict:
    """Coerce a {value, unit} quantity object into the required 'value unit' string form."""
    quantities = question.get("quantities")
    if not isinstance(quantities, dict):
        return question
    normalized = {}
    for name, entry in quantities.items():
        if isinstance(entry, dict) and "value" in entry:
            unit = str(entry.get("unit", "")).strip()
            normalized[name] = f"{entry['value']} {unit}".strip()
        else:
            normalized[name] = entry
    return {**question, "quantities": normalized}
