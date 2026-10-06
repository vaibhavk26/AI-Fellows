"""Browser E2E tests for the React app in capstone/web (served on E2E_WEB_URL, default :5173)."""

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


def _wait_for_student_assignment(api_url: str, credentials: dict[str, str], exam_id: str) -> None:
    login = requests.post(f"{api_url}/api/v1/auth/login", json=credentials, timeout=10)
    login.raise_for_status()
    headers = {"Authorization": f"Bearer {login.json()['data']['access_token']}"}
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        response = requests.get(f"{api_url}/api/v1/students/me/assignments", headers=headers, timeout=10)
        response.raise_for_status()
        if any(item["exam_id"] == exam_id for item in response.json()["data"]):
            return
        time.sleep(0.25)
    raise AssertionError("Assigned exam did not appear in the student's assignments")

SUBMITTED = re.compile(r"Quest report")


def _sign_in(page: Page, credentials: dict[str, str], web_url: str) -> None:
    page.goto(f"{web_url}/login")
    page.get_by_label("Email").fill(credentials["email"])
    page.get_by_label("Password").fill(credentials["password"])
    page.get_by_role("button", name="Sign in").click()
    page.get_by_role("button", name="Sign out").first.wait_for()


def _nav(page: Page, label: str) -> None:
    page.get_by_role("navigation").get_by_role("link", name=label, exact=True).click()


def _submit_exam(page: Page) -> None:
    page.get_by_role("button", name="Submit exam").click()
    page.get_by_role("dialog").get_by_role("button", name="Submit exam").click()
    page.get_by_role("heading", name=SUBMITTED).wait_for(timeout=15_000)


def _pick_first_option(page: Page) -> None:
    page.get_by_role("radio").first.click()


def test_invalid_login_shows_error(page: Page, web_url: str):
    page.goto(f"{web_url}/login")
    page.get_by_label("Email").fill("missing-user@example.com")
    page.get_by_label("Password").fill("WrongPassword123!")
    page.get_by_role("button", name="Sign in").click()
    page.get_by_text(re.compile("invalid credentials", re.I)).wait_for()


def test_unauthenticated_user_is_redirected_to_login(page: Page, web_url: str):
    page.goto(f"{web_url}/exam")
    page.get_by_role("button", name="Sign in").wait_for()


def test_student_can_register_sign_in_and_sign_out(page: Page, web_url: str):
    email = f"react-student-{uuid4()}@example.com"
    page.goto(f"{web_url}/login")
    page.get_by_role("tab", name="Create account").click()
    page.get_by_label("Full name").fill("React Student")
    page.get_by_label("Email").fill(email)
    page.get_by_label("Password").fill("StrongPassword123!")
    page.get_by_role("button", name=re.compile("Create account|Sign up|Start", re.I)).last.click()
    page.get_by_text("Account created").wait_for()
    page.get_by_label("Password").fill("StrongPassword123!")
    page.get_by_role("button", name="Sign in").click()
    page.get_by_role("heading", name=re.compile("Ready to level up")).wait_for()
    page.get_by_role("button", name="Sign out").first.click()
    page.get_by_role("button", name="Sign in").wait_for()


def test_student_progress_and_empty_results_states(page: Page, student_credentials: dict[str, str], web_url: str):
    _sign_in(page, student_credentials, web_url)
    _nav(page, "Progress")
    page.get_by_role("heading", name=re.compile("Your progress")).wait_for()
    page.get_by_label("Subject").wait_for()
    page.get_by_label("Chapter").wait_for()
    page.get_by_label("Period").wait_for()

    _nav(page, "Results")
    page.get_by_role("heading", name="No results yet").wait_for()


def test_student_cannot_reach_teacher_screens(page: Page, student_credentials: dict[str, str], web_url: str):
    _sign_in(page, student_credentials, web_url)
    assert page.get_by_role("link", name="Roster").count() == 0
    assert page.get_by_role("link", name="Generate", exact=True).count() == 0
    page.goto(f"{web_url}/generate")
    page.get_by_role("heading", name="Generate questions").wait_for(state="detached", timeout=5_000)


def test_teacher_hub_shows_analytics(page: Page, teacher_credentials: dict[str, str], web_url: str):
    _sign_in(page, teacher_credentials, web_url)
    page.get_by_role("heading", name=re.compile("Welcome")).wait_for()
    page.get_by_role("heading", name="Assessment analytics").wait_for()


def test_teacher_can_view_question_bank(page: Page, teacher_credentials: dict[str, str], web_url: str):
    _sign_in(page, teacher_credentials, web_url)
    _nav(page, "Bank")
    page.get_by_role("heading", name="Browse questions").wait_for()
    page.get_by_label("Status").wait_for()
    page.get_by_text(re.compile(r"questions? match(es)? these filters")).wait_for(timeout=15_000)


def test_teacher_question_bank_handles_empty_bank(page: Page, empty_teacher_credentials: dict[str, str], api_url: str, web_url: str):
    login = requests.post(f"{api_url}/api/v1/auth/login", json=empty_teacher_credentials, timeout=10)
    login.raise_for_status()
    headers = {"Authorization": f"Bearer {login.json()['data']['access_token']}"}
    bank = requests.get(f"{api_url}/api/v1/questions", params={"page_size": 1}, headers=headers, timeout=10)
    if bank.json().get("data"):
        pytest.skip("The question bank is shared and already populated in this environment")

    _sign_in(page, empty_teacher_credentials, web_url)
    _nav(page, "Bank")
    page.get_by_text(re.compile(r"^0 questions? match")).wait_for(timeout=15_000)


