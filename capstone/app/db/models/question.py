from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    ForeignKey,
    Numeric,
    SmallInteger,
    String,
    TIMESTAMP,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.db.models.base import Base


class Question(Base):
    __tablename__ = "questions"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    subject_id = Column(
        UUID(as_uuid=True), ForeignKey("subjects.id", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False
    )
    chapter_id = Column(
        UUID(as_uuid=True), ForeignKey("chapters.id", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False
    )
    topic_id = Column(
        UUID(as_uuid=True), ForeignKey("topics.id", onupdate="CASCADE", ondelete="SET NULL"), nullable=True
    )
    class_level = Column(SmallInteger, nullable=False, server_default=text("10"))
    question_type = Column(String(30), nullable=False)
    difficulty = Column(String(20), nullable=False)
    bloom_level = Column(String(20), nullable=True)
    marks = Column(SmallInteger, nullable=False)
    question_text = Column(Text, nullable=False)
    options = Column(JSONB, nullable=True)
    correct_answer = Column(Text, nullable=False)
    expected_answer = Column(Text, nullable=False)
    explanation = Column(Text, nullable=False)
    learning_objective = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, server_default=text("'generated'"))
    created_by = Column(
        UUID(as_uuid=True), ForeignKey("users.id", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False
    )
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint("class_level = 10", name="ck_questions_class_level"),
        CheckConstraint(
            "question_type IN ('mcq', 'numerical', 'short_answer', 'long_answer', 'competency')",
            name="ck_questions_type",
        ),
        CheckConstraint("difficulty IN ('easy', 'medium', 'hard')", name="ck_questions_difficulty"),
        CheckConstraint(
            "bloom_level IS NULL OR bloom_level IN ('remember', 'understand', 'apply', 'analyze')",
            name="ck_questions_bloom",
        ),
        CheckConstraint("marks > 0", name="ck_questions_marks"),
        CheckConstraint("status IN ('generated', 'validated', 'rejected', 'approved')", name="ck_questions_status"),
        CheckConstraint(
            "(question_type = 'mcq' AND jsonb_typeof(options) = 'array' AND jsonb_array_length(options) = 4) "
            "OR (question_type <> 'mcq' AND options IS NULL)",
            name="ck_questions_options_shape",
        ),
    )


class QuestionSourceReference(Base):
    __tablename__ = "question_source_references"

    question_id = Column(
        UUID(as_uuid=True), ForeignKey("questions.id", onupdate="CASCADE", ondelete="CASCADE"), primary_key=True
    )
    source_reference_id = Column(
        UUID(as_uuid=True),
        ForeignKey("source_references.id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    )
    relevance_score = Column(Numeric(6, 5), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint("relevance_score IS NULL OR relevance_score BETWEEN 0 AND 1", name="ck_qsr_relevance"),
    )


class QuestionValidationResult(Base):
    __tablename__ = "question_validation_results"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    question_id = Column(
        UUID(as_uuid=True), ForeignKey("questions.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False
    )
    workflow_run_id = Column(String(200), nullable=True)
    status = Column(String(20), nullable=False)
    curriculum_relevance = Column(Boolean, nullable=False)
    answer_correctness = Column(Boolean, nullable=False)
    difficulty_match = Column(Boolean, nullable=False)
    type_match = Column(Boolean, nullable=False)
    duplicate_check = Column(Boolean, nullable=False)
    learning_objective_alignment = Column(Boolean, nullable=False)
    failure_reasons = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint("status IN ('validated', 'rejected')", name="ck_qvr_status"),
        CheckConstraint(
            "(status = 'validated' AND curriculum_relevance AND answer_correctness AND difficulty_match "
            "AND type_match AND duplicate_check AND learning_objective_alignment) "
            "OR (status = 'rejected' AND NOT (curriculum_relevance AND answer_correctness AND difficulty_match "
            "AND type_match AND duplicate_check AND learning_objective_alignment))",
            name="ck_qvr_status_checks",
        ),
        CheckConstraint("jsonb_typeof(failure_reasons) = 'array'", name="ck_qvr_failure_reasons"),
    )
