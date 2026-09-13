import re
from uuid import uuid4

import pytest
from playwright.sync_api import Page


pytestmark = pytest.mark.e2e


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
    page.get_by_role("heading", name="Progress dashboard").wait_for()
    page.get_by_role("button", name="Sign out").click()

    page.goto(f"{frontend_url}/")
    page.get_by_role("tabpanel", name="Sign in").wait_for()


def test_student_dashboard_and_empty_results_states(page: Page, student_credentials: dict[str, str], frontend_url: str):
    _sign_in(page, student_credentials, frontend_url)
    page.get_by_role("link", name="Dashboard").click()
    page.get_by_role("heading", name="Progress dashboard").wait_for()
    page.get_by_text("Topics practiced").wait_for()

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