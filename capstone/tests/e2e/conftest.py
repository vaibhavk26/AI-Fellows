import os
from uuid import uuid4

import pytest
import requests
from playwright.sync_api import Browser, Page, sync_playwright


API_URL = os.getenv("E2E_API_URL", "http://localhost:8000").rstrip("/")
FRONTEND_URL = os.getenv("E2E_FRONTEND_URL", "http://localhost:8501").rstrip("/")


def _skip_if_unavailable() -> None:
    try:
        response = requests.get(f"{API_URL}/health", timeout=3)
        response.raise_for_status()
        requests.get(FRONTEND_URL, timeout=3).raise_for_status()
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
def frontend_url() -> str:
    return FRONTEND_URL


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
    configured_email = os.getenv("E2E_TEACHER_EMAIL")
    configured_password = os.getenv("E2E_TEACHER_PASSWORD")
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
    teacher_email = os.getenv("E2E_TEACHER_EMAIL")
    teacher_password = os.getenv("E2E_TEACHER_PASSWORD")
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
def numerical_bank() -> dict:
    teacher_email = os.getenv("E2E_TEACHER_EMAIL")
    teacher_password = os.getenv("E2E_TEACHER_PASSWORD")
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