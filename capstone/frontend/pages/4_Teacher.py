import streamlit as st

from components.api import (
    ApiError,
    add_teacher_student,
    get_chapters_for_subject,
    get_subjects,
    get_teacher_dashboard,
    get_teacher_exams,
    get_teacher_questions,
    get_teacher_students,
    options_for,
    post,
    require_auth,
)
from components.sidebar import render


render()
st.title("Question bank")
if require_auth("teacher"):
    try:
        dashboard = get_teacher_dashboard()
        counts = dashboard["questions"]
        first, second, third = st.columns(3)
        first.metric("Validated", counts["validated"])
        second.metric("Generated", counts["generated"])
        third.metric("Rejected", counts["rejected"])

        st.subheader("Assessment analytics")
        assignment_counts = dashboard["assignments"]
        total, started, completed, average = st.columns(4)
        total.metric("Assigned", assignment_counts["total"])
        started.metric("Started", assignment_counts["started"])
        completed.metric("Completed", assignment_counts["completed"])
        average_score = assignment_counts["average_score_percentage"]
        average.metric("Average score", f"{float(average_score):.1f}%" if average_score is not None else "N/A")
        if dashboard["exam_performance"]:
            st.dataframe(
                [{
                    "Exam": item["title"],
                    "Assigned": item["assigned"],
                    "Started": item["started"],
                    "Completed": item["completed"],
                    "Average score": f"{float(item['average_score_percentage']):.1f}%" if item["average_score_percentage"] is not None else "N/A",
                } for item in dashboard["exam_performance"]],
                use_container_width=True,
                hide_index=True,
            )

        st.subheader("Student roster")
        with st.form("add_roster_student"):
            email = st.text_input("Registered student email")
            add_student = st.form_submit_button("Add student")
        if add_student:
            student = add_teacher_student(email)
            st.success(f"Added {student['full_name']} to your roster.")
            st.rerun()

        students = get_teacher_students()
        student_names = {student["id"]: f"{student['full_name']} · {student['email']}" for student in students}
        if students:
            st.dataframe([{"Student": value} for value in student_names.values()], use_container_width=True, hide_index=True)
        else:
            st.info("Add registered students to your roster before assigning exams.")

        st.subheader("Create assessment")
        subjects = get_subjects()
        subject_map = options_for(subjects)
        if subject_map:
            subject_name = st.selectbox("Subject", list(subject_map), key="teacher_exam_subject")
            chapters = get_chapters_for_subject(subject_map[subject_name]["id"])
            chapter_map = {"All chapters": None} | options_for(chapters)
            chapter_name = st.selectbox(
                "Chapter",
                list(chapter_map),
                key=f"teacher_exam_chapter_{subject_map[subject_name]['id']}",
            )
            with st.form("create_teacher_exam"):
                exam_title = st.text_input("Exam title", value="Class assessment")
                difficulty = st.selectbox("Difficulty", ["easy", "medium", "hard"], key="teacher_exam_difficulty")
                question_types = st.multiselect(
                    "Question types",
                    ["mcq", "numerical"],
                    default=["mcq"],
                    key="teacher_exam_types",
                )
                question_count = st.number_input("Questions", min_value=1, max_value=20, value=5, key="teacher_exam_count")
                duration = st.number_input("Time limit (minutes)", min_value=1, max_value=180, value=30, key="teacher_exam_duration")
                create_exam = st.form_submit_button("Create assessment", type="primary")
            if create_exam:
                if not question_types:
                    st.error("Select at least one question type.")
                else:
                    payload = {
                        "title": exam_title,
                        "subject_id": subject_map[subject_name]["id"],
                        "chapter_id": chapter_map[chapter_name]["id"] if chapter_map[chapter_name] else None,
                        "difficulty": difficulty,
                        "question_types": question_types,
                        "question_count": question_count,
                        "time_limit_minutes": duration,
                    }
                    with st.spinner("Creating assessment..."):
                        post("/api/v1/exams/generate", json=payload)
                    st.success("Assessment created.")
                    st.rerun()
        else:
            st.info("No curriculum is available for assessment creation.")

        st.subheader("Assign assessment")
        exams = get_teacher_exams()
        if exams and students:
            exam_labels = {f"{exam['title']} · {str(exam['id'])[:8]}": exam for exam in exams}
            with st.form("assign_exam"):
                selected_exam_name = st.selectbox("Assessment", list(exam_labels))
                selected_students = st.multiselect(
                    "Students",
                    list(student_names),
                    format_func=student_names.get,
                )
                assign = st.form_submit_button("Assign exam", type="primary")
            if assign:
                if not selected_students:
                    st.error("Select at least one student.")
                else:
                    selected_exam = exam_labels[selected_exam_name]
                    result = post(
                        f"/api/v1/exams/{selected_exam['id']}/assignments",
                        json={"student_ids": selected_students},
                    )
                    st.success(f"Assigned to {len(result['data'])} student(s).")
                    st.rerun()
        elif not exams:
            st.info("Create an assessment before assigning it.")

        questions = get_teacher_questions()
        st.subheader("Your questions and validated bank")
        for question in questions:
            with st.expander(f"{question['question_type'].upper()} · {question['difficulty']} · {question['question_text'][:90]}"):
                st.write(question["question_text"])
                st.caption(f"Status: {question['status']} · Marks: {question['marks']}")
                st.write(question["explanation"])
    except ApiError as error:
        st.error(error.message)
