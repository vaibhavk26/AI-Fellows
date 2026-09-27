import re
import time
from uuid import uuid4

import pytest
import requests
from playwright.sync_api import Page

from tests.e2e.conftest import _teacher_login_credentials


pytestmark = pytest.mark.e2e


def test_e2e_teacher_credentials_load_from_env_file(tmp_path, monkeypatch):
    monkeypatch.delenv("E2E_TEACHER_EMAIL", raising=False)
    monkeypatch.delenv("E2E_TEACHER_PASSWORD", raising=False)
    env_file = tmp_path / ".env.local"
    env_file.write_text(
        "E2E_TEACHER_EMAIL=teacher@example.com\nE2E_TEACHER_PASSWORD=test-password\n",
        encoding="utf-8",
    )

    assert _teacher_login_credentials(env_file) == ("teacher@example.com", "test-password")


def _sign_in(page: Page, credentials: dict[str, str], frontend_url: str) -> None:
    page.goto(f"{frontend_url}/")
    page.get_by_role("tabpanel", name="Sign in").get_by_label("Email").fill(credentials["email"])
    page.get_by_role("tabpanel", name="Sign in").get_by_role("textbox", name="Password").fill(credentials["password"])
    page.get_by_role("tabpanel", name="Sign in").get_by_role("button", name="Sign in").click()
    page.get_by_text("Welcome back").wait_for()


def _register(page: Page, frontend_url: str, role: str = "student") -> dict[str, str]:
    credentials = {"email": f"browser-{role}-{uuid4()}@example.com", "password": "StrongPassword123!"}
    page.goto(f"{frontend_url}/")
    page.get_by_role("tab", name="Create account").click()
    panel = page.get_by_role("tabpanel", name="Create account")
    panel.get_by_label("Full name").fill(f"Browser {role.title()}")
    panel.get_by_label("Email").fill(credentials["email"])
    panel.get_by_role("textbox", name="Password").fill(credentials["password"])
    if role == "teacher":
        panel.get_by_role("combobox", name=re.compile("Account type")).click()
        page.get_by_text("teacher", exact=True).last.click()
    panel.get_by_role("button", name="Register").click()
    page.get_by_text("Account created. Sign in to continue.").wait_for()
    return credentials


def _wait_for_student_assignment(api_url: str, credentials: dict[str, str], exam_id: str) -> None:
    login = requests.post(f"{api_url}/api/v1/auth/login", json=credentials, timeout=10)
    login.raise_for_status()
    headers = {"Authorization": f"Bearer {login.json()['data']['access_token']}"}
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        response = requests.get(
            f"{api_url}/api/v1/students/me/assignments",
            headers=headers,
            timeout=10,
        )
        response.raise_for_status()
        if any(item["exam_id"] == exam_id for item in response.json()["data"]):
            return
        time.sleep(0.25)
    raise AssertionError("Assigned exam did not appear in the student's assignments")


def test_teacher_can_view_validated_question_bank(page: Page, teacher_credentials: dict[str, str], frontend_url: str):
    _sign_in(page, teacher_credentials, frontend_url)
    page.get_by_role("link", name="Teacher").click()

    page.get_by_role("heading", name="Question bank").wait_for()
    page.get_by_text("Validated", exact=True).wait_for(timeout=15_000)
    assert "Validated" in page.locator("body").inner_text()
    page.get_by_text("Your questions and validated bank").wait_for(timeout=15_000)


def test_teacher_question_bank_handles_empty_bank(page: Page, empty_teacher_credentials: dict[str, str], frontend_url: str):
    _sign_in(page, empty_teacher_credentials, frontend_url)
    page.get_by_role("link", name="Teacher").click()

    page.get_by_role("heading", name="Question bank").wait_for()
    page.get_by_text("Validated", exact=True).wait_for(timeout=15_000)
    assert "Generated" in page.locator("body").inner_text()
    assert "Rejected" in page.locator("body").inner_text()
    page.get_by_text("Your questions and validated bank").wait_for(timeout=15_000)


