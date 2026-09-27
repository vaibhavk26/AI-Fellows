from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, model_validator


class AddStudentRequest(BaseModel):
    email: EmailStr


class ExamAssignmentRequest(BaseModel):
    student_ids: list[UUID] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def require_unique_students(self) -> "ExamAssignmentRequest":
        if len(self.student_ids) != len(set(self.student_ids)):
            raise ValueError("student_ids must not contain duplicates")
        return self