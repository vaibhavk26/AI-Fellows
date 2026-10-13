import os
from pathlib import Path
from uuid import uuid4

import pytest
import requests
from dotenv import dotenv_values
from playwright.sync_api import Browser, Page, sync_playwright


API_URL = os.getenv("E2E_API_URL", "http://localhost:8000").rstrip("/")
WEB_URL = os.getenv("E2E_WEB_URL", "http://localhost:5173").rstrip("/")
LOCAL_ENV_FILE = Path(__file__).resolve().parents[2] / ".env.local"


def _teacher_login_credentials(env_file: Path = LOCAL_ENV_FILE) -> tuple[str | None, str | None]:
    file_values = dotenv_values(env_file)
    return (
        os.getenv("E2E_TEACHER_EMAIL") or file_values.get("E2E_TEACHER_EMAIL"),
        os.getenv("E2E_TEACHER_PASSWORD") or file_values.get("E2E_TEACHER_PASSWORD"),
    )


def _skip_if_unavailable(url: str | None = None) -> None:
    try:
        response = requests.get(f"{API_URL}/health", timeout=3)
        response.raise_for_status()
        if url:
            requests.get(url, timeout=3).raise_for_status()
    except requests.RequestException as error:
        pytest.skip(f"E2E services are unavailable: {error}")


@pytest.fixture(scope="session")
def browser() -> Browser:
    _skip_if_unavailable()
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        yield browser
        browser.close()


@pytest.fixture(scope="session")
def web_url() -> str:
    _skip_if_unavailable(WEB_URL)
    return WEB_URL


@pytest.fixture(scope="session")
def api_url() -> str:
    return API_URL


@pytest.fixture
def page(browser: Browser) -> Page:
    context = browser.new_context()
    page = context.new_page()
    page.set_default_timeout(15_000)
    yield page
    context.close()


@pytest.fixture
def student_credentials() -> dict[str, str]:
    credentials = {
        "email": f"e2e-student-{uuid4()}@example.com",
        "password": "StrongPassword123!",
    }
    response = requests.post(
        f"{API_URL}/api/v1/auth/register",
        json={**credentials, "full_name": "Browser Student", "role": "student", "class_level": 10},
        timeout=10,
    )
    response.raise_for_status()
    return credentials


@pytest.fixture
def teacher_credentials() -> dict[str, str]:
    configured_email, configured_password = _teacher_login_credentials()
    if configured_email and configured_password:
        return {"email": configured_email, "password": configured_password}
    credentials = {
        "email": f"e2e-teacher-{uuid4()}@example.com",
        "password": "StrongPassword123!",
    }
    response = requests.post(
        f"{API_URL}/api/v1/auth/register",
        json={**credentials, "full_name": "Browser Teacher", "role": "teacher"},
        timeout=10,
    )
    response.raise_for_status()
    return credentials


@pytest.fixture
def empty_teacher_credentials() -> dict[str, str]:
    credentials = {
        "email": f"e2e-empty-teacher-{uuid4()}@example.com",
        "password": "StrongPassword123!",
    }
    response = requests.post(
        f"{API_URL}/api/v1/auth/register",
        json={**credentials, "full_name": "Empty Bank Teacher", "role": "teacher"},
        timeout=10,
    )
    response.raise_for_status()
    return credentials


