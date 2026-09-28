import streamlit as st

from components.api import require_auth


def _open_student_page(page_path: str, title: str) -> None:
    if st.button("Go to page", key=f"student_hub_{title}", use_container_width=True):
        st.switch_page(st.Page(page_path, title=title))


def render_student_hub() -> None:
    st.title("Student Hub")
    if not require_auth("student"):
        return
    student = st.session_state.get("user", {})
    first_name = student.get("full_name", "").split()
    if first_name:
        st.caption(f"Welcome back, {first_name[0]}. What would you like to work on?")
    else:
        st.caption("Choose where you would like to continue your learning.")

    destinations = [
        ("📈", "Dashboard", "Review your progress, scores, and areas to practice.", "pages/1_Dashboard.py"),
        ("📝", "Exam", "Continue an assigned exam or start a practice session.", "pages/2_Exam.py"),
        ("🎯", "Results", "Review completed exams and question explanations.", "pages/3_Results.py"),
    ]
    columns = st.columns(3, gap="medium")
    for column, (icon, title, description, page_path) in zip(columns, destinations):
        with column:
            with st.container(border=True):
                st.markdown(f"### {icon}  {title}")
                st.caption(description)
                _open_student_page(page_path, title)