def test_invalid_login_shows_error(page: Page, frontend_url: str):
    page.goto(f"{frontend_url}/")
    panel = page.get_by_role("tabpanel", name="Sign in")
    panel.get_by_label("Email").fill("missing-user@example.com")
    panel.get_by_role("textbox", name="Password").fill("WrongPassword123!")
    panel.get_by_role("button", name="Sign in").click()

    page.get_by_text("Invalid credentials").wait_for()


def test_student_can_register_and_sign_out(page: Page, frontend_url: str):
    credentials = _register(page, frontend_url)
    _sign_in(page, credentials, frontend_url)
    page.get_by_role("link", name="Dashboard").click()
    page.get_by_role("heading", name="Student Performance").wait_for()
    page.get_by_role("button", name="Sign out").click()

    page.goto(f"{frontend_url}/")
    page.get_by_role("tabpanel", name="Sign in").wait_for()


def test_student_dashboard_and_empty_results_states(page: Page, student_credentials: dict[str, str], frontend_url: str):
    _sign_in(page, student_credentials, frontend_url)
    page.get_by_role("link", name="Dashboard").click()
    page.get_by_role("heading", name="Student Performance").wait_for()
    page.get_by_text("Exam attempts").wait_for()
    page.get_by_role("combobox", name="Subject").wait_for()
    page.get_by_role("combobox", name="Chapter").wait_for()
    page.get_by_role("combobox", name="Period").wait_for()

    page.get_by_role("link", name="Results").click()
    page.get_by_role("heading", name="Results").wait_for()
    page.get_by_text("Submit an exam to see detailed results here.").wait_for()


def test_student_is_blocked_from_teacher_workflow(page: Page, student_credentials: dict[str, str], frontend_url: str):
    _sign_in(page, student_credentials, frontend_url)
    page.get_by_role("link", name="Teacher").click()
    page.get_by_role("heading", name="Question bank").wait_for()

    page.get_by_text("This page is available only to teachers.").wait_for()


def test_teacher_generation_controls_render(page: Page, teacher_credentials: dict[str, str], frontend_url: str):
    _sign_in(page, teacher_credentials, frontend_url)
    page.get_by_role("link", name="Generate").click()
    page.get_by_role("heading", name="Generate questions").wait_for()
    page.get_by_role("combobox", name=re.compile("Question type")).wait_for()
    page.get_by_role("combobox", name=re.compile("Difficulty")).wait_for()
    page.get_by_role("button", name="Generate").wait_for()


def test_teacher_assigns_exam_and_student_completes_it(
    page: Page,
    teacher_credentials: dict[str, str],
    student_credentials: dict[str, str],
    assignment_exam: dict,
    api_url: str,
    frontend_url: str,
):
    _sign_in(page, teacher_credentials, frontend_url)
    page.get_by_role("link", name="Teacher").click()
    page.get_by_role("heading", name="Question bank").wait_for()
    page.get_by_text("Your questions and validated bank").wait_for(timeout=30_000)

    assessment_selector = page.get_by_role("combobox", name="Assessment")
    assessment_selector.wait_for(timeout=30_000)
    assessment_selector.click()
    page.get_by_text(assignment_exam["title"], exact=False).last.click()
    page.get_by_role("combobox", name="Students").click()
    student_option = page.get_by_role("option", name=re.compile(re.escape(student_credentials["email"])))
    student_option.wait_for(timeout=15_000)
    student_option.click()
    page.get_by_role("button", name="Assign exam").click()
    _wait_for_student_assignment(api_url, student_credentials, assignment_exam["id"])

    page.get_by_role("button", name="Sign out").click()
    _sign_in(page, student_credentials, frontend_url)
    page.get_by_role("link", name="Exam").click()
    page.get_by_role("heading", name="Practice exam").wait_for()
    page.get_by_text(assignment_exam["title"], exact=True).wait_for(timeout=15_000)
    page.get_by_role("button", name="Start").click()
    page.get_by_role("button", name="Submit exam").wait_for(timeout=15_000)
    page.get_by_role("radio").first.check()
    page.get_by_role("button", name="Submit exam").click()
    page.get_by_text("Exam submitted. Open Results to review your feedback.").wait_for(timeout=15_000)

    page.get_by_role("link", name="Dashboard").click()
    page.get_by_role("link", name="Exam").click()
    page.get_by_role("button", name="Completed").wait_for(timeout=15_000)


