import streamlit as st

from components.api import ApiError, get, require_auth
from components.sidebar import render


render()
st.title("Question bank")
if require_auth("teacher"):
	try:
		dashboard = get("/api/v1/teachers/me/dashboard")["data"]
		counts = dashboard["questions"]
		first, second, third = st.columns(3)
		first.metric("Validated", counts["validated"])
		second.metric("Generated", counts["generated"])
		third.metric("Rejected", counts["rejected"])
		questions = get("/api/v1/questions", params={"page_size": 100}).get("data", [])
		st.subheader("Your questions and validated bank")
		for question in questions:
			with st.expander(f"{question['question_type'].upper()} · {question['difficulty']} · {question['question_text'][:90]}"):
				st.write(question["question_text"])
				st.caption(f"Status: {question['status']} · Marks: {question['marks']}")
				st.write(question["explanation"])
	except ApiError as error:
		st.error(error.message)
