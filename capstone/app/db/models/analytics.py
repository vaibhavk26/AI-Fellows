from sqlalchemy import (
    CheckConstraint,
    Column,
    ForeignKey,
    Integer,
    Numeric,
    String,
    TIMESTAMP,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID

from app.db.models.base import Base


class TopicPerformance(Base):
    __tablename__ = "topic_performance"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    student_id = Column(
        UUID(as_uuid=True),
        ForeignKey("student_profiles.user_id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    topic_id = Column(UUID(as_uuid=True), ForeignKey("topics.id", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False)
    attempts = Column(Integer, nullable=False, server_default=text("0"))
    correct_answers = Column(Integer, nullable=False, server_default=text("0"))
    score_earned = Column(Numeric(12, 2), nullable=False, server_default=text("0"))
    score_possible = Column(Numeric(12, 2), nullable=False, server_default=text("0"))
    score_percentage = Column(Numeric(6, 2), nullable=False, server_default=text("0"))
    status = Column(String(20), nullable=False, server_default=text("'needs_practice'"))
    last_updated = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("student_id", "topic_id", name="uq_topic_performance_student_topic"),
        CheckConstraint("attempts >= 0 AND correct_answers >= 0", name="ck_topic_performance_counts"),
        CheckConstraint("score_earned >= 0 AND score_possible >= 0", name="ck_topic_performance_scores"),
        CheckConstraint("score_percentage BETWEEN 0 AND 100", name="ck_topic_performance_percentage"),
        CheckConstraint("status IN ('strong', 'good', 'needs_practice')", name="ck_topic_performance_status"),
    )
