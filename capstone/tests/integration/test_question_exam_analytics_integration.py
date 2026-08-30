"""Integration tests for the Section 10.2 question, exam, and analytics APIs."""
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
from app.db.models.question import Question
from app.db.models.user import StudentProfile, TeacherProfile, User
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
def seeded_data():
    database = TestingSessionLocal()
    try:
        database.execute(text("TRUNCATE TABLE users, subjects CASCADE"))
        database.commit()
        teacher = User(email=f"teacher-{uuid4()}@example.com", password_hash=hash_password("Password123!"), full_name="Test Teacher", role="teacher")
        student = User(email=f"student-{uuid4()}@example.com", password_hash=hash_password("Password123!"), full_name="Test Student", role="student")
        database.add_all([teacher, student])
        database.flush()
        database.add_all([TeacherProfile(user_id=teacher.id), StudentProfile(user_id=student.id)])
        subject = Subject(name=f"Physics-{uuid4()}")
        database.add(subject)
        database.flush()
        chapter = Chapter(subject_id=subject.id, name="Light", display_order=1)
        database.add(chapter)
        database.flush()
        topic = Topic(chapter_id=chapter.id, name="Reflection", display_order=1)
        database.add(topic)
        database.flush()
        database.add_all([
            Question(subject_id=subject.id, chapter_id=chapter.id, topic_id=topic.id, question_type="mcq", difficulty="easy", marks=2, question_text="Which option is correct?", options=[{"key": "A", "text": "Correct"}, {"key": "B", "text": "Incorrect"}, {"key": "C", "text": "Incorrect"}, {"key": "D", "text": "Incorrect"}], correct_answer="A", expected_answer="A", explanation="A is correct.", learning_objective="Identify the correct option.", status="validated", created_by=teacher.id),
            Question(subject_id=subject.id, chapter_id=chapter.id, topic_id=topic.id, question_type="numerical", difficulty="easy", marks=3, question_text="What is the value?", options=None, correct_answer="100 m", expected_answer="100 m", explanation="The value is 100 m.", learning_objective="Calculate a numeric value.", status="validated", created_by=teacher.id),
            Question(subject_id=subject.id, chapter_id=chapter.id, topic_id=topic.id, question_type="mcq", difficulty="easy", marks=1, question_text="Rejected question", options=[{"key": "A", "text": "A"}, {"key": "B", "text": "B"}, {"key": "C", "text": "C"}, {"key": "D", "text": "D"}], correct_answer="A", expected_answer="A", explanation="Not available to students.", learning_objective="Test teacher visibility.", status="rejected", created_by=teacher.id),
        ])
        database.commit()
        teacher_token, _ = create_access_token(teacher.id, "teacher")
        student_token, _ = create_access_token(student.id, "student")
        yield {"subject": subject, "chapter": chapter, "topic": topic, "teacher_headers": {"Authorization": f"Bearer {teacher_token}"}, "student_headers": {"Authorization": f"Bearer {student_token}"}}
    finally:
        database.rollback()
        database.execute(text("TRUNCATE TABLE users, subjects CASCADE"))
        database.commit()
        database.close()


def test_question_exam_attempt_and_analytics_flow(seeded_data):
    teacher_headers = seeded_data["teacher_headers"]
    student_headers = seeded_data["student_headers"]

    assert client.get("/api/v1/questions", headers=student_headers).json()["data"] == []
    teacher_questions = client.get("/api/v1/questions", headers=teacher_headers)
    assert teacher_questions.status_code == 200
    assert teacher_questions.json()["meta"]["total"] == 3
    assert client.post("/api/v1/questions/generate", headers=teacher_headers, json={"subject_id": str(seeded_data["subject"].id), "chapter_id": str(seeded_data["chapter"].id), "difficulty": "easy", "question_type": "mcq", "marks": 1, "number_of_questions": 1}).status_code == 501

    exam_response = client.post("/api/v1/exams/generate", headers=student_headers, json={"subject_id": str(seeded_data["subject"].id), "chapter_id": str(seeded_data["chapter"].id), "topic_id": str(seeded_data["topic"].id), "difficulty": "easy", "question_types": ["mcq", "numerical"], "question_count": 2, "time_limit_minutes": 30})
    assert exam_response.status_code == 201
    exam = exam_response.json()["data"]
    assert all("correct_answer" not in item["question"] for item in exam["questions"])

    start_response = client.post(f"/api/v1/exams/{exam['id']}/attempts", headers=student_headers)
    assert start_response.status_code == 201
    attempt_id = start_response.json()["data"]["id"]
    assert client.post(f"/api/v1/exams/{exam['id']}/attempts", headers=student_headers).status_code == 200
    assert "correct_answer" not in client.get(f"/api/v1/attempts/{attempt_id}", headers=student_headers).json()["data"]["exam"]["questions"][0]["question"]

    answers = [{"question_id": item["question"]["id"], "answer": "A" if item["question"]["question_type"] == "mcq" else "104 m"} for item in exam["questions"]]
    submission = client.post(f"/api/v1/attempts/{attempt_id}/submit", headers=student_headers, json={"answers": answers})
    assert submission.status_code == 201
    result = submission.json()["data"]
    assert result["score"] == "5.00"
    assert result["percentage"] == "100.00"
    assert len(result["answers"]) == 2
    assert client.post(f"/api/v1/attempts/{attempt_id}/submit", headers=student_headers, json={"answers": answers}).status_code == 200

    progress = client.get("/api/v1/students/me/progress", headers=student_headers)
    assert progress.status_code == 200
    assert progress.json()["data"][0]["attempts"] == 1
    assert progress.json()["data"][0]["score_percentage"] == "100.00"
    assert client.get("/api/v1/students/me/weak-topics", headers=student_headers).json()["data"] == []
    assert client.get("/api/v1/students/me/attempts", headers=student_headers).json()["meta"]["total"] == 1
    assert client.get("/api/v1/teachers/me/dashboard", headers=teacher_headers).json()["data"]["questions"] == {"generated": 0, "validated": 2, "rejected": 1}