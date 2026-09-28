from datetime import date, timedelta

import streamlit as st

from components.api import ApiError, get_chapters_for_subject, get_student_analytics, get_subjects, require_auth
from components.dashboard import (
    apply_dashboard_styles,
    render_attempt_trend,
    render_chapter_heatmap,
    render_header,
    render_kpis,
    render_section,
    render_subject_performance,
    render_topic_matrix,
)
if require_auth("student"):
    try:
        apply_dashboard_styles()
        student_name = st.session_state.get("user", {}).get("full_name")
        render_header(student_name.split()[0] if student_name else None)

        subjects = get_subjects()
        subject_options = {"All subjects": None} | {item["name"]: item["id"] for item in subjects}
        subject_columns = st.columns([1.4, 1.4, 1])
        selected_subject = subject_columns[0].selectbox("Subject", list(subject_options), key="dashboard_subject")
        subject_id = subject_options[selected_subject]

        chapter_options = {"All chapters": None}
        if subject_id:
            chapters = get_chapters_for_subject(str(subject_id))
            chapter_options |= {item["name"]: item["id"] for item in chapters}
        selected_chapter = subject_columns[1].selectbox(
            "Chapter", list(chapter_options), key=f"dashboard_chapter_{subject_id or 'all'}"
        )

        periods = {"All time": None, "Last 30 days": 30, "Last 90 days": 90, "This year": "year"}
        selected_period = subject_columns[2].selectbox("Period", list(periods), key="dashboard_period")
        today = date.today()
        period_days = periods[selected_period]
        if period_days == "year":
            from_date = date(today.year, 1, 1)
        elif period_days:
            from_date = today - timedelta(days=period_days - 1)
        else:
            from_date = None

        params = {"to_date": today.isoformat()} if period_days else {}
        if from_date:
            params["from_date"] = from_date.isoformat()
        if subject_id:
            params["subject_id"] = str(subject_id)
        chapter_id = chapter_options[selected_chapter]
        if chapter_id:
            params["chapter_id"] = str(chapter_id)

        analytics = get_student_analytics(params).get("data", {})
        summary = analytics.get("summary", {})
        attempts = analytics.get("attempts_detail", []) or []
        render_kpis(summary, attempts)
        subject_rows = analytics.get("subjects", [])
        chapter_rows = analytics.get("chapters", [])
        topic_rows = analytics.get("topics", [])

        if not attempts:
            st.info("Complete an exam to see your analytics.")
        else:
            render_section("Progress over attempts", "Your latest score is highlighted; hover for exam details.")
            render_attempt_trend(attempts)

            render_section("Subject performance", "Compare average scores across subjects.")
            render_subject_performance(subject_rows)

            render_section("Chapter performance", "Color and score indicate current performance level.")
            render_chapter_heatmap(chapter_rows)

            render_section("Topic performance", "Grouped by chapter, with strongest topics first.")
            render_topic_matrix(topic_rows)

            with st.expander("Exam history"):
                st.dataframe(
                    [
                        {
                            "Exam": str(attempt.get("exam_title") or "Exam"),
                            "Submitted": str(attempt.get("submitted_at") or "")[:19].replace("T", " "),
                            "Subject": ", ".join(attempt.get("subjects") or []),
                            "Chapter": ", ".join(attempt.get("chapters") or []),
                            "Score": f"{attempt.get('score', 0)} / {attempt.get('max_score', 0)}",
                            "Percentage": f"{float(attempt.get('score_percentage') or 0):.1f}%",
                        }
                        for attempt in sorted(
                            attempts,
                            key=lambda row: str(row.get("submitted_at") or ""),
                            reverse=True,
                        )
                    ],
                    use_container_width=True,
                    hide_index=True,
                )
    except ApiError as error:
        st.error(error.message)
