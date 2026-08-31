from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, PositiveInt

from app.api.schemas.base import BaseSchema


class QuestionOption(BaseModel):
    key: str
    text: str


class SourceReferenceResponse(BaseSchema):
    id: UUID
    document_id: UUID
    page_number: int | None
    chunk_id: str | None
    excerpt: str | None


class QuestionResponse(BaseSchema):
    id: UUID
    subject_id: UUID
    chapter_id: UUID
    topic_id: UUID | None
    class_level: int
    question_type: Literal["mcq", "numerical"]
    difficulty: Literal["easy", "medium", "hard"]
    bloom_level: Literal["remember", "understand", "apply", "analyze"] | None
    marks: PositiveInt
    question_text: str
    options: list[QuestionOption] | None
    expected_answer: str
    explanation: str
    learning_objective: str
    source_references: list[SourceReferenceResponse] = Field(default_factory=list)
    status: Literal["generated", "validated", "rejected"]
    created_by: UUID
    created_at: datetime


class QuestionForAttemptResponse(BaseSchema):
    id: UUID
    topic_id: UUID | None
    question_type: Literal["mcq", "numerical"]
    difficulty: Literal["easy", "medium", "hard"]
    marks: PositiveInt
    question_text: str
    options: list[QuestionOption] | None


class QuestionGenerationRequest(BaseModel):
    subject_id: UUID
    chapter_id: UUID
    topic_id: UUID | None = None
    difficulty: Literal["easy", "medium", "hard"]
    question_type: Literal["mcq", "numerical"]
    marks: PositiveInt
    number_of_questions: int = Field(ge=1, le=50)
    bloom_level: Literal["remember", "understand", "apply", "analyze"] | None = None