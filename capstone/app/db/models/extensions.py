from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    TIMESTAMP,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.db.models.base import Base


class ExamAssignment(Base):
    __tablename__ = "exam_assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    exam_id = Column(UUID(as_uuid=True), ForeignKey("exams.id", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False)
    student_id = Column(
        UUID(as_uuid=True),
        ForeignKey("student_profiles.user_id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    assigned_by = Column(
        UUID(as_uuid=True),
        ForeignKey("teacher_profiles.user_id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    status = Column(String(20), nullable=False, server_default=text("'assigned'"))
    assigned_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    completed_at = Column(TIMESTAMP(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("exam_id", "student_id", name="uq_exam_assignments_exam_student"),
        CheckConstraint(
            "status IN ('assigned', 'started', 'completed', 'expired')", name="ck_exam_assignments_status"
        ),
    )


class Badge(Base):
    __tablename__ = "badges"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    code = Column(String(80), nullable=False, unique=True)
    name = Column(String(120), nullable=False)
    description = Column(Text, nullable=False)
    points = Column(Integer, nullable=False, server_default=text("0"))
    is_active = Column(Boolean, nullable=False, server_default=text("true"))

    __table_args__ = (CheckConstraint("points >= 0", name="ck_badges_points"),)


class StudentBadge(Base):
    __tablename__ = "student_badges"

    student_id = Column(
        UUID(as_uuid=True),
        ForeignKey("student_profiles.user_id", onupdate="CASCADE", ondelete="RESTRICT"),
        primary_key=True,
    )
    badge_id = Column(
        UUID(as_uuid=True), ForeignKey("badges.id", onupdate="CASCADE", ondelete="RESTRICT"), primary_key=True
    )
    earned_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())


class PracticeRecommendation(Base):
    __tablename__ = "practice_recommendations"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    student_id = Column(
        UUID(as_uuid=True),
        ForeignKey("student_profiles.user_id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    topic_id = Column(
        UUID(as_uuid=True), ForeignKey("topics.id", onupdate="CASCADE", ondelete="SET NULL"), nullable=True
    )
    question_count = Column(SmallInteger, nullable=False)
    difficulty = Column(String(20), nullable=False)
    question_types = Column(JSONB, nullable=False)
    status = Column(String(20), nullable=False, server_default=text("'recommended'"))
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    completed_at = Column(TIMESTAMP(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint("question_count BETWEEN 1 AND 50", name="ck_recommendations_count"),
        CheckConstraint("difficulty IN ('easy', 'medium', 'hard')", name="ck_recommendations_difficulty"),
        CheckConstraint(
            "status IN ('recommended', 'accepted', 'completed', 'dismissed')", name="ck_recommendations_status"
        ),
    )
