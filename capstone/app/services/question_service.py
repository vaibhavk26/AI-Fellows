from uuid import UUID

from sqlalchemy import and_, exists
from sqlalchemy.orm import Session

from app.db.models.attempt import StudentAttempt
from app.db.models.exam import ExamQuestion
from app.db.models.question import Question


class QuestionService:
    @staticmethod
    def list_questions(
        db: Session,
        user_id: UUID,
        role: str,
        *,
        subject_id: UUID | None = None,
        chapter_id: UUID | None = None,
        topic_id: UUID | None = None,
        question_type: str | None = None,
        difficulty: str | None = None,
        question_status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Question], int]:
        query = db.query(Question)
        if role == "student":
            visible_to_student = exists().where(
                and_(
                    ExamQuestion.question_id == Question.id,
                    StudentAttempt.exam_id == ExamQuestion.exam_id,
                    StudentAttempt.student_id == user_id,
                )
            )
            query = query.filter(Question.status == "validated", visible_to_student)
        elif question_status:
            query = query.filter((Question.created_by == user_id) | (Question.status == "validated"))
        else:
            query = query.filter((Question.created_by == user_id) | (Question.status == "validated"))

        for column, value in (
            (Question.subject_id, subject_id),
            (Question.chapter_id, chapter_id),
            (Question.topic_id, topic_id),
            (Question.question_type, question_type),
            (Question.difficulty, difficulty),
            (Question.status, question_status),
        ):
            if value is not None:
                query = query.filter(column == value)

        total = query.count()
        questions = query.order_by(Question.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        return questions, total

    @staticmethod
    def get_visible_question(db: Session, question_id: UUID, user_id: UUID, role: str) -> Question | None:
        query = db.query(Question).filter(Question.id == question_id)
        if role == "student":
            visible_to_student = exists().where(
                and_(
                    ExamQuestion.question_id == Question.id,
                    StudentAttempt.exam_id == ExamQuestion.exam_id,
                    StudentAttempt.student_id == user_id,
                )
            )
            query = query.filter(Question.status == "validated", visible_to_student)
        else:
            query = query.filter((Question.created_by == user_id) | (Question.status == "validated"))
        return query.one_or_none()
