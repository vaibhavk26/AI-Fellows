from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_student, get_current_user
from app.api.dependencies.database import get_db
from app.api.schemas.auth import UserResponse
from app.api.schemas.exam import AttemptSubmissionRequest, ExamGenerationRequest
from app.db.models.attempt import StudentAnswer, StudentAttempt
from app.db.models.exam import Exam
from app.db.models.question import Question
from app.services.analytics_service import AnalyticsService
from app.services.exam_service import ExamService

router = APIRouter(prefix="/api/v1", tags=["exams"])


def _exam_data(db: Session, exam: Exam) -> dict:
	questions = [{"id": exam_question.id, "sequence_no": exam_question.sequence_no, "question": {"id": question.id, "topic_id": question.topic_id, "question_type": question.question_type, "difficulty": question.difficulty, "marks": question.marks, "question_text": question.question_text, "options": question.options}} for exam_question, question in ExamService.get_exam_questions(db, exam.id)]
	return {"id": exam.id, "title": exam.title, "subject_id": exam.subject_id, "chapter_id": exam.chapter_id, "topic_id": exam.topic_id, "question_count": exam.question_count, "time_limit_minutes": exam.time_limit_minutes, "questions": questions, "created_by": exam.created_by, "created_at": exam.created_at}


def _attempt_result(db: Session, attempt: StudentAttempt) -> dict:
	answer_rows = db.query(StudentAnswer, Question).join(Question, Question.id == StudentAnswer.question_id).filter(StudentAnswer.attempt_id == attempt.id).all()
	weak_rows, _ = AnalyticsService.list_performance(db, attempt.student_id, weak_only=True, page_size=100)
	return {"id": attempt.id, "exam_id": attempt.exam_id, "student_id": attempt.student_id, "status": attempt.status, "score": attempt.score, "max_score": attempt.max_score, "percentage": attempt.percentage, "submitted_at": attempt.submitted_at, "answers": [{"question_id": answer.question_id, "submitted_answer": answer.submitted_answer, "is_correct": answer.is_correct, "score_awarded": answer.score_awarded, "max_score": answer.max_score, "correct_answer": question.correct_answer, "explanation": question.explanation} for answer, question in answer_rows], "weak_topics": [{"topic_id": performance.topic_id, "topic_name": topic_name, "attempts": performance.attempts, "correct_answers": performance.correct_answers, "score_percentage": performance.score_percentage, "status": performance.status, "last_updated": performance.last_updated} for performance, topic_name in weak_rows]}


@router.post("/exams/generate", status_code=status.HTTP_201_CREATED)
def generate_exam(request: ExamGenerationRequest, current_user: UserResponse = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
	try:
		exam = ExamService.generate_exam(db, request, current_user.id)
	except ValueError as error:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))
	return {"data": _exam_data(db, exam), "meta": None}


@router.get("/exams")
def list_exams(subject_id: UUID | None = None, created_by: UUID | None = None, page: int = Query(default=1, ge=1), page_size: int = Query(default=20, ge=1, le=100), current_user: UserResponse = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
	query = db.query(Exam).filter(Exam.created_by == current_user.id)
	if subject_id:
		query = query.filter(Exam.subject_id == subject_id)
	if created_by:
		query = query.filter(Exam.created_by == created_by)
	total = query.count()
	exams = query.order_by(Exam.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
	return {"data": [_exam_data(db, exam) for exam in exams], "meta": {"page": page, "page_size": page_size, "total": total, "has_next": page * page_size < total}}


@router.get("/exams/{exam_id}")
def get_exam(exam_id: UUID, current_user: UserResponse = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
	exam = ExamService.get_exam(db, exam_id, current_user.id, current_user.role)
	if exam is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam was not found")
	return {"data": _exam_data(db, exam), "meta": None}


@router.post("/exams/{exam_id}/attempts", status_code=status.HTTP_201_CREATED)
def start_attempt(exam_id: UUID, response: Response, current_user: UserResponse = Depends(get_current_student), db: Session = Depends(get_db)) -> dict:
	exam = ExamService.get_exam(db, exam_id, current_user.id, current_user.role)
	if exam is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam was not found")
	attempt, created = ExamService.start_attempt(db, exam, current_user.id)
	if not created:
		response.status_code = status.HTTP_200_OK
	return {"data": {"id": attempt.id, "exam_id": attempt.exam_id, "status": attempt.status, "started_at": attempt.started_at}, "meta": None}


@router.get("/attempts/{attempt_id}")
def get_attempt(attempt_id: UUID, current_user: UserResponse = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
	attempt = db.query(StudentAttempt).filter_by(id=attempt_id).one_or_none()
	if attempt is None or (current_user.role == "student" and attempt.student_id != current_user.id):
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attempt was not found")
	if attempt.status == "submitted":
		return {"data": _attempt_result(db, attempt), "meta": None}
	exam = ExamService.get_exam(db, attempt.exam_id, current_user.id, current_user.role)
	return {"data": {"id": attempt.id, "exam_id": attempt.exam_id, "status": attempt.status, "started_at": attempt.started_at, "exam": _exam_data(db, exam)}, "meta": None}


@router.post("/attempts/{attempt_id}/submit", status_code=status.HTTP_201_CREATED)
def submit_attempt(attempt_id: UUID, request: AttemptSubmissionRequest, response: Response, current_user: UserResponse = Depends(get_current_student), db: Session = Depends(get_db)) -> dict:
	attempt = db.query(StudentAttempt).filter_by(id=attempt_id, student_id=current_user.id).one_or_none()
	if attempt is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attempt was not found")
	if attempt.status == "submitted":
		response.status_code = status.HTTP_200_OK
		return {"data": _attempt_result(db, attempt), "meta": None}
	try:
		attempt = ExamService.submit_attempt(db, attempt, request.answers)
	except TimeoutError as error:
		db.rollback()
		raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error))
	except ValueError as error:
		db.rollback()
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))
	return {"data": _attempt_result(db, attempt), "meta": None}
