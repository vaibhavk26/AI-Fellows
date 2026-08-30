from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.analytics import TopicPerformance
from app.db.models.curriculum import Chapter, Topic


class AnalyticsService:
    @staticmethod
    def status_for(percentage: Decimal) -> str:
        if percentage >= Decimal("80"):
            return "strong"
        if percentage >= Decimal("60"):
            return "good"
        return "needs_practice"

    @staticmethod
    def record_answer(db: Session, student_id: UUID, topic_id: UUID | None, is_correct: bool, score: Decimal, maximum: int, count_attempt: bool = True) -> None:
        if topic_id is None:
            return
        performance = db.query(TopicPerformance).filter_by(student_id=student_id, topic_id=topic_id).with_for_update().one_or_none()
        if performance is None:
            performance = TopicPerformance(student_id=student_id, topic_id=topic_id, attempts=0, correct_answers=0, score_earned=0, score_possible=0)
            db.add(performance)
            db.flush()
        performance.attempts += int(count_attempt)
        performance.correct_answers += int(is_correct)
        performance.score_earned = Decimal(performance.score_earned) + score
        performance.score_possible = Decimal(performance.score_possible) + Decimal(maximum)
        percentage = Decimal(performance.score_earned) * Decimal("100") / Decimal(performance.score_possible)
        performance.score_percentage = percentage.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        performance.status = AnalyticsService.status_for(performance.score_percentage)

    @staticmethod
    def list_performance(db: Session, student_id: UUID, *, subject_id: UUID | None = None, chapter_id: UUID | None = None, topic_id: UUID | None = None, weak_only: bool = False, page: int = 1, page_size: int = 20):
        query = db.query(TopicPerformance, Topic.name).join(Topic, Topic.id == TopicPerformance.topic_id).join(Chapter, Chapter.id == Topic.chapter_id).filter(TopicPerformance.student_id == student_id)
        if subject_id:
            query = query.filter(Chapter.subject_id == subject_id)
        if chapter_id:
            query = query.filter(Topic.chapter_id == chapter_id)
        if topic_id:
            query = query.filter(Topic.id == topic_id)
        if weak_only:
            query = query.filter(TopicPerformance.status == "needs_practice").order_by(TopicPerformance.score_percentage, TopicPerformance.last_updated)
        else:
            query = query.order_by(TopicPerformance.last_updated.desc())
        total = query.count()
        return query.offset((page - 1) * page_size).limit(page_size).all(), total