def test_teacher_generation_controls_render(page: Page, teacher_credentials: dict[str, str], web_url: str):
    _sign_in(page, teacher_credentials, web_url)
    _nav(page, "Generate")
    page.get_by_role("heading", name="Generate questions").wait_for()
    page.get_by_label("Question type").wait_for()
    page.get_by_label("Difficulty").wait_for()
    page.get_by_role("button", name="Generate", exact=True).wait_for()


def test_teacher_adds_student_from_roster_page(
    page: Page,
    teacher_credentials: dict[str, str],
    student_credentials: dict[str, str],
    web_url: str,
):
    _sign_in(page, teacher_credentials, web_url)
    _nav(page, "Roster")
    page.get_by_role("heading", name="Student roster").wait_for()
    page.get_by_label("Student email").fill(student_credentials["email"])
    page.get_by_role("button", name="Add student").click()
    page.get_by_text(re.compile(r"Added .* to your roster")).wait_for()


def test_teacher_creates_assessment_from_create_tab(
    page: Page,
    teacher_credentials: dict[str, str],
    assignment_exam: dict,
    populated_bank: dict,
    web_url: str,
):
    _sign_in(page, teacher_credentials, web_url)
    _nav(page, "Assess")
    page.get_by_role("tab", name="Create Assessment").click()
    page.get_by_label("Subject").select_option(label=populated_bank["subject_name"])
    page.get_by_label("Chapter").select_option(label=populated_bank["chapter_name"])
    page.get_by_label("Exam title").fill(f"UI assessment {uuid4().hex[:8]}")
    page.get_by_role("button", name="Create assessment").click()
    page.get_by_text("created successfully").wait_for(timeout=90_000)
    page.get_by_role("button", name="Proceed to Assign Assessment").wait_for()


def test_assign_requires_a_student_selection(
    page: Page,
    teacher_credentials: dict[str, str],
    assignment_exam: dict,
    web_url: str,
):
    _sign_in(page, teacher_credentials, web_url)
    _nav(page, "Assess")
    page.get_by_role("tab", name="Assign Assessment").click()
    page.get_by_role("button", name="Assign assessment", exact=True).click()
    page.get_by_text("Select at least one student.").wait_for()


def test_teacher_assigns_exam_and_student_completes_it(
    page: Page,
    teacher_credentials: dict[str, str],
    student_credentials: dict[str, str],
    assignment_exam: dict,
    api_url: str,
    web_url: str,
):
    _sign_in(page, teacher_credentials, web_url)
    _nav(page, "Assess")
    page.get_by_role("tab", name="Assign Assessment").click()
    page.get_by_label("Assessment").select_option(value=assignment_exam["id"])
    page.get_by_role("checkbox", name=re.compile(re.escape(student_credentials["email"]))).click()
    page.get_by_role("button", name="Assign assessment", exact=True).click()
    page.get_by_text(re.compile(r"assigned to 1 student")).wait_for()
    _wait_for_student_assignment(api_url, student_credentials, assignment_exam["id"])

    page.get_by_role("button", name="Sign out").first.click()
    _sign_in(page, student_credentials, web_url)
    page.get_by_text(assignment_exam["title"], exact=True).wait_for()
    page.get_by_role("link", name=re.compile("Start quest")).first.click()
    page.get_by_role("button", name="Submit exam").wait_for(timeout=15_000)
    _pick_first_option(page)
    _submit_exam(page)

    _nav(page, "Exam")
    page.get_by_text("Completed", exact=True).wait_for()


def test_student_can_submit_numerical_answer(
    page: Page,
    student_credentials: dict[str, str],
    numerical_bank: dict,
    web_url: str,
):
    _sign_in(page, student_credentials, web_url)
    _nav(page, "Exam")
    page.get_by_label("Subject").select_option(label=numerical_bank["subject_name"])
    page.get_by_label("Chapter").select_option(label=numerical_bank["chapter_name"])
    page.get_by_role("button", name="Multiple choice").click()
    page.get_by_role("button", name="Numerical").click()
    page.get_by_label(re.compile("Questions:")).fill("1")
    page.get_by_role("button", name="Generate exam").click()
    page.get_by_label("Your answer").fill("0", timeout=90_000)
    _submit_exam(page)


def test_student_can_complete_three_question_exam_and_review(
    page: Page,
    student_credentials: dict[str, str],
    populated_bank: dict,
    web_url: str,
):
    _sign_in(page, student_credentials, web_url)
    _nav(page, "Exam")
    page.get_by_label("Subject").select_option(label=populated_bank["subject_name"])
    page.get_by_label("Chapter").select_option(label=populated_bank["chapter_name"])
    page.get_by_label(re.compile("Questions:")).fill("3")
    page.get_by_role("button", name="Generate exam").click()
    page.get_by_role("button", name="Submit exam").wait_for(timeout=90_000)

    for index in range(3):
        _pick_first_option(page)
        if index < 2:
            page.get_by_role("button", name="Next").click()
    page.get_by_role("button", name="Go to question 3, answered").wait_for()

    # A reload must not lose the attempt in progress.
    page.reload()
    page.get_by_role("button", name="Submit exam").wait_for(timeout=15_000)
    _submit_exam(page)
    page.get_by_role("heading", name="Question review").wait_for(timeout=15_000)
    page.get_by_text(re.compile(r"^Q3\.")).wait_for()

    _nav(page, "Progress")
    page.get_by_role("heading", name=re.compile("Your progress")).wait_for()
    page.get_by_role("cell", name="Practice Exam").first.wait_for()
