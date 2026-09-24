import streamlit as st

from components.api import (
    ApiError,
    _start_background_load,
    get_subjects,
    _load_chapters_for_subject,
    _load_topics_for_chapter,
    _background_result,
    options_for,
    post,
    require_auth,
)
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
            subjects = get_subjects()
            subject_map = options_for(subjects)
            if not subject_map:
                st.warning("No curriculum has been ingested yet.")
            else:
                subject_names = list(subject_map)
                if "exam_subject" not in st.session_state or st.session_state.exam_subject not in subject_map:
                    st.session_state.exam_subject = subject_names[0]
                subject_name = st.selectbox("Subject", subject_names, index=subject_names.index(st.session_state.exam_subject), key="exam_subject")
                if st.session_state.exam_subject != subject_name:
                    st.session_state.exam_subject = subject_name
                    st.session_state.exam_chapter = None
                    st.session_state.exam_topic = None
                subject_id = subject_map[subject_name]["id"]
                chapters_key = f"exam_chapters_{subject_id}"
                if chapters_key not in st.session_state or st.session_state.get(chapters_key) is None:
                    st.session_state[chapters_key] = _start_background_load(f"_exam_chapters_future_{subject_id}", _load_chapters_for_subject, str(subject_id))
                chapter_future = st.session_state[chapters_key]
                chapters = _background_result(chapter_future, "Loading chapters...")
                chapter_map = options_for(chapters)
                if not chapter_map:
                    st.info("No chapters are available for the selected subject.")
                    chapter_name = None
                    topic_map = {"All topics": None}
                    topic_name = "All topics"
                else:
                    chapter_names = list(chapter_map)
                    if "exam_chapter" not in st.session_state or st.session_state.exam_chapter not in chapter_map:
                        st.session_state.exam_chapter = chapter_names[0]
                    chapter_name = st.selectbox("Chapter", chapter_names, index=chapter_names.index(st.session_state.exam_chapter), key="exam_chapter")
                    if st.session_state.exam_chapter != chapter_name:
                        st.session_state.exam_chapter = chapter_name
                        st.session_state.exam_topic = None
                    chapter_id = chapter_map[chapter_name]["id"]
                    topics_key = f"exam_topics_{chapter_id}"
                    if topics_key not in st.session_state or st.session_state.get(topics_key) is None:
                        st.session_state[topics_key] = _start_background_load(f"_exam_topics_future_{chapter_id}", _load_topics_for_chapter, str(chapter_id))
                    topic_future = st.session_state[topics_key]
                    topics = _background_result(topic_future, "Loading topics...")
                    topic_map = {"All topics": None} | options_for(topics)
                    topic_names = list(topic_map)
                    if "exam_topic" not in st.session_state or st.session_state.exam_topic not in topic_map:
                        st.session_state.exam_topic = topic_names[0]
                    topic_name = st.selectbox("Topic", topic_names, index=topic_names.index(st.session_state.exam_topic), key="exam_topic")
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
                        payload = {
                            "subject_id": subject_map[subject_name]["id"],
                            "chapter_id": chapter_map[chapter_name]["id"] if chapter_name else None,
                            "topic_id": topic_map[topic_name]["id"] if topic_map[topic_name] else None,
                            "difficulty": difficulty,
                            "question_types": question_types,
                            "question_count": count,
                            "time_limit_minutes": duration,
                        }
                        exam = post("/api/v1/exams/generate", json=payload)["data"]
                        started = post(f"/api/v1/exams/{exam['id']}/attempts")["data"]
                        st.session_state.active_exam = exam
                        st.session_state.active_attempt = started
                        st.rerun()
        except ApiError as error:
            st.error(error.message)
