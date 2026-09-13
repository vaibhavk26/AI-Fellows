import streamlit as st

from components.api import ApiError, post


st.set_page_config(page_title="Capstone Learning", page_icon="📘", layout="wide")


def login() -> None:
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
			st.success("Signed in. Use the pages in the sidebar to begin.")
			st.rerun()
		except ApiError as error:
			st.error(error.message)


def register() -> None:
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
			post("/api/v1/auth/register", json={"full_name": name, "email": email, "password": password, "role": role, "class_level": class_level})
			st.success("Account created. Sign in to continue.")
		except ApiError as error:
			st.error(error.message)


if st.session_state.get("user"):
	st.title(f"Welcome back, {st.session_state.user['full_name'].split()[0]}")
	st.write("Choose a page from the sidebar to review progress, take an exam, or manage questions.")
	st.info("Start with Dashboard for progress, or Exam to create a practice session.")
else:
	st.title("Capstone Learning")
	st.write("A focused workspace for curriculum-grounded practice and feedback.")
	sign_in, create_account = st.tabs(["Sign in", "Create account"])
	with sign_in:
		login()
	with create_account:
		register()
