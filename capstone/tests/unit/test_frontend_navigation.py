from pathlib import Path
import sys

from streamlit.testing.v1 import AppTest


FRONTEND_ROOT = Path(__file__).resolve().parents[2] / "frontend"
if str(FRONTEND_ROOT) not in sys.path:
    sys.path.insert(0, str(FRONTEND_ROOT))

from components.navigation import navigation_spec  # noqa: E402
from components.teacher_pages import _filter_questions  # noqa: E402
from components import api as api_client  # noqa: E402


def _page_titles(navigation: dict) -> list[str]:
    return [title for pages in navigation.values() for _, title in pages]


def _placeholder_page() -> None:
    pass


def test_sidebar_navigation_is_persona_scoped():
    teacher_pages = _page_titles(navigation_spec(
        {"role": "teacher"}, _placeholder_page, _placeholder_page
    ))
    student_pages = _page_titles(navigation_spec(
        {"role": "student"}, _placeholder_page, _placeholder_page
    ))
    auth_pages = _page_titles(navigation_spec(None, _placeholder_page, _placeholder_page))

    assert teacher_pages == [
        "Teacher Hub", "Analytics", "Roster", "Assessments", "Question Bank", "Generate Questions"
    ]
    assert student_pages == ["Student Hub", "Dashboard", "Exam", "Results"]
    assert auth_pages == ["Sign In", "Sign Up"]
    assert set(teacher_pages).isdisjoint(student_pages)


def test_teacher_hub_renders_actions_without_backend_calls(monkeypatch):
    monkeypatch.chdir(FRONTEND_ROOT)
    app = AppTest.from_file("pages/4_Teacher.py")
    app.session_state["user"] = {"full_name": "Test Teacher", "role": "teacher"}
    app.run()

    assert not app.exception
    assert [title.value for title in app.title] == ["Teacher Hub"]
    assert [button.label for button in app.button] == ["Go to page"] * 4


def test_student_hub_renders_all_student_destinations(monkeypatch):
    monkeypatch.chdir(FRONTEND_ROOT)
    app = AppTest.from_file("pages/0_Student.py")
    app.session_state["user"] = {"full_name": "Test Student", "role": "student"}
    app.run()

    assert not app.exception
    assert [title.value for title in app.title] == ["Student Hub"]
    assert [button.label for button in app.button] == ["Go to page"] * 3
    card_text = " ".join(item.value for item in app.markdown)
    assert all(label in card_text for label in ("Dashboard", "Exam", "Results"))


def test_student_hub_rejects_teacher_persona(monkeypatch):
    monkeypatch.chdir(FRONTEND_ROOT)
    app = AppTest.from_file("pages/0_Student.py")
    app.session_state["user"] = {"full_name": "Test Teacher", "role": "teacher"}
    app.run()

    assert not app.exception
    assert any("available only to students" in item.value for item in app.error)
    assert not app.button


def test_teacher_hub_rejects_student_persona(monkeypatch):
    monkeypatch.chdir(FRONTEND_ROOT)
    app = AppTest.from_file("pages/4_Teacher.py")
    app.session_state["user"] = {"full_name": "Test Student", "role": "student"}
    app.run()

    assert not app.exception
    assert any("available only to teachers" in item.value for item in app.error)
    assert not app.button


def test_question_bank_filters_compose_across_all_requested_fields():
    questions = [
        {
            "id": "q1", "subject_id": "math", "chapter_id": "trig", "topic_id": "ratios",
            "difficulty": "easy", "question_type": "mcq", "status": "validated",
        },
        {
            "id": "q2", "subject_id": "math", "chapter_id": "trig", "topic_id": "identities",
            "difficulty": "hard", "question_type": "numerical", "status": "rejected",
        },
        {
            "id": "q3", "subject_id": "physics", "chapter_id": "light", "topic_id": "reflection",
            "difficulty": "easy", "question_type": "mcq", "status": "generated",
        },
    ]

    result = _filter_questions(
        questions,
        subject_id="math",
        chapter_id="trig",
        topic_id="identities",
        difficulty="hard",
        question_type="numerical",
        status="rejected",
    )

    assert [question["id"] for question in result] == ["q2"]


def test_private_cached_responses_are_partitioned_by_access_token(monkeypatch):
    calls = []

    def fake_get(path, **kwargs):
        token = kwargs["access_token"]
        calls.append((path, token))
        if path.endswith("/attempts"):
            return {"data": [{"owner_token": token}]}
        if path.startswith("/api/v1/attempts/"):
            return {"data": {"owner_token": token}}
        return {"data": [{"owner_token": token}]}

    monkeypatch.setattr(api_client, "get", fake_get)
    api_client.get_student_attempts.clear()
    api_client.get_attempt_detail.clear()
    api_client.get_teacher_questions.clear()

    assert api_client.get_student_attempts("student-a") == [{"owner_token": "student-a"}]
    assert api_client.get_student_attempts("student-b") == [{"owner_token": "student-b"}]
    assert api_client.get_attempt_detail("attempt-1", "student-a")["owner_token"] == "student-a"
    assert api_client.get_attempt_detail("attempt-1", "student-b")["owner_token"] == "student-b"
    assert api_client.get_teacher_questions("teacher-a") == [{"owner_token": "teacher-a"}]
    assert api_client.get_teacher_questions("teacher-b") == [{"owner_token": "teacher-b"}]
    assert len(calls) == 6
