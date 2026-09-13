from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.api.dependencies.database import get_db
from app.core.config import get_settings
from app.core.security import create_access_token, hash_password
from app.db.models.base import Base
from app.db.models.curriculum import Chapter, Subject, Topic
from app.db.models.user import StudentProfile, User
from app.main import app


settings = get_settings()
engine = create_engine(settings.test_database_url, pool_pre_ping=True)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    database = TestingSessionLocal()
    try:
        yield database
    finally:
        database.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def database_schema():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def curriculum_data():
    database = TestingSessionLocal()
    try:
        database.execute(text("TRUNCATE TABLE users, subjects CASCADE"))
        user = User(
            email=f"curriculum-{uuid4()}@example.com",
            password_hash=hash_password("Password123!"),
            full_name="Curriculum Student",
            role="student",
        )
        database.add(user)
        database.flush()
        database.add(StudentProfile(user_id=user.id))
        physics = Subject(name="Physics", class_level=10)
        mathematics = Subject(name="Mathematics", class_level=10)
        inactive = Subject(name="Inactive", class_level=10, is_active=False)
        database.add_all([physics, mathematics, inactive])
        database.flush()
        chapter_late = Chapter(subject_id=physics.id, name="Late", display_order=2)
        chapter_first = Chapter(subject_id=physics.id, name="First", display_order=1)
        database.add_all([chapter_late, chapter_first])
        database.flush()
        topic_late = Topic(chapter_id=chapter_first.id, name="Late topic", display_order=2)
        topic_first = Topic(chapter_id=chapter_first.id, name="First topic", display_order=1)
        database.add_all([topic_late, topic_first])
        database.commit()
        token, _ = create_access_token(user.id, "student")
        yield {"subject": physics, "chapter": chapter_first, "token": token}
    finally:
        database.rollback()
        database.execute(text("TRUNCATE TABLE users, subjects CASCADE"))
        database.commit()
        database.close()


def test_curriculum_endpoints_require_authentication():
    assert client.get("/api/v1/curriculum/subjects").status_code == 403


def test_curriculum_endpoints_return_active_records_in_display_order(curriculum_data):
    headers = {"Authorization": f"Bearer {curriculum_data['token']}"}

    subjects = client.get("/api/v1/curriculum/subjects", headers=headers)
    assert subjects.status_code == 200
    assert [item["name"] for item in subjects.json()["data"]] == ["Mathematics", "Physics"]
    assert subjects.json()["meta"] == {"page": 1, "page_size": 20, "total": 2, "has_next": False}

    chapters = client.get(
        f"/api/v1/curriculum/subjects/{curriculum_data['subject'].id}/chapters",
        headers=headers,
    )
    assert [item["name"] for item in chapters.json()["data"]] == ["First", "Late"]

    topics = client.get(
        f"/api/v1/curriculum/chapters/{curriculum_data['chapter'].id}/topics",
        headers=headers,
    )
    assert [item["name"] for item in topics.json()["data"]] == ["First topic", "Late topic"]


def test_unknown_curriculum_parent_uses_documented_error(curriculum_data):
    headers = {"Authorization": f"Bearer {curriculum_data['token']}"}
    response = client.get(f"/api/v1/curriculum/subjects/{uuid4()}/chapters", headers=headers)

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "CURRICULUM_NOT_FOUND"