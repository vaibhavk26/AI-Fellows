from datetime import datetime, timezone

import streamlit as st

from components.api import ApiError, get_attempt_detail, get_student_attempts, require_auth


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _format_duration(attempt: dict | None) -> str:
    if not attempt:
        return "N/A"
    started = _parse_datetime(attempt.get("started_at"))
    submitted = _parse_datetime(attempt.get("submitted_at"))
    if not started or not submitted:
        return "N/A"
    seconds = max(0, int((submitted - started).total_seconds()))
    minutes, seconds = divmod(seconds, 60)
    return f"{minutes}m {seconds:02d}s"


def _render_topic_breakdown(answers: list[dict]) -> None:
    topic_stats: dict[str, dict] = {}
    for answer in answers:
        topic_name = answer.get("topic_name")
        if not topic_name:
            continue
        stats = topic_stats.setdefault(topic_name, {"correct": 0, "total": 0})
        stats["total"] += 1
        stats["correct"] += bool(answer.get("is_correct"))
    if not topic_stats:
        st.info("Topic-level results are not available for this attempt.")
        return
    for topic_name, stats in topic_stats.items():
        accuracy = stats["correct"] / stats["total"]
        left, right = st.columns([3, 1])
        left.write(topic_name)
        right.caption(f"{stats['correct']}/{stats['total']} correct")
        st.progress(accuracy)


def _render_answer_review(answer: dict, index: int) -> None:
    is_correct = bool(answer.get("is_correct"))
    label = "Correct" if is_correct else "Review this answer"
    icon = "✅" if is_correct else "❌"
    with st.expander(f"{icon}  Question {index}: {label}"):
        st.markdown(f"**{answer['question_text']}**")
        submitted_answer = answer.get("submitted_answer") or "No answer"
        options = answer.get("options") or []
        if options:
            for option in options:
                key = str(option["key"])
                choice = f"{key}. {option['text']}"
                is_selected = key.casefold() == str(submitted_answer).casefold()
                is_answer_key = key.casefold() == str(answer["correct_answer"]).casefold()
                if is_answer_key and is_selected:
                    st.success(f"{choice} · Your answer")
                elif is_answer_key:
                    st.success(f"{choice} · Correct answer")
                elif is_selected:
                    st.error(f"{choice} · Your answer")
                else:
                    st.write(choice)
        elif is_correct:
            st.success(f"Your answer: {submitted_answer}")
        else:
            st.error(f"Your answer: {submitted_answer}")
            st.success(f"Correct answer: {answer['correct_answer']}")
        st.caption(answer.get("explanation") or "No explanation is available for this question.")


st.title("Results")
if require_auth("student"):
    try:
        access_token = st.session_state.get("access_token", "")
        attempts = get_student_attempts(access_token)
        result = st.session_state.get("last_result")
        selected_attempt = None
        if attempts:
            labels = {}
            for index, item in enumerate(attempts, start=1):
                submitted_at = _parse_datetime(item.get("submitted_at"))
                timestamp = submitted_at.astimezone().strftime("%Y-%m-%d %H:%M") if submitted_at else ""
                labels[str(item["id"])] = (
                    f"Attempt {index} · {timestamp} · {float(item.get('percentage') or 0):.1f}%"
                )
            selected_id = st.selectbox("Completed exam", list(labels), format_func=labels.get, key="result_attempt")
            selected_attempt = next((item for item in attempts if str(item["id"]) == selected_id), None)
            if not result or str(result.get("id")) != str(selected_id):
                result = get_attempt_detail(str(selected_id), access_token)

        if not result:
            st.info("Complete an exam to see your score, topic performance, and answer explanations here.")
        else:
            answers = result.get("answers", [])
            correct_count = sum(bool(answer.get("is_correct")) for answer in answers)
            accuracy = (correct_count / len(answers) * 100) if answers else 0
            first, second, third, fourth = st.columns(4)
            first.metric("Score", f"{result['score']} / {result['max_score']}")
            second.metric("Score percentage", f"{float(result['percentage']):.1f}%")
            third.metric("Accuracy", f"{accuracy:.1f}%", f"{correct_count} of {len(answers)} correct")
            fourth.metric("Time taken", _format_duration(selected_attempt))

            st.subheader("Topic performance")
            _render_topic_breakdown(answers)

            st.subheader("Question review")
            st.caption("Open a question to see your response, the correct answer, and its explanation.")
            for index, answer in enumerate(answers, start=1):
                _render_answer_review(answer, index)
    except ApiError as error:
        st.error(error.message)
