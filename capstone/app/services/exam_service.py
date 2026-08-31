import re
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.attempt import StudentAnswer, StudentAttempt
from app.db.models.curriculum import Chapter, Topic
from app.db.models.exam import Exam, ExamQuestion
from app.db.models.question import Question
from app.services.analytics_service import AnalyticsService


class ExamService:
    @staticmethod
    def _validate_scope(db: Session, subject_id: UUID, chapter_id: UUID | None, topic_id: UUID | None) -> None:
        if chapter_id:
            chapter = db.query(Chapter).filter_by(id=chapter_id, subject_id=subject_id).one_or_none()
            if chapter is None:
                raise ValueError("chapter_id does not belong to subject_id")
        if topic_id:
            topic = db.query(Topic).join(Chapter).filter(Topic.id == topic_id, Chapter.subject_id == subject_id).one_or_none()
            if topic is None or (chapter_id and topic.chapter_id != chapter_id):
                raise ValueError("topic_id does not belong to the selected curriculum scope")

    @staticmethod
    def generate_exam(db: Session, request, creator_id: UUID) -> Exam:
        ExamService._validate_scope(db, request.subject_id, request.chapter_id, request.topic_id)
        query = db.query(Question).filter(Question.status == "validated", Question.subject_id == request.subject_id, Question.difficulty == request.difficulty, Question.question_type.in_(request.question_types))
        if request.chapter_id:
            query = query.filter(Question.chapter_id == request.chapter_id)
        if request.topic_id:
            query = query.filter(Question.topic_id == request.topic_id)
        questions = query.order_by(Question.created_at).limit(request.question_count).all()
        if len(questions) != request.question_count:
            raise ValueError("Not enough validated questions match the requested exam criteria")
        title = request.title or "Practice Exam"
        exam = Exam(title=title, subject_id=request.subject_id, chapter_id=request.chapter_id, topic_id=request.topic_id, difficulty=request.difficulty, question_types=request.question_types, question_count=len(questions), time_limit_minutes=request.time_limit_minutes, created_by=creator_id)
        db.add(exam)
        db.flush()
        db.add_all(ExamQuestion(exam_id=exam.id, question_id=question.id, sequence_no=index) for index, question in enumerate(questions, start=1))
        db.commit()
        db.refresh(exam)
        return exam

    @staticmethod
    def get_exam_questions(db: Session, exam_id: UUID) -> list[tuple[ExamQuestion, Question]]:
        return db.query(ExamQuestion, Question).join(Question, Question.id == ExamQuestion.question_id).filter(ExamQuestion.exam_id == exam_id).order_by(ExamQuestion.sequence_no).all()

    @staticmethod
    def get_exam(db: Session, exam_id: UUID, user_id: UUID, role: str) -> Exam | None:
        exam = db.query(Exam).filter_by(id=exam_id).one_or_none()
        if exam is None:
            return None
        has_attempt = db.query(StudentAttempt).filter_by(exam_id=exam_id, student_id=user_id).first() is not None
        return exam if role == "teacher" or exam.created_by == user_id or has_attempt else None

    @staticmethod
    def start_attempt(db: Session, exam: Exam, student_id: UUID) -> tuple[StudentAttempt, bool]:
        attempt = db.query(StudentAttempt).filter_by(exam_id=exam.id, student_id=student_id, status="in_progress").one_or_none()
        if attempt:
            return attempt, False
        max_score = sum(question.marks for _, question in ExamService.get_exam_questions(db, exam.id))
        attempt = StudentAttempt(exam_id=exam.id, student_id=student_id, max_score=max_score)
        db.add(attempt)
        db.commit()
        db.refresh(attempt)
        return attempt, True

    @staticmethod
    def _is_correct(question: Question, submitted_answer: str | None) -> bool:
        if submitted_answer is None:
            return False
        if question.question_type == "mcq":
            return submitted_answer.strip().casefold() == question.correct_answer.strip().casefold()
        expected_match = re.search(r"([-+]?\d+(?:\.\d+)?)(?:\s*([a-zA-Z]+))?", question.correct_answer)
        answer_match = re.search(r"([-+]?\d+(?:\.\d+)?)(?:\s*([a-zA-Z]+))?", submitted_answer)
        if not expected_match or not answer_match:
            return False
        expected_unit = expected_match.group(2)
        answer_unit = answer_match.group(2)
        if expected_unit and expected_unit.casefold() != (answer_unit or "").casefold():
            return False
        try:
            expected = Decimal(expected_match.group(1))
            submitted = Decimal(answer_match.group(1))
        except InvalidOperation:
            return False
        tolerance = abs(expected) * Decimal("0.05")
        return abs(submitted - expected) <= tolerance if expected else submitted == 0

    @staticmethod
    def submit_attempt(db: Session, attempt: StudentAttempt, answers: list) -> StudentAttempt:
        if attempt.status == "submitted":
            return attempt
        exam = db.query(Exam).filter_by(id=attempt.exam_id).one()
        now = datetime.now(timezone.utc)
        if (now - attempt.started_at).total_seconds() > exam.time_limit_minutes * 60:
            raise TimeoutError("Attempt time limit has expired")
        submitted = {answer.question_id: answer.answer.strip() for answer in answers}
        exam_questions = ExamService.get_exam_questions(db, exam.id)
        allowed_ids = {question.id for _, question in exam_questions}
        if not set(submitted).issubset(allowed_ids):
            raise ValueError("Every answer question_id must belong to the exam")
        total = Decimal("0")
        recorded_topics: set[UUID] = set()
        for _, question in exam_questions:
            response = submitted.get(question.id)
            correct = ExamService._is_correct(question, response)
            awarded = Decimal(question.marks) if correct else Decimal("0")
            db.add(StudentAnswer(attempt_id=attempt.id, question_id=question.id, submitted_answer=response, is_correct=correct, score_awarded=awarded, max_score=question.marks))
            count_attempt = question.topic_id is not None and question.topic_id not in recorded_topics
            AnalyticsService.record_answer(db, attempt.student_id, question.topic_id, correct, awarded, question.marks, count_attempt)
            if question.topic_id is not None:
                recorded_topics.add(question.topic_id)
            total += awarded
        attempt.status = "submitted"
        attempt.submitted_at = now
        attempt.score = total
        attempt.percentage = (total * Decimal("100") / Decimal(attempt.max_score)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        db.commit()
        db.refresh(attempt)
        return attempt
