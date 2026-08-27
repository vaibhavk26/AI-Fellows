from sqlalchemy import (
    CheckConstraint,
    Column,
    ForeignKey,
    SmallInteger,
    String,
    TIMESTAMP,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.db.models.base import Base


class Exam(Base):
    __tablename__ = "exams"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    title = Column(String(200), nullable=False)
    subject_id = Column(
        UUID(as_uuid=True), ForeignKey("subjects.id", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False
    )
    chapter_id = Column(
        UUID(as_uuid=True), ForeignKey("chapters.id", onupdate="CASCADE", ondelete="RESTRICT"), nullable=True
    )
    topic_id = Column(
        UUID(as_uuid=True), ForeignKey("topics.id", onupdate="CASCADE", ondelete="RESTRICT"), nullable=True
    )
    difficulty = Column(String(20), nullable=False)
    question_types = Column(JSONB, nullable=False)
    question_count = Column(SmallInteger, nullable=False)
    time_limit_minutes = Column(SmallInteger, nullable=False)
    created_by = Column(
        UUID(as_uuid=True), ForeignKey("users.id", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False
    )
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint("difficulty IN ('easy', 'medium', 'hard')", name="ck_exams_difficulty"),
        CheckConstraint("question_count BETWEEN 1 AND 50", name="ck_exams_question_count"),
        CheckConstraint("time_limit_minutes BETWEEN 1 AND 180", name="ck_exams_time_limit"),
        CheckConstraint(
            "jsonb_typeof(question_types) = 'array' AND jsonb_array_length(question_types) > 0",
            name="ck_exams_question_types",
        ),
    )


class ExamQuestion(Base):
    __tablename__ = "exam_questions"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    exam_id = Column(UUID(as_uuid=True), ForeignKey("exams.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    question_id = Column(
        UUID(as_uuid=True), ForeignKey("questions.id", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False
    )
    sequence_no = Column(SmallInteger, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("exam_id", "question_id", name="uq_exam_questions_question"),
        UniqueConstraint("exam_id", "sequence_no", name="uq_exam_questions_sequence"),
        CheckConstraint("sequence_no > 0", name="ck_exam_questions_sequence"),
    )
