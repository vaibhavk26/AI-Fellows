import streamlit as st

from components.api import ApiError, get, require_auth
from components.sidebar import render


render()
st.title("Results")
if require_auth("student"):
	result = st.session_state.get("last_result")
	try:
		attempts = get("/api/v1/students/me/attempts", params={"status": "submitted", "page_size": 20}).get("data", [])
		if attempts:
			labels = {str(item["id"]): f"{item['submitted_at'][:10]} · {item['percentage']}%" for item in attempts}
			selected = st.selectbox("Attempt", list(labels), format_func=labels.get)
			result = get(f"/api/v1/attempts/{selected}")["data"]
		if not result:
			st.info("Submit an exam to see detailed results here.")
		else:
			first, second = st.columns(2)
			first.metric("Score", f"{result['score']} / {result['max_score']}")
			second.metric("Percentage", f"{result['percentage']}%")
			st.subheader("Answer review")
			for index, answer in enumerate(result.get("answers", []), start=1):
				label = "Correct" if answer["is_correct"] else "Review"
				with st.expander(f"{label} · Question {index}"):
					st.write(f"Your answer: {answer['submitted_answer'] or 'No answer'}")
					st.write(f"Correct answer: {answer['correct_answer']}")
					st.caption(answer["explanation"])
			if result.get("weak_topics"):
				st.subheader("Topics to revisit")
				for topic in result["weak_topics"]:
					st.warning(f"{topic['topic_name']}: {topic['score_percentage']}%")
	except ApiError as error:
		st.error(error.message)