@pytest.fixture
def populated_bank() -> dict:
    teacher_email, teacher_password = _teacher_login_credentials()
    if not teacher_email or not teacher_password:
        pytest.skip("Set E2E_TEACHER_EMAIL and E2E_TEACHER_PASSWORD for populated-bank E2E tests")
    login = requests.post(
        f"{API_URL}/api/v1/auth/login",
        json={"email": teacher_email, "password": teacher_password},
        timeout=10,
    )
    login.raise_for_status()
    headers = {"Authorization": f"Bearer {login.json()['data']['access_token']}"}
    questions = requests.get(
        f"{API_URL}/api/v1/questions",
        params={"status": "validated", "question_type": "mcq", "difficulty": "easy", "page_size": 100},
        headers=headers,
        timeout=10,
    )
    questions.raise_for_status()
    rows = questions.json().get("data", [])
    by_chapter: dict[str, list[dict]] = {}
    for question in rows:
        by_chapter.setdefault(str(question["chapter_id"]), []).append(question)
    matching = next((items for items in by_chapter.values() if len(items) >= 3), None)
    if matching is None:
        pytest.skip("Need at least three validated easy MCQs in one chapter for the multi-question E2E test")
    first = matching[0]
    subjects = requests.get(
        f"{API_URL}/api/v1/curriculum/subjects",
        params={"page_size": 100},
        headers=headers,
        timeout=10,
    ).json()["data"]
    subject = next(item for item in subjects if item["id"] == first["subject_id"])
    chapters = requests.get(
        f"{API_URL}/api/v1/curriculum/subjects/{subject['id']}/chapters",
        params={"page_size": 100},
        headers=headers,
        timeout=10,
    ).json()["data"]
    chapter = next(item for item in chapters if item["id"] == first["chapter_id"])
    return {
        "questions": matching,
        "subject_id": first["subject_id"],
        "subject_name": subject["name"],
        "chapter_id": first["chapter_id"],
        "chapter_name": chapter["name"],
    }


@pytest.fixture
def assignment_exam(
    teacher_credentials: dict[str, str],
    student_credentials: dict[str, str],
    populated_bank: dict,
) -> dict:
    login = requests.post(
        f"{API_URL}/api/v1/auth/login",
        json=teacher_credentials,
        timeout=10,
    )
    login.raise_for_status()
    headers = {"Authorization": f"Bearer {login.json()['data']['access_token']}"}
    roster_response = requests.post(
        f"{API_URL}/api/v1/teachers/me/students",
        headers=headers,
        json={"email": student_credentials["email"]},
        timeout=10,
    )
    roster_response.raise_for_status()
    roster = requests.get(f"{API_URL}/api/v1/teachers/me/students", headers=headers, timeout=10)
    roster.raise_for_status()
    assert any(student["email"] == student_credentials["email"] for student in roster.json()["data"])
    response = requests.post(
        f"{API_URL}/api/v1/exams/generate",
        headers=headers,
        json={
            "title": f"Browser assignment {uuid4().hex[:8]}",
            "subject_id": populated_bank["subject_id"],
            "chapter_id": populated_bank["chapter_id"],
            "difficulty": "easy",
            "question_types": ["mcq"],
            "question_count": 1,
            "time_limit_minutes": 20,
        },
        timeout=90,
    )
    response.raise_for_status()
    return response.json()["data"]


@pytest.fixture
def numerical_bank() -> dict:
    teacher_email, teacher_password = _teacher_login_credentials()
    if not teacher_email or not teacher_password:
        pytest.skip("Set E2E_TEACHER_EMAIL and E2E_TEACHER_PASSWORD for numerical E2E tests")
    login = requests.post(
        f"{API_URL}/api/v1/auth/login",
        json={"email": teacher_email, "password": teacher_password},
        timeout=10,
    )
    login.raise_for_status()
    headers = {"Authorization": f"Bearer {login.json()['data']['access_token']}"}
    response = requests.get(
        f"{API_URL}/api/v1/questions",
        params={"status": "validated", "question_type": "numerical", "difficulty": "easy", "page_size": 100},
        headers=headers,
        timeout=10,
    )
    response.raise_for_status()
    rows = response.json().get("data", [])
    if not rows:
        pytest.skip("Need at least one validated easy numerical question for the numerical E2E test")
    first = rows[0]
    subjects = requests.get(
        f"{API_URL}/api/v1/curriculum/subjects",
        params={"page_size": 100},
        headers=headers,
        timeout=10,
    ).json()["data"]
    subject = next(item for item in subjects if item["id"] == first["subject_id"])
    chapters = requests.get(
        f"{API_URL}/api/v1/curriculum/subjects/{subject['id']}/chapters",
        params={"page_size": 100},
        headers=headers,
        timeout=10,
    ).json()["data"]
    chapter = next(item for item in chapters if item["id"] == first["chapter_id"])
    return {"subject_name": subject["name"], "chapter_name": chapter["name"]}