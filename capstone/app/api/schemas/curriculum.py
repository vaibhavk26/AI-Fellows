from uuid import UUID

from pydantic import PositiveInt

from app.api.schemas.base import BaseSchema


class SubjectResponse(BaseSchema):
    id: UUID
    name: str
    class_level: int


class ChapterResponse(BaseSchema):
    id: UUID
    subject_id: UUID
    name: str
    display_order: PositiveInt


class TopicResponse(BaseSchema):
    id: UUID
    chapter_id: UUID
    name: str
    display_order: PositiveInt