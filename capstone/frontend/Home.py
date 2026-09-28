import streamlit as st

from components.api import ApiError, post
from components.navigation import build_navigation
from components.sidebar import render_account_controls


st.set_page_config(
    page_title="ExamIQ",
    page_icon="📘",
    layout="wide",
    initial_sidebar_state="expanded",
)


def sign_in_page() -> None:
    st.title("ExamIQ")
    st.write("A focused workspace for curriculum-grounded practice and feedback.")
    st.subheader("Sign in")
    with st.form("login"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign in", type="primary", use_container_width=True)
    if submitted:
        try:
            result = post("/api/v1/auth/login", json={"email": email, "password": password})["data"]
            st.session_state.access_token = result["access_token"]
            st.session_state.user = result["user"]
            st.rerun()
        except ApiError as error:
            st.error(error.message)


def sign_up_page() -> None:
    st.title("ExamIQ")
    st.write("A focused workspace for curriculum-grounded practice and feedback.")
    st.subheader("Create an account")
    with st.form("register"):
        name = st.text_input("Full name")
        email = st.text_input("Email", key="register_email")
        password = st.text_input("Password", type="password", key="register_password")
        role = st.selectbox("Account type", ["student", "teacher"])
        class_level = st.number_input("Class level", min_value=10, max_value=10, value=10) if role == "student" else None
        submitted = st.form_submit_button("Register", use_container_width=True)
    if submitted:
        try:
            post("/api/v1/auth/register", json={
                "full_name": name,
                "email": email,
                "password": password,
                "role": role,
                "class_level": class_level,
            })
            st.success("Account created. Sign in to continue.")
        except ApiError as error:
            st.error(error.message)


user = st.session_state.get("user")
navigation = build_navigation(user, sign_in_page, sign_up_page)

page = st.navigation(navigation, position="sidebar")
render_account_controls(user)

page.run()
