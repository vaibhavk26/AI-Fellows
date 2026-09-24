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
st.title("Generate questions")
if require_auth("teacher"):
    try:
        subjects = get_subjects()
        subject_map = options_for(subjects)
        if not subject_map:
            st.warning("No curriculum has been ingested yet.")
        else:
            subject_names = list(subject_map)
            if "generator_subject" not in st.session_state or st.session_state.generator_subject not in subject_map:
                st.session_state.generator_subject = subject_names[0]
            subject_name = st.selectbox("Subject", subject_names, index=subject_names.index(st.session_state.generator_subject), key="generator_subject")
            if st.session_state.generator_subject != subject_name:
                st.session_state.generator_subject = subject_name
                st.session_state.generator_chapter = None
                st.session_state.generator_topic = None
            subject_id = subject_map[subject_name]["id"]
            chapters_key = f"generator_chapters_{subject_id}"
            if chapters_key not in st.session_state or st.session_state.get(chapters_key) is None:
                st.session_state[chapters_key] = _start_background_load(f"_chapters_future_{subject_id}", _load_chapters_for_subject, str(subject_id))
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
                if "generator_chapter" not in st.session_state or st.session_state.generator_chapter not in chapter_map:
                    st.session_state.generator_chapter = chapter_names[0]
                chapter_name = st.selectbox("Chapter", chapter_names, index=chapter_names.index(st.session_state.generator_chapter), key="generator_chapter")
                if st.session_state.generator_chapter != chapter_name:
                    st.session_state.generator_chapter = chapter_name
                    st.session_state.generator_topic = None
                chapter_id = chapter_map[chapter_name]["id"]
                topics_key = f"generator_topics_{chapter_id}"
                if topics_key not in st.session_state or st.session_state.get(topics_key) is None:
                    st.session_state[topics_key] = _start_background_load(f"_topics_future_{chapter_id}", _load_topics_for_chapter, str(chapter_id))
                topic_future = st.session_state[topics_key]
                topics = _background_result(topic_future, "Loading topics...")
                topic_map = {"All topics": None} | options_for(topics)
                topic_names = list(topic_map)
                if "generator_topic" not in st.session_state or st.session_state.generator_topic not in topic_map:
                    st.session_state.generator_topic = topic_names[0]
                topic_name = st.selectbox("Topic", topic_names, index=topic_names.index(st.session_state.generator_topic), key="generator_topic")

            with st.form("generation"):
                question_type = st.selectbox("Question type", ["mcq", "numerical"])
                difficulty = st.selectbox("Difficulty", ["easy", "medium", "hard"])
                marks = st.number_input("Marks", min_value=1, max_value=10, value=1)
                number = st.slider("Questions", 1, 10, 5)
                bloom = st.selectbox("Learning level", ["remember", "understand", "apply", "analyze"])
                submitted = st.form_submit_button("Generate", type="primary", use_container_width=True)
            if submitted:
                if chapter_name is None:
                    st.warning("Select a valid chapter before generating questions.")
                else:
                    payload = {
                        "subject_id": subject_map[subject_name]["id"],
                        "chapter_id": chapter_map[chapter_name]["id"],
                        "topic_id": topic_map[topic_name]["id"] if topic_map[topic_name] else None,
                        "difficulty": difficulty,
                        "question_type": question_type,
                        "marks": marks,
                        "number_of_questions": number,
                        "bloom_level": bloom,
                    }
                    result = post("/api/v1/questions/generate", json=payload)
                    st.success(f"Generated {result['meta']['validated']} validated question(s).")
                    for question in result["data"]["questions"]:
                        st.write(question["question_text"])
                        st.caption(f"{question['status']} · {question['difficulty']} · {question['marks']} mark(s)")
    except ApiError as error:
        if error.status_code == 429:
            st.warning(
                "The question generator is busy right now (AI provider rate limit). "
                "Please wait about a minute and click Generate again, or try fewer questions at a time."
            )
        else:
            st.error(error.message)
