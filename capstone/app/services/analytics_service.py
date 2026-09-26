from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.attempt import StudentAnswer, StudentAttempt
from app.db.models.analytics import TopicPerformance
from app.db.models.curriculum import Chapter, Subject, Topic
from app.db.models.exam import Exam
from app.db.models.question import Question


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

    @staticmethod
    def dashboard_analytics(db: Session, student_id: UUID, *, subject_id: UUID | None = None, chapter_id: UUID | None = None, from_date: date | None = None, to_date: date | None = None) -> dict:
        query = db.query(
            StudentAttempt.id.label("attempt_id"),
            StudentAttempt.submitted_at.label("submitted_at"),
            Exam.title.label("exam_title"),
            Subject.id.label("subject_id"),
            Subject.name.label("subject_name"),
            Chapter.id.label("chapter_id"),
            Chapter.name.label("chapter_name"),
            Topic.id.label("topic_id"),
            Topic.name.label("topic_name"),
            StudentAnswer.score_awarded.label("score_awarded"),
            StudentAnswer.max_score.label("max_score"),
        ).join(Exam, Exam.id == StudentAttempt.exam_id
        ).join(StudentAnswer, StudentAnswer.attempt_id == StudentAttempt.id
        ).join(Question, Question.id == StudentAnswer.question_id
        ).join(Subject, Subject.id == Question.subject_id
        ).join(Chapter, Chapter.id == Question.chapter_id
        ).outerjoin(Topic, Topic.id == Question.topic_id
        ).filter(StudentAttempt.student_id == student_id, StudentAttempt.status == "submitted")
        if subject_id:
            query = query.filter(Question.subject_id == subject_id)
        if chapter_id:
            query = query.filter(Question.chapter_id == chapter_id)
        if from_date:
            query = query.filter(StudentAttempt.submitted_at >= datetime.combine(from_date, time.min, timezone.utc))
        if to_date:
            query = query.filter(StudentAttempt.submitted_at < datetime.combine(to_date + timedelta(days=1), time.min, timezone.utc))

        subject_scores = {}
        chapter_scores = {}
        topic_scores = {}
        attempts = {}
        total_score = Decimal("0")
        total_possible = Decimal("0")
        questions_answered = 0

        def add_score(group, key, name, attempt_id, score, possible, parent=None):
            item = group.setdefault(key, {
                "id": key,
                "name": name,
                "score": Decimal("0"),
                "max_score": Decimal("0"),
                "attempt_ids": set(),
            })
            item["score"] += score
            item["max_score"] += possible
            item["attempt_ids"].add(attempt_id)
            if parent:
                item.update(parent)

        for row in query.all():
            questions_answered += 1
            score = Decimal(row.score_awarded)
            possible = Decimal(row.max_score)
            total_score += score
            total_possible += possible
            add_score(subject_scores, row.subject_id, row.subject_name, row.attempt_id, score, possible)
            add_score(
                chapter_scores,
                row.chapter_id,
                row.chapter_name,
                row.attempt_id,
                score,
                possible,
                {"subject_id": row.subject_id, "subject_name": row.subject_name},
            )
            if row.topic_id is not None:
                add_score(
                    topic_scores,
                    row.topic_id,
                    row.topic_name,
                    row.attempt_id,
                    score,
                    possible,
                    {"chapter_id": row.chapter_id, "chapter_name": row.chapter_name, "subject_id": row.subject_id, "subject_name": row.subject_name},
                )
            attempt = attempts.setdefault(row.attempt_id, {
                "id": row.attempt_id,
                "exam_title": row.exam_title,
                "submitted_at": row.submitted_at,
                "score": Decimal("0"),
                "max_score": Decimal("0"),
                "subjects": set(),
                "chapters": set(),
            })
            attempt["score"] += score
            attempt["max_score"] += possible
            attempt["subjects"].add(row.subject_name)
            attempt["chapters"].add(row.chapter_name)

        def present_group(item):
            percentage = (item["score"] * Decimal("100") / item["max_score"]).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            return {
                **{key: value for key, value in item.items() if key not in ("attempt_ids",)},
                "attempts": len(item["attempt_ids"]),
                "score_percentage": percentage,
                "status": AnalyticsService.status_for(percentage),
            }

        attempt_rows = []
        for attempt in attempts.values():
            percentage = (attempt["score"] * Decimal("100") / attempt["max_score"]).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            attempt_rows.append({
                "id": attempt["id"],
                "exam_title": attempt["exam_title"],
                "submitted_at": attempt["submitted_at"],
                "score": attempt["score"],
                "max_score": attempt["max_score"],
                "score_percentage": percentage,
                "subjects": sorted(attempt["subjects"]),
                "chapters": sorted(attempt["chapters"]),
            })

        def ordered(values):
            return sorted((present_group(item) for item in values.values()), key=lambda item: item["name"].casefold())

        overall_percentage = (total_score * Decimal("100") / total_possible).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) if total_possible else Decimal("0.00")
        return {
            "summary": {
                "attempts": len(attempt_rows),
                "questions_answered": questions_answered,
                "score": total_score,
                "max_score": total_possible,
                "score_percentage": overall_percentage,
                "subjects": len(subject_scores),
                "chapters": len(chapter_scores),
                "topics": len(topic_scores),
            },
            "subjects": ordered(subject_scores),
            "chapters": ordered(chapter_scores),
            "topics": ordered(topic_scores),
            "attempts_detail": sorted(attempt_rows, key=lambda item: item["submitted_at"], reverse=True),
        }
