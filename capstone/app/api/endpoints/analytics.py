from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from datetime import datetime

from app.api.dependencies.auth import get_current_student, get_current_teacher
from app.api.dependencies.database import get_db
from app.api.schemas.auth import UserResponse
from app.db.models.attempt import StudentAttempt
from app.db.models.exam import Exam
from app.db.models.question import Question
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/api/v1/students/me", tags=["analytics"])
teacher_router = APIRouter(prefix="/api/v1/teachers/me", tags=["analytics"])


def _page(rows, total: int, page: int, page_size: int) -> dict:
	return {"data": [{"topic_id": performance.topic_id, "topic_name": topic_name, "attempts": performance.attempts, "correct_answers": performance.correct_answers, "score_percentage": performance.score_percentage, "status": performance.status, "last_updated": performance.last_updated} for performance, topic_name in rows], "meta": {"page": page, "page_size": page_size, "total": total, "has_next": page * page_size < total}}


@router.get("/progress")
def progress(subject_id: UUID | None = None, chapter_id: UUID | None = None, topic_id: UUID | None = None, page: int = Query(default=1, ge=1), page_size: int = Query(default=20, ge=1, le=100), current_user: UserResponse = Depends(get_current_student), db: Session = Depends(get_db)) -> dict:
	rows, total = AnalyticsService.list_performance(db, current_user.id, subject_id=subject_id, chapter_id=chapter_id, topic_id=topic_id, page=page, page_size=page_size)
	return _page(rows, total, page, page_size)


@router.get("/weak-topics")
def weak_topics(page: int = Query(default=1, ge=1), page_size: int = Query(default=20, ge=1, le=100), current_user: UserResponse = Depends(get_current_student), db: Session = Depends(get_db)) -> dict:
	rows, total = AnalyticsService.list_performance(db, current_user.id, weak_only=True, page=page, page_size=page_size)
	return _page(rows, total, page, page_size)


@router.get("/attempts")
def list_attempts(exam_id: UUID | None = None, attempt_status: str | None = Query(default=None, alias="status", pattern="^(in_progress|submitted)$"), from_date: datetime | None = None, to_date: datetime | None = None, page: int = Query(default=1, ge=1), page_size: int = Query(default=20, ge=1, le=100), current_user: UserResponse = Depends(get_current_student), db: Session = Depends(get_db)) -> dict:
	query = db.query(StudentAttempt).filter(StudentAttempt.student_id == current_user.id)
	if exam_id:
		query = query.filter(StudentAttempt.exam_id == exam_id)
	if attempt_status:
		query = query.filter(StudentAttempt.status == attempt_status)
	if from_date:
		query = query.filter(StudentAttempt.started_at >= from_date)
	if to_date:
		query = query.filter(StudentAttempt.started_at <= to_date)
	total = query.count()
	attempts = query.order_by(StudentAttempt.started_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
	return {"data": [{"id": attempt.id, "exam_id": attempt.exam_id, "status": attempt.status, "started_at": attempt.started_at, "submitted_at": attempt.submitted_at, "score": attempt.score, "max_score": attempt.max_score, "percentage": attempt.percentage} for attempt in attempts], "meta": {"page": page, "page_size": page_size, "total": total, "has_next": page * page_size < total}}


@teacher_router.get("/dashboard")
def teacher_dashboard(current_user: UserResponse = Depends(get_current_teacher), db: Session = Depends(get_db)) -> dict:
	question_counts = {question_status: db.query(Question).filter(Question.created_by == current_user.id, Question.status == question_status).count() for question_status in ("generated", "validated", "rejected")}
	return {"data": {"questions": question_counts, "exams_created": db.query(Exam).filter(Exam.created_by == current_user.id).count()}, "meta": None}
