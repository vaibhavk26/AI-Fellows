from datetime import datetime

import streamlit as st

from components.api import ApiError, get_attempt_detail, get_student_attempts, require_auth
from components.sidebar import render


render()
st.title("Results")
if require_auth("student"):
    result = st.session_state.get("last_result")
    try:
        attempts = get_student_attempts()
        if attempts:
            labels = {}
            for index, item in enumerate(attempts, start=1):
                submitted_at = datetime.fromisoformat(str(item["submitted_at"]).replace("Z", "+00:00"))
                labels[str(item["id"])] = (
                    f"Attempt {index} · {submitted_at.astimezone():%Y-%m-%d %H:%M:%S} · {item['percentage']}%"
                )
            selected = st.selectbox("Attempt", list(labels), format_func=labels.get, key="result_attempt")
            result = get_attempt_detail(str(selected)) if selected else None
        if not result:
            st.info("Submit an exam to see detailed results here.")
        else:
            first, second = st.columns(2)
            first.metric("Score", f"{result['score']} / {result['max_score']}")
            second.metric("Percentage", f"{result['percentage']}%")
            st.subheader("Answer review")
            for index, answer in enumerate(result.get("answers", []), start=1):
                label = "Correct" if answer["is_correct"] else "Incorrect"
                with st.expander(f"{label} · Question {index}"):
                    st.markdown(f"**{answer['question_text']}**")
                    submitted_answer = answer["submitted_answer"] or "No answer"
                    options = answer.get("options") or []
                    if options:
                        for option in options:
                            key = str(option["key"])
                            choice = f"{key}. {option['text']}"
                            is_selected = key.casefold() == str(submitted_answer).casefold()
                            is_correct = key.casefold() == str(answer["correct_answer"]).casefold()
                            if is_correct and is_selected:
                                st.success(f"{choice} · Your answer, correct")
                            elif is_correct:
                                st.success(f"{choice} · Correct answer")
                            elif is_selected:
                                st.error(f"{choice} · Your answer, incorrect")
                            else:
                                st.write(choice)
                    elif answer["is_correct"]:
                        st.success(f"Your answer: {submitted_answer}")
                    else:
                        st.error(f"Your answer: {submitted_answer}")
                        st.success(f"Correct answer: {answer['correct_answer']}")
                    st.caption(answer["explanation"])
            if result.get("weak_topics"):
                st.subheader("Topics to revisit")
                for topic in result["weak_topics"]:
                    st.warning(f"{topic['topic_name']}: {topic['score_percentage']}%")
    except ApiError as error:
        st.error(error.message)