def test_student_can_submit_numerical_answer(
    page: Page,
    student_credentials: dict[str, str],
    numerical_bank: dict,
    frontend_url: str,
):
    _sign_in(page, student_credentials, frontend_url)
    page.get_by_role("link", name="Exam").click()
    page.get_by_role("heading", name="Practice exam").wait_for()
    page.get_by_role("combobox", name=re.compile("Subject$")).click()
    page.get_by_text(numerical_bank["subject_name"], exact=True).last.click()
    page.get_by_role("combobox", name=re.compile("Chapter$")).click()
    page.get_by_text(numerical_bank["chapter_name"], exact=True).last.click()

    page.get_by_role("combobox", name=re.compile("Question types")).click()
    page.get_by_role("button", name="Clear all").click()
    page.get_by_role("combobox", name=re.compile("Question types")).click()
    page.get_by_role("option", name="numerical").click()
    page.get_by_role("spinbutton", name="Questions").fill("1")
    page.get_by_role("button", name="Generate exam").click()
    page.get_by_role("button", name="Submit exam").wait_for(timeout=90_000)
    page.get_by_role("textbox", name="Answer").fill("0")
    page.get_by_role("button", name="Submit exam").click()
    page.get_by_text("Exam submitted. Open Results to review your feedback.").wait_for(timeout=15_000)


def test_student_can_complete_three_question_exam(
    page: Page,
    student_credentials: dict[str, str],
    populated_bank: dict,
    frontend_url: str,
):
    _sign_in(page, student_credentials, frontend_url)
    page.get_by_role("link", name="Exam").click()
    page.get_by_role("heading", name="Practice exam").wait_for()

    page.get_by_role("combobox", name=re.compile("Subject$")).click()
    page.get_by_text(populated_bank["subject_name"], exact=True).last.click()
    page.get_by_role("combobox", name=re.compile("Chapter$")).click()
    page.get_by_text(populated_bank["chapter_name"], exact=True).last.click()

    questions_input = page.get_by_role("spinbutton", name="Questions")
    questions_input.fill("3")
    assert questions_input.input_value() == "3"

    page.get_by_role("button", name="Generate exam").click()
    page.get_by_role("button", name="Submit exam").wait_for(timeout=90_000)
    radios = page.get_by_role("radio")
    assert radios.count() >= 12

    for index in (0, 4, 8):
        radios.nth(index).check()
    page.get_by_role("button", name="Submit exam").click()

    page.get_by_text("Exam submitted. Open Results to review your feedback.").wait_for(timeout=15_000)
    page.get_by_role("link", name="Results").click()
    page.get_by_role("heading", name="Results").wait_for()
    page.get_by_text("Answer review").wait_for(timeout=15_000)
    page.get_by_text("Question 3").wait_for(timeout=15_000)

    page.get_by_role("link", name="Dashboard").click()
    page.get_by_role("heading", name="Progress over attempts").wait_for(timeout=15_000)
    page.get_by_role("heading", name="Subject performance").wait_for(timeout=15_000)
    page.get_by_role("heading", name="Chapter performance").wait_for(timeout=15_000)
    page.get_by_role("heading", name="Topic performance").wait_for(timeout=15_000)

    page.get_by_role("link", name="Dashboard").click()
    page.get_by_role("heading", name="Subject performance").wait_for(timeout=15_000)
    page.get_by_role("heading", name="Chapter performance").wait_for(timeout=15_000)
    page.get_by_role("heading", name="Topic performance").wait_for(timeout=15_000)
    page.get_by_role("heading", name="Score by attempt").wait_for(timeout=15_000)