import streamlit as st

from components.api import ApiError, get_student_progress, get_weak_topics, require_auth
from components.sidebar import render


render()
st.title("Progress dashboard")
if require_auth("student"):
    try:
        progress = get_student_progress()
        weak = get_weak_topics()
        rows = progress.get("data", [])
        first, second, third = st.columns(3)
        first.metric("Topics practiced", len(rows))
        second.metric("Strong topics", sum(row["status"] == "strong" for row in rows))
        third.metric("Needs practice", len(weak.get("data", [])))
        st.subheader("Topic performance")
        if rows:
            st.dataframe(
                [{"Topic": row["topic_name"], "Score": f"{row['score_percentage']}%", "Attempts": row["attempts"], "Status": row["status"].replace("_", " ").title()} for row in rows],
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("Complete an exam to see topic performance here.")
        st.subheader("Weak topics")
        if weak.get("data"):
            for row in weak["data"]:
                st.warning(f"{row['topic_name']}: {row['score_percentage']}%")
        else:
            st.success("No weak topics yet. Keep practicing.")
    except ApiError as error:
        st.error(error.message)
