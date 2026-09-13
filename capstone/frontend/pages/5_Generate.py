import streamlit as st

from components.api import ApiError, get, options_for, post, require_auth
from components.sidebar import render


render()
st.title("Generate questions")
if require_auth("teacher"):
	try:
		subjects = get("/api/v1/curriculum/subjects", params={"page_size": 100}).get("data", [])
		subject_map = options_for(subjects)
		if not subject_map:
			st.warning("No curriculum has been ingested yet.")
		else:
			subject_name = st.selectbox("Subject", list(subject_map))
			chapters = get(f"/api/v1/curriculum/subjects/{subject_map[subject_name]['id']}/chapters", params={"page_size": 100}).get("data", [])
			chapter_map = options_for(chapters)
			chapter_name = st.selectbox("Chapter", list(chapter_map))
			topics = get(f"/api/v1/curriculum/chapters/{chapter_map[chapter_name]['id']}/topics", params={"page_size": 100}).get("data", [])
			topic_map = {"All topics": None} | options_for(topics)
			topic_name = st.selectbox("Topic", list(topic_map))
			with st.form("generation"):
				question_type = st.selectbox("Question type", ["mcq", "numerical"])
				difficulty = st.selectbox("Difficulty", ["easy", "medium", "hard"])
				marks = st.number_input("Marks", min_value=1, max_value=10, value=1)
				number = st.slider("Questions", 1, 20, 5)
				bloom = st.selectbox("Learning level", ["remember", "understand", "apply", "analyze"])
				submitted = st.form_submit_button("Generate", type="primary", use_container_width=True)
			if submitted:
				payload = {"subject_id": subject_map[subject_name]["id"], "chapter_id": chapter_map[chapter_name]["id"], "topic_id": topic_map[topic_name]["id"] if topic_map[topic_name] else None, "difficulty": difficulty, "question_type": question_type, "marks": marks, "number_of_questions": number, "bloom_level": bloom}
				result = post("/api/v1/questions/generate", json=payload)
				st.success(f"Generated {result['meta']['validated']} validated question(s).")
				for question in result["data"]["questions"]:
					st.write(question["question_text"])
					st.caption(f"{question['status']} · {question['difficulty']} · {question['marks']} mark(s)")
	except ApiError as error:
		st.error(error.message)
