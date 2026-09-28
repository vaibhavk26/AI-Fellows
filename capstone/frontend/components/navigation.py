import streamlit as st

from components.teacher_pages import (
    render_analytics,
    render_assessments,
    render_question_bank,
    render_roster,
)


def navigation_spec(user: dict | None, sign_in_page, sign_up_page) -> dict[str, list[tuple[object, str]]]:
    """Describe the page set available to a persona without rendering it."""
    if user and user.get("role") == "teacher":
        return {
            "Teacher Workspace": [
                ("pages/4_Teacher.py", "Teacher Hub"),
                (render_analytics, "Analytics"),
                (render_roster, "Roster"),
                (render_assessments, "Assessments"),
                (render_question_bank, "Question Bank"),
                ("pages/5_Generate.py", "Generate Questions"),
            ]
        }
    if user and user.get("role") == "student":
        return {
            "Student Workspace": [
                ("pages/0_Student.py", "Student Hub"),
                ("pages/1_Dashboard.py", "Dashboard"),
                ("pages/2_Exam.py", "Exam"),
                ("pages/3_Results.py", "Results"),
            ]
        }
    return {
        "Account": [
            (sign_in_page, "Sign In"),
            (sign_up_page, "Sign Up"),
        ]
    }


def build_navigation(user: dict | None, sign_in_page, sign_up_page) -> dict[str, list]:
    """Build Streamlit pages from the persona-specific navigation spec."""
    return {
        section: [st.Page(page, title=title) for page, title in pages]
        for section, pages in navigation_spec(user, sign_in_page, sign_up_page).items()
    }
