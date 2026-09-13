from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.api.dependencies.database import get_db
from app.api.schemas.auth import UserResponse
from app.db.models.curriculum import Chapter, Subject, Topic

router = APIRouter(prefix="/api/v1/curriculum", tags=["curriculum"])


def _pagination(page: int, page_size: int, total: int) -> dict:
    return {"page": page, "page_size": page_size, "total": total, "has_next": page * page_size < total}


def _not_found() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"code": "CURRICULUM_NOT_FOUND", "message": "Curriculum resource was not found"},
    )


def _subject_data(subject: Subject) -> dict:
    return {"id": subject.id, "name": subject.name, "class_level": subject.class_level}


def _chapter_data(chapter: Chapter) -> dict:
    return {
        "id": chapter.id,
        "subject_id": chapter.subject_id,
        "name": chapter.name,
        "display_order": chapter.display_order,
    }


def _topic_data(topic: Topic) -> dict:
    return {
        "id": topic.id,
        "chapter_id": topic.chapter_id,
        "name": topic.name,
        "display_order": topic.display_order,
    }


@router.get("/subjects")
def list_subjects(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    query = db.query(Subject).filter(Subject.class_level == 10, Subject.is_active.is_(True))
    total = query.count()
    subjects = query.order_by(Subject.name).offset((page - 1) * page_size).limit(page_size).all()
    return {"data": [_subject_data(subject) for subject in subjects], "meta": _pagination(page, page_size, total)}


@router.get("/subjects/{subject_id}/chapters")
def list_chapters(
    subject_id: UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    subject = db.query(Subject).filter_by(id=subject_id, class_level=10, is_active=True).one_or_none()
    if subject is None:
        raise _not_found()
    query = db.query(Chapter).filter(Chapter.subject_id == subject.id, Chapter.is_active.is_(True))
    total = query.count()
    chapters = query.order_by(Chapter.display_order).offset((page - 1) * page_size).limit(page_size).all()
    return {"data": [_chapter_data(chapter) for chapter in chapters], "meta": _pagination(page, page_size, total)}


@router.get("/chapters/{chapter_id}/topics")
def list_topics(
    chapter_id: UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    chapter = db.query(Chapter).filter_by(id=chapter_id, is_active=True).one_or_none()
    if chapter is None:
        raise _not_found()
    query = db.query(Topic).filter(Topic.chapter_id == chapter.id, Topic.is_active.is_(True))
    total = query.count()
    topics = query.order_by(Topic.display_order).offset((page - 1) * page_size).limit(page_size).all()
    return {"data": [_topic_data(topic) for topic in topics], "meta": _pagination(page, page_size, total)}