from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_teacher, get_current_user
from app.api.dependencies.database import get_db
from app.api.schemas.auth import UserResponse
from app.api.schemas.question import QuestionGenerationRequest
from app.db.models.curriculum import SourceReference
from app.db.models.question import QuestionSourceReference
from app.services.question_service import QuestionService

router = APIRouter(prefix="/api/v1/questions", tags=["questions"])


def _question_data(db: Session, question) -> dict:
	source_references = db.query(SourceReference).join(
		QuestionSourceReference, QuestionSourceReference.source_reference_id == SourceReference.id
	).filter(QuestionSourceReference.question_id == question.id).all()
	return {
		"id": question.id, "subject_id": question.subject_id, "chapter_id": question.chapter_id,
		"topic_id": question.topic_id, "class_level": question.class_level, "question_type": question.question_type,
		"difficulty": question.difficulty, "bloom_level": question.bloom_level, "marks": question.marks,
		"question_text": question.question_text, "options": question.options, "expected_answer": question.expected_answer,
		"explanation": question.explanation, "learning_objective": question.learning_objective,
		"source_references": [{"id": source.id, "document_id": source.document_id, "page_number": source.page_number, "chunk_id": source.chunk_id, "excerpt": source.excerpt} for source in source_references], "status": question.status, "created_by": question.created_by, "created_at": question.created_at,
	}


@router.post("/generate", status_code=status.HTTP_501_NOT_IMPLEMENTED)
def generate_questions(
	request: QuestionGenerationRequest,
	current_user: UserResponse = Depends(get_current_teacher),
) -> dict:
	raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Question generation requires the Section 10.3 RAG workflow")


@router.get("")
def list_questions(
	subject_id: UUID | None = None, chapter_id: UUID | None = None, topic_id: UUID | None = None,
	question_type: str | None = Query(default=None, pattern="^(mcq|numerical)$"),
	difficulty: str | None = Query(default=None, pattern="^(easy|medium|hard)$"),
	question_status: str | None = Query(default=None, alias="status", pattern="^(generated|validated|rejected)$"),
	page: int = Query(default=1, ge=1), page_size: int = Query(default=20, ge=1, le=100),
	current_user: UserResponse = Depends(get_current_user), db: Session = Depends(get_db),
) -> dict:
	questions, total = QuestionService.list_questions(db, current_user.id, current_user.role, subject_id=subject_id, chapter_id=chapter_id, topic_id=topic_id, question_type=question_type, difficulty=difficulty, question_status=question_status, page=page, page_size=page_size)
	return {"data": [_question_data(db, question) for question in questions], "meta": {"page": page, "page_size": page_size, "total": total, "has_next": page * page_size < total}}


@router.get("/{question_id}")
def get_question(question_id: UUID, current_user: UserResponse = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
	question = QuestionService.get_visible_question(db, question_id, current_user.id, current_user.role)
	if question is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question was not found")
	return {"data": _question_data(db, question), "meta": None}
