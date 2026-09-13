import streamlit as st

from components.api import ApiError, get, options_for, post, require_auth
from components.sidebar import render


render()
st.title("Practice exam")
if require_auth("student"):
	active = st.session_state.get("active_exam")
	attempt = st.session_state.get("active_attempt")
	if active and attempt and attempt.get("status") == "in_progress":
		st.caption(f"{active['title']} · {active['time_limit_minutes']} minutes")
		with st.form("exam_answers"):
			answers = []
			for index, item in enumerate(active["questions"], start=1):
				question = item["question"]
				st.markdown(f"**{index}. {question['question_text']}**  ·  {question['marks']} marks")
				if question["question_type"] == "mcq":
					choices = {option["key"]: f"{option['key']}. {option['text']}" for option in question.get("options") or []}
					answer = st.radio("Answer", list(choices), format_func=choices.get, key=f"answer_{question['id']}")
				else:
					answer = st.text_input("Answer", key=f"answer_{question['id']}")
				answers.append({"question_id": question["id"], "answer": answer})
			submitted = st.form_submit_button("Submit exam", type="primary", use_container_width=True)
		if submitted:
			try:
				result = post(f"/api/v1/attempts/{attempt['id']}/submit", json={"answers": answers})["data"]
				st.session_state.last_result = result
				st.session_state.active_exam = None
				st.session_state.active_attempt = None
				st.success("Exam submitted. Open Results to review your feedback.")
			except ApiError as error:
				st.error(error.message)
	else:
		try:
			subjects = get("/api/v1/curriculum/subjects", params={"page_size": 100}).get("data", [])
			subject_map = options_for(subjects)
			if not subject_map:
				st.warning("No curriculum has been ingested yet.")
			else:
				subject_name = st.selectbox("Subject", list(subject_map))
				chapters = get(f"/api/v1/curriculum/subjects/{subject_map[subject_name]['id']}/chapters", params={"page_size": 100}).get("data", [])
				chapter_map = options_for(chapters)
				chapter_name = st.selectbox("Chapter", list(chapter_map)) if chapter_map else None
				topics = get(f"/api/v1/curriculum/chapters/{chapter_map[chapter_name]['id']}/topics", params={"page_size": 100}).get("data", []) if chapter_name else []
				topic_map = {"All topics": None} | options_for(topics)
				topic_name = st.selectbox("Topic", list(topic_map))
				with st.form("exam_setup"):
					difficulty = st.selectbox("Difficulty", ["easy", "medium", "hard"])
					question_types = st.multiselect("Question types", ["mcq", "numerical"], default=["mcq"])
					count = st.number_input("Questions", min_value=1, max_value=20, value=1, step=1)
					duration = st.slider("Time limit (minutes)", 1, 60, 20)
					submitted = st.form_submit_button("Generate exam", type="primary", use_container_width=True)
				if submitted:
					if not question_types:
						st.error("Select at least one question type.")
					else:
						payload = {"subject_id": subject_map[subject_name]["id"], "chapter_id": chapter_map[chapter_name]["id"], "topic_id": topic_map[topic_name]["id"] if topic_map[topic_name] else None, "difficulty": difficulty, "question_types": question_types, "question_count": count, "time_limit_minutes": duration}
						exam = post("/api/v1/exams/generate", json=payload)["data"]
						started = post(f"/api/v1/exams/{exam['id']}/attempts")["data"]
						st.session_state.active_exam = exam
						st.session_state.active_attempt = started
						st.rerun()
		except ApiError as error:
			st.error(error.message)
