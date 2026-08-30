from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, PositiveInt, model_validator

from app.api.schemas.base import BaseSchema
from app.api.schemas.question import QuestionForAttemptResponse


class ExamGenerationRequest(BaseModel):
    subject_id: UUID
    chapter_id: UUID | None = None
    topic_id: UUID | None = None
    difficulty: Literal["easy", "medium", "hard"]
    question_types: list[Literal["mcq", "numerical"]]
    question_count: int = Field(ge=1, le=50)
    time_limit_minutes: int = Field(ge=1, le=180)
    title: str | None = Field(default=None, max_length=200)

    @model_validator(mode="after")
    def require_unique_question_types(self) -> "ExamGenerationRequest":
        if not self.question_types or len(self.question_types) != len(set(self.question_types)):
            raise ValueError("question_types must be non-empty and contain no duplicates")
        return self


class ExamQuestionResponse(BaseSchema):
    id: UUID
    sequence_no: PositiveInt
    question: QuestionForAttemptResponse


class ExamResponse(BaseSchema):
    id: UUID
    title: str
    subject_id: UUID
    chapter_id: UUID | None
    topic_id: UUID | None
    question_count: int
    time_limit_minutes: int
    questions: list[ExamQuestionResponse]
    created_by: UUID
    created_at: datetime


class AnswerSubmission(BaseModel):
    question_id: UUID
    answer: str = Field(min_length=1, max_length=4000)


class AttemptSubmissionRequest(BaseModel):
    answers: list[AnswerSubmission]

    @model_validator(mode="after")
    def require_unique_question_ids(self) -> "AttemptSubmissionRequest":
        question_ids = [answer.question_id for answer in self.answers]
        if len(question_ids) != len(set(question_ids)):
            raise ValueError("answers must not contain duplicate question_id values")
        return self


class AttemptStartResponse(BaseSchema):
    id: UUID
    exam_id: UUID
    status: Literal["in_progress"]
    started_at: datetime


class StudentAnswerResult(BaseModel):
    question_id: UUID
    submitted_answer: str | None
    is_correct: bool
    score_awarded: Decimal
    max_score: PositiveInt
    correct_answer: str
    explanation: str


class AttemptResultResponse(BaseModel):
    id: UUID
    exam_id: UUID
    student_id: UUID
    status: Literal["submitted"]
    score: Decimal
    max_score: PositiveInt
    percentage: Decimal
    submitted_at: datetime
    answers: list[StudentAnswerResult]
    weak_topics: list[dict]