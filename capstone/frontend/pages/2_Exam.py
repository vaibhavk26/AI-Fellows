from datetime import datetime, timezone

import streamlit as st

from components.api import (
    ApiError,
    _background_result,
    _load_chapters_for_subject,
    _load_topics_for_chapter,
    _start_background_load,
    get,
    get_student_assignments,
    get_student_attempts,
    get_subjects,
    options_for,
    post,
    require_auth,
)


def _parse_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


@st.fragment(run_every="1s")
def _render_timer(started_at: str, time_limit_minutes: int) -> None:
    started = _parse_datetime(started_at)
    remaining_seconds = max(
        0,
        time_limit_minutes * 60 - int((datetime.now(timezone.utc) - started).total_seconds()),
    )
    minutes, seconds = divmod(remaining_seconds, 60)
    st.metric("Time remaining", f"{minutes:02d}:{seconds:02d}")
    if remaining_seconds == 0:
        st.error("Time is up. Submit your answers to complete this attempt.")


@st.dialog("Submit this exam?")
def _confirm_submission() -> None:
    exam = st.session_state.get("active_exam")
    attempt = st.session_state.get("active_attempt")
    if not exam or not attempt:
        st.info("There is no active exam to submit.")
        return

    questions = exam.get("questions", [])
    answer_prefix = f"exam_answer_{attempt['id']}_"
    answered_count = sum(
        bool(str(st.session_state.get(answer_prefix + item["question"]["id"], "") or "").strip())
        for item in questions
    )
    unanswered = len(questions) - answered_count
    st.write(f"You have answered **{answered_count} of {len(questions)} questions**.")
    if unanswered:
        st.warning(f"{unanswered} unanswered question(s) will receive zero marks.")
    st.write("After submission, your answers cannot be changed.")
    confirm, cancel = st.columns(2)
    if confirm.button("Submit exam", type="primary", use_container_width=True):
        answers = []
        for item in questions:
            question_id = item["question"]["id"]
            answer = str(st.session_state.get(answer_prefix + question_id, "") or "").strip()
            if answer:
                answers.append({"question_id": question_id, "answer": answer})
        try:
            result = post(f"/api/v1/attempts/{attempt['id']}/submit", json={"answers": answers})["data"]
            get_student_attempts.clear()
            st.session_state.last_result = result
            st.session_state.exam_submission_notice = "Exam submitted. Open Results to review your feedback."
            for key in list(st.session_state):
                if key.startswith(answer_prefix):
                    del st.session_state[key]
            st.session_state.active_exam = None
            st.session_state.active_attempt = None
            st.session_state.pop("exam_question_index", None)
            st.rerun()
        except ApiError as error:
            st.error(error.message)
    if cancel.button("Keep working", use_container_width=True):
        st.rerun()


def _render_active_attempt(exam: dict, attempt: dict) -> None:
    questions = exam.get("questions", [])
    if not questions:
        st.warning("This exam has no questions.")
        return

    index_key = "exam_question_index"
    current_index = max(0, min(st.session_state.get(index_key, 0), len(questions) - 1))
    st.session_state[index_key] = current_index
    question = questions[current_index]["question"]
    answer_key = f"exam_answer_{attempt['id']}_{question['id']}"

    header_left, header_right = st.columns([3, 1])
    with header_left:
        st.title(exam["title"])
        st.caption(f"{len(questions)} questions · {exam['time_limit_minutes']} minutes")
    with header_right:
        started_at = attempt.get("started_at")
        if started_at:
            _render_timer(started_at, exam["time_limit_minutes"])
        else:
            st.metric("Time limit", f"{exam['time_limit_minutes']} min")

    st.progress((current_index + 1) / len(questions))
    st.caption(f"Question {current_index + 1} of {len(questions)}")
    with st.container(border=True):
        st.markdown(f"### {question['question_text']}")
        st.caption(f"{question['marks']} marks · {question['question_type'].title()}")
        if question["question_type"] == "mcq":
            choices = {
                option["key"]: f"{option['key']}. {option['text']}"
                for option in question.get("options") or []
            }
            st.radio(
                "Choose one answer",
                list(choices),
                format_func=choices.get,
                index=None,
                key=answer_key,
            )
        else:
            st.text_input("Your answer", key=answer_key, placeholder="Enter your answer")

    previous, spacer, next_question, submit = st.columns([1, 2, 1, 1])
    if previous.button("Previous", disabled=current_index == 0, use_container_width=True):
        st.session_state[index_key] = current_index - 1
        st.rerun()
    if next_question.button(
        "Next", disabled=current_index >= len(questions) - 1, type="primary", use_container_width=True
    ):
        st.session_state[index_key] = current_index + 1
        st.rerun()
    if submit.button("Submit", use_container_width=True):
        _confirm_submission()


def _render_exam_setup() -> None:
    notice = st.session_state.pop("exam_submission_notice", None)
    if notice:
        st.success(notice)

    assignments = get_student_assignments()
    if assignments:
        st.subheader("Assigned exams")
        for assignment in assignments:
            first, second = st.columns([3, 1])
            first.markdown(f"**{assignment['exam_title']}**")
            first.caption(
                f"{assignment['question_count']} questions · {assignment['time_limit_minutes']} minutes · "
                f"{assignment['status'].title()}"
            )
            if assignment["status"] == "completed":
                second.button(
                    "Completed", key=f"assigned_completed_{assignment['id']}", disabled=True,
                    use_container_width=True,
                )
            elif second.button(
                "Start" if assignment["status"] == "assigned" else "Resume",
                key=f"assigned_start_{assignment['id']}", type="primary", use_container_width=True,
            ):
                exam = get(f"/api/v1/exams/{assignment['exam_id']}")["data"]
                started = post(f"/api/v1/exams/{assignment['exam_id']}/attempts")["data"]
                st.session_state.active_exam = exam
                st.session_state.active_attempt = started
                st.session_state.exam_question_index = 0
                st.rerun()
        st.divider()

    subjects = get_subjects()
    subject_map = options_for(subjects)
    if not subject_map:
        st.warning("No curriculum has been ingested yet.")
        return

    st.subheader("Start a practice exam")
    subject_names = list(subject_map)
    if "exam_subject" not in st.session_state or st.session_state.exam_subject not in subject_map:
        st.session_state.exam_subject = subject_names[0]
    subject_name = st.selectbox(
        "Subject", subject_names, index=subject_names.index(st.session_state.exam_subject), key="exam_subject"
    )
    if st.session_state.exam_subject != subject_name:
        st.session_state.exam_subject = subject_name
        st.session_state.exam_chapter = None
        st.session_state.exam_topic = None
    subject_id = subject_map[subject_name]["id"]
    chapters_key = f"exam_chapters_{subject_id}"
    if chapters_key not in st.session_state or st.session_state.get(chapters_key) is None:
        st.session_state[chapters_key] = _start_background_load(
            f"_exam_chapters_future_{subject_id}", _load_chapters_for_subject, str(subject_id)
        )
    chapters = _background_result(st.session_state[chapters_key], "Loading chapters...")
    chapter_map = options_for(chapters)
    chapter_id = None
    topic_id = None
    if chapter_map:
        chapter_names = list(chapter_map)
        if st.session_state.get("exam_chapter") not in chapter_map:
            st.session_state.exam_chapter = chapter_names[0]
        chapter_name = st.selectbox(
            "Chapter", chapter_names, index=chapter_names.index(st.session_state.exam_chapter), key="exam_chapter"
        )
        if st.session_state.exam_chapter != chapter_name:
            st.session_state.exam_chapter = chapter_name
            st.session_state.exam_topic = None
        chapter_id = chapter_map[chapter_name]["id"]
        topics_key = f"exam_topics_{chapter_id}"
        if topics_key not in st.session_state or st.session_state.get(topics_key) is None:
            st.session_state[topics_key] = _start_background_load(
                f"_exam_topics_future_{chapter_id}", _load_topics_for_chapter, str(chapter_id)
            )
        topics = _background_result(st.session_state[topics_key], "Loading topics...")
        topic_map = {"All topics": None} | options_for(topics)
        topic_names = list(topic_map)
        if st.session_state.get("exam_topic") not in topic_map:
            st.session_state.exam_topic = topic_names[0]
        topic_name = st.selectbox(
            "Topic", topic_names, index=topic_names.index(st.session_state.exam_topic), key="exam_topic"
        )
        topic_id = topic_map[topic_name]["id"] if topic_map[topic_name] else None
    else:
        st.info("No chapters are available for the selected subject.")

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
                "chapter_id": chapter_id,
                "topic_id": topic_id,
                "difficulty": difficulty,
                "question_types": question_types,
                "question_count": count,
                "time_limit_minutes": duration,
            }
            exam = post("/api/v1/exams/generate", json=payload)["data"]
            started = post(f"/api/v1/exams/{exam['id']}/attempts")["data"]
            st.session_state.active_exam = exam
            st.session_state.active_attempt = started
            st.session_state.exam_question_index = 0
            st.rerun()


st.title("Exam")
if require_auth("student"):
    active_exam = st.session_state.get("active_exam")
    active_attempt = st.session_state.get("active_attempt")
    try:
        if active_exam and active_attempt and active_attempt.get("status") == "in_progress":
            _render_active_attempt(active_exam, active_attempt)
        else:
            _render_exam_setup()
    except ApiError as error:
        st.error(error.message)
