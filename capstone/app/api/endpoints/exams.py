from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_student, get_current_teacher, get_current_user
from app.api.dependencies.database import get_db
from app.api.schemas.auth import UserResponse
from app.api.schemas.exam import AttemptSubmissionRequest, ExamGenerationRequest
from app.api.schemas.teacher import ExamAssignmentRequest
from app.db.models.attempt import StudentAnswer, StudentAttempt
from app.db.models.curriculum import Topic
from app.db.models.exam import Exam
from app.db.models.extensions import ExamAssignment
from app.db.models.question import Question
from app.services.analytics_service import AnalyticsService
from app.services.exam_service import ExamService

router = APIRouter(prefix="/api/v1", tags=["exams"])


def _exam_data(db: Session, exam: Exam) -> dict:
	questions = [{"id": exam_question.id, "sequence_no": exam_question.sequence_no, "question": {"id": question.id, "topic_id": question.topic_id, "question_type": question.question_type, "difficulty": question.difficulty, "marks": question.marks, "question_text": question.question_text, "options": question.options}} for exam_question, question in ExamService.get_exam_questions(db, exam.id)]
	return {"id": exam.id, "title": exam.title, "subject_id": exam.subject_id, "chapter_id": exam.chapter_id, "topic_id": exam.topic_id, "question_count": exam.question_count, "time_limit_minutes": exam.time_limit_minutes, "questions": questions, "created_by": exam.created_by, "created_at": exam.created_at}


def _attempt_result(db: Session, attempt: StudentAttempt) -> dict:
	answer_rows = db.query(StudentAnswer, Question, Topic.name).join(Question, Question.id == StudentAnswer.question_id).outerjoin(Topic, Topic.id == Question.topic_id).filter(StudentAnswer.attempt_id == attempt.id).all()
	topic_scores = {}
	answers = []
	for answer, question, topic_name in answer_rows:
		answers.append({"question_id": answer.question_id, "question_text": question.question_text, "question_type": question.question_type, "options": question.options, "topic_id": question.topic_id, "topic_name": topic_name, "submitted_answer": answer.submitted_answer, "is_correct": answer.is_correct, "score_awarded": answer.score_awarded, "max_score": answer.max_score, "correct_answer": question.correct_answer, "explanation": question.explanation})
		if question.topic_id is not None:
			score = topic_scores.setdefault(question.topic_id, {"topic_name": topic_name, "earned": Decimal("0"), "possible": Decimal("0")})
			score["earned"] += Decimal(answer.score_awarded)
			score["possible"] += Decimal(answer.max_score)
	weak_topics = []
	for topic_id, score in topic_scores.items():
		percentage = (score["earned"] * Decimal("100") / score["possible"]).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
		if AnalyticsService.status_for(percentage) == "needs_practice":
			weak_topics.append({"topic_id": topic_id, "topic_name": score["topic_name"], "score_percentage": percentage, "status": "needs_practice"})
	return {"id": attempt.id, "exam_id": attempt.exam_id, "student_id": attempt.student_id, "status": attempt.status, "score": attempt.score, "max_score": attempt.max_score, "percentage": attempt.percentage, "submitted_at": attempt.submitted_at, "answers": answers, "weak_topics": weak_topics}


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


@router.get("/students/me/assignments")
def list_student_assignments(current_user: UserResponse = Depends(get_current_student), db: Session = Depends(get_db)) -> dict:
	rows = db.query(ExamAssignment, Exam).join(Exam, Exam.id == ExamAssignment.exam_id).filter(
		ExamAssignment.student_id == current_user.id
	).order_by(ExamAssignment.assigned_at.desc()).all()
	return {"data": [{
		"id": assignment.id,
		"exam_id": exam.id,
		"exam_title": exam.title,
		"question_count": exam.question_count,
		"time_limit_minutes": exam.time_limit_minutes,
		"status": assignment.status,
		"assigned_at": assignment.assigned_at,
	} for assignment, exam in rows], "meta": None}


@router.post("/exams/{exam_id}/assignments", status_code=status.HTTP_201_CREATED)
def assign_exam(exam_id: UUID, request: ExamAssignmentRequest, response: Response, current_user: UserResponse = Depends(get_current_teacher), db: Session = Depends(get_db)) -> dict:
	exam = db.query(Exam).filter_by(id=exam_id, created_by=current_user.id).one_or_none()
	if exam is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam was not found")
	try:
		assignments, created = ExamService.assign_exam(db, exam, current_user.id, request.student_ids)
	except ValueError as error:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))
	if not created:
		response.status_code = status.HTTP_200_OK
	return {"data": [{"id": assignment.id, "student_id": assignment.student_id, "status": assignment.status, "assigned_at": assignment.assigned_at} for assignment in assignments], "meta": None}


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
	try:
		attempt, created = ExamService.start_attempt(db, exam, current_user.id)
	except ValueError as error:
		raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error))
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
