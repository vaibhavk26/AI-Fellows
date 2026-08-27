from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    ForeignKey,
    Index,
    Numeric,
    SmallInteger,
    String,
    TIMESTAMP,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID

from app.db.models.base import Base


class StudentAttempt(Base):
    __tablename__ = "student_attempts"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    exam_id = Column(UUID(as_uuid=True), ForeignKey("exams.id", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False)
    student_id = Column(
        UUID(as_uuid=True),
        ForeignKey("student_profiles.user_id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    status = Column(String(20), nullable=False, server_default=text("'in_progress'"))
    started_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    submitted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    score = Column(Numeric(8, 2), nullable=True)
    max_score = Column(SmallInteger, nullable=False)
    percentage = Column(Numeric(6, 2), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint("status IN ('in_progress', 'submitted')", name="ck_attempts_status"),
        CheckConstraint("max_score > 0", name="ck_attempts_max_score"),
        CheckConstraint("score IS NULL OR score >= 0", name="ck_attempts_score"),
        CheckConstraint("percentage IS NULL OR percentage BETWEEN 0 AND 100", name="ck_attempts_percentage"),
        CheckConstraint(
            "(status = 'in_progress' AND submitted_at IS NULL AND score IS NULL AND percentage IS NULL) "
            "OR (status = 'submitted' AND submitted_at IS NOT NULL AND score IS NOT NULL AND percentage IS NOT NULL)",
            name="ck_attempts_result_state",
        ),
        # partial unique index: only one active (in_progress) attempt per exam/student
        Index(
            "uq_student_attempts_active",
            "exam_id",
            "student_id",
            unique=True,
            postgresql_where=text("status = 'in_progress'"),
        ),
    )


class StudentAnswer(Base):
    __tablename__ = "student_answers"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    attempt_id = Column(
        UUID(as_uuid=True), ForeignKey("student_attempts.id", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False
    )
    question_id = Column(
        UUID(as_uuid=True), ForeignKey("questions.id", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False
    )
    submitted_answer = Column(String(4000), nullable=True)
    is_correct = Column(Boolean, nullable=False, server_default=text("false"))
    score_awarded = Column(Numeric(8, 2), nullable=False, server_default=text("0"))
    max_score = Column(SmallInteger, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("attempt_id", "question_id", name="uq_student_answers_attempt_question"),
        CheckConstraint(
            "submitted_answer IS NULL OR length(btrim(submitted_answer)) > 0", name="ck_student_answers_answer"
        ),
        CheckConstraint("score_awarded >= 0", name="ck_student_answers_score"),
        CheckConstraint("max_score > 0", name="ck_student_answers_max_score"),
    )
