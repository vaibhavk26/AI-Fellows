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
    get_topics_for_chapter,
    options_for,
    post,
    require_auth,
)


def _teacher_only() -> bool:
    return require_auth("teacher")


def _open_teacher_page(render_page, title: str) -> None:
    if st.button("Go to page", key=f"teacher_hub_{title}", use_container_width=True):
        st.switch_page(st.Page(render_page, title=title))


def render_hub() -> None:
    st.title("Teacher Hub")
    st.caption("Your workspace for student progress, assessments, and learning content.")
    if not _teacher_only():
        return

    destinations = [
        ("📊", "Teacher Analytics", "Review question quality and assessment outcomes.", render_analytics, "Analytics"),
        ("👥", "Student Roster", "Manage the students connected to your classes.", render_roster, "Roster"),
        ("📝", "Assessments", "Create assessments and assign them to your students.", render_assessments, "Assessments"),
        ("📚", "Question Bank", "Browse, filter, and review generated questions.", render_question_bank, "Question Bank"),
    ]
    for start in (0, 2):
        left, right = st.columns(2, gap="medium")
        for column, destination in zip((left, right), destinations[start:start + 2]):
            icon, title, description, render_page, route_title = destination
            with column:
                with st.container(border=True):
                    st.markdown(f"### {icon}  {title}")
                    st.caption(description)
                    _open_teacher_page(render_page, route_title)


def render_analytics() -> None:
    st.title("Teacher Analytics")
    st.caption("A read-only overview of question quality and assessment progress.")
    if not _teacher_only():
        return
    try:
        dashboard = get_teacher_dashboard()
        questions = dashboard["questions"]
        st.subheader("Question bank")
        validated, generated, rejected = st.columns(3)
        validated.metric("Validated", questions["validated"])
        generated.metric("Generated", questions["generated"])
        rejected.metric("Rejected", questions["rejected"])

        assignments = dashboard["assignments"]
        st.subheader("Assessment analytics")
        assigned, started, completed, average = st.columns(4)
        assigned.metric("Assigned", assignments["total"])
        started.metric("Started", assignments["started"])
        completed.metric("Completed", assignments["completed"])
        average_score = assignments["average_score_percentage"]
        average.metric("Average score", f"{float(average_score):.1f}%" if average_score is not None else "N/A")

        st.subheader("Exam records")
        records = dashboard["exam_performance"]
        if records:
            st.dataframe(
                [{
                    "Exam": item["title"],
                    "Assigned": item["assigned"],
                    "Started": item["started"],
                    "Completed": item["completed"],
                    "Average score": (
                        f"{float(item['average_score_percentage']):.1f}%"
                        if item["average_score_percentage"] is not None else "N/A"
                    ),
                } for item in records],
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("Exam records will appear here after you assign an assessment.")
    except ApiError as error:
        st.error(error.message)


def render_roster() -> None:
    st.title("Student Roster")
    st.caption("Add registered students and find them quickly in your roster.")
    if not _teacher_only():
        return

    notice = st.session_state.pop("teacher_roster_notice", None)
    if notice:
        st.toast(notice, icon="✅")

    st.subheader("Add student")
    with st.form("add_roster_student"):
        email = st.text_input("Student email", placeholder="student@example.com")
        add_student = st.form_submit_button("Add student", type="primary")
    if add_student:
        try:
            student = add_teacher_student(email)
            st.session_state.teacher_roster_notice = f"Added {student['full_name']} to your roster."
            st.rerun()
        except ApiError as error:
            st.error(error.message)

    st.divider()
    st.subheader("Student list")
    try:
        students = get_teacher_students()
        search = st.text_input("Search students", placeholder="Search by name or email", key="teacher_roster_search")
        needle = search.strip().casefold()
        visible_students = [
            student for student in students
            if not needle or needle in student["full_name"].casefold() or needle in student["email"].casefold()
        ]
        if visible_students:
            st.dataframe(
                [{"Student": student["full_name"], "Email": student["email"]} for student in visible_students],
                use_container_width=True,
                hide_index=True,
            )
            st.caption(f"Showing {len(visible_students)} of {len(students)} students")
        elif students:
            st.info("No students match that search.")
        else:
            st.info("Your roster is empty. Add a registered student above to get started.")
    except ApiError as error:
        st.error(error.message)


def _show_create_assessment() -> None:
    if "teacher_assessment_notice" in st.session_state:
        st.success(st.session_state.teacher_assessment_notice)
        st.button(
            "Proceed to Assign Assessment",
            type="primary",
            key="proceed_to_assignment",
            on_click=lambda: st.session_state.update(teacher_assessment_tab="Assign Assessment"),
        )

    subjects = get_subjects()
    subject_map = options_for(subjects)
    if not subject_map:
        st.info("No curriculum is available for assessment creation.")
        return

    subject_name = st.selectbox("Subject", list(subject_map), key="teacher_exam_subject")
    chapters = get_chapters_for_subject(subject_map[subject_name]["id"])
    chapter_map = {"All chapters": None} | options_for(chapters)
    chapter_name = st.selectbox(
        "Chapter", list(chapter_map), key=f"teacher_exam_chapter_{subject_map[subject_name]['id']}"
    )
    with st.form("create_teacher_exam"):
        exam_title = st.text_input("Exam title", value="Class assessment")
        difficulty = st.selectbox("Difficulty", ["easy", "medium", "hard"], key="teacher_exam_difficulty")
        question_type = st.selectbox("Question type", ["MCQ", "Numerical", "Both"])
        question_count = st.number_input("Number of questions", min_value=1, max_value=20, value=5)
        duration = st.number_input("Time limit (minutes)", min_value=1, max_value=180, value=30)
        create_exam = st.form_submit_button("Create assessment", type="primary")

    if create_exam:
        question_types = {"MCQ": ["mcq"], "Numerical": ["numerical"], "Both": ["mcq", "numerical"]}[question_type]
        payload = {
            "title": exam_title,
            "subject_id": subject_map[subject_name]["id"],
            "chapter_id": chapter_map[chapter_name]["id"] if chapter_map[chapter_name] else None,
            "difficulty": difficulty,
            "question_types": question_types,
            "question_count": question_count,
            "time_limit_minutes": duration,
        }
        try:
            with st.spinner("Creating assessment..."):
                result = post("/api/v1/exams/generate", json=payload)["data"]
            st.session_state.teacher_assessment_notice = f"Assessment ‘{result['title']}’ created successfully."
            st.session_state.teacher_created_exam_id = result["id"]
            st.rerun()
        except ApiError as error:
            st.error(error.message)


def _show_assign_assessment() -> None:
    exams = get_teacher_exams()
    students = get_teacher_students()
    if not exams:
        st.info("Create an assessment before assigning it.")
        return
    if not students:
        st.info("Add students to your roster before assigning assessments.")
        return

    exam_labels = {f"{exam['title']} · {str(exam['id'])[:8]}": exam for exam in exams}
    exam_names = list(exam_labels)
    default_exam_id = st.session_state.get("teacher_created_exam_id")
    selected_exam_index = next(
        (index for index, name in enumerate(exam_names) if exam_labels[name]["id"] == default_exam_id),
        0,
    )
    student_names = {student["id"]: f"{student['full_name']} · {student['email']}" for student in students}
    with st.form("assign_exam"):
        selected_exam_name = st.selectbox("Assessment", exam_names, index=selected_exam_index)
        selected_students = st.multiselect("Students", list(student_names), format_func=student_names.get)
        assign_exam = st.form_submit_button("Assign assessment", type="primary")
    if assign_exam:
        if not selected_students:
            st.error("Select at least one student.")
            return
        selected_exam = exam_labels[selected_exam_name]
        try:
            result = post(
                f"/api/v1/exams/{selected_exam['id']}/assignments",
                json={"student_ids": selected_students},
            )
            st.toast(f"Assessment assigned to {len(result['data'])} student(s).", icon="✅")
        except ApiError as error:
            st.error(error.message)


def render_assessments() -> None:
    st.title("Assessments")
    st.caption("Create an assessment, then assign it to students in your roster.")
    if not _teacher_only():
        return

    create_tab, assign_tab = st.tabs(
        ["Create Assessment", "Assign Assessment"],
        key="teacher_assessment_tab",
        on_change="rerun",
    )
    try:
        if create_tab.open:
            with create_tab:
                _show_create_assessment()
        if assign_tab.open:
            with assign_tab:
                _show_assign_assessment()
    except ApiError as error:
        st.error(error.message)


def _filter_questions(
    questions: list[dict],
    *,
    subject_id: str | None = None,
    chapter_id: str | None = None,
    topic_id: str | None = None,
    difficulty: str = "All difficulties",
    question_type: str = "All types",
    status: str = "All statuses",
) -> list[dict]:
    return [
        question for question in questions
        if (subject_id is None or question["subject_id"] == subject_id)
        and (chapter_id is None or question["chapter_id"] == chapter_id)
        and (topic_id is None or question.get("topic_id") == topic_id)
        and (difficulty == "All difficulties" or question["difficulty"] == difficulty)
        and (question_type == "All types" or question["question_type"] == question_type)
        and (status == "All statuses" or question["status"] == status)
    ]


def render_question_bank() -> None:
    st.title("Question Bank")
    st.caption("Filter generated questions and open a card to review its answer and learning objective.")
    if not _teacher_only():
        return
    try:
        questions = get_teacher_questions(st.session_state.get("access_token", ""))
        subjects = get_subjects()
        subject_map = options_for(subjects)

        filters = st.columns(3)
        subject_options = {"All subjects": None} | {name: item["id"] for name, item in subject_map.items()}
        subject_name = filters[0].selectbox("Subject", list(subject_options), key="question_filter_subject")
        subject_id = subject_options[subject_name]
        chapters = get_chapters_for_subject(subject_id) if subject_id else []
        chapter_options = {"All chapters": None} | {item["name"]: item["id"] for item in chapters}
        chapter_name = filters[1].selectbox("Chapter", list(chapter_options), key="question_filter_chapter")
        chapter_id = chapter_options[chapter_name]
        topics = get_topics_for_chapter(chapter_id) if chapter_id else []
        topic_options = {"All topics": None} | {item["name"]: item["id"] for item in topics}
        topic_name = filters[2].selectbox("Topic", list(topic_options), key="question_filter_topic")
        topic_id = topic_options[topic_name]

        filter_row = st.columns(3)
        difficulty = filter_row[0].selectbox("Difficulty", ["All difficulties", "easy", "medium", "hard"])
        question_type = filter_row[1].selectbox("Question type", ["All types", "mcq", "numerical"])
        status = filter_row[2].selectbox("Status", ["All statuses", "validated", "generated", "rejected"])

        filtered = _filter_questions(
            questions,
            subject_id=subject_id,
            chapter_id=chapter_id,
            topic_id=topic_id,
            difficulty=difficulty,
            question_type=question_type,
            status=status,
        )
        st.caption(f"{len(filtered)} questions match these filters")
        page_size = 10
        pages = max(1, (len(filtered) + page_size - 1) // page_size)
        page_key = "question_bank_page_number"
        if st.session_state.get(page_key, 1) > pages:
            st.session_state[page_key] = 1
        if len(filtered) > page_size:
            current_page = st.number_input("Page", min_value=1, max_value=pages, step=1, key=page_key)
        else:
            current_page = 1
        page_questions = filtered[(current_page - 1) * page_size:current_page * page_size]
        if not page_questions:
            st.info("No questions match these filters.")
            return

        subject_names = {item["id"]: item["name"] for item in subjects}
        chapter_names = {item["id"]: item["name"] for item in chapters}
        topic_names = {item["id"]: item["name"] for item in topics}
        for question in page_questions:
            header = f"{question['question_type'].upper()} · {question['difficulty'].title()} · {question['status'].title()}"
            with st.expander(header + f" — {question['question_text'][:100]}"):
                st.markdown(f"**{question['question_text']}**")
                options = question.get("options") or []
                if options:
                    for option in options:
                        st.write(f"{option['key']}. {option['text']}")
                st.write(f"**Expected answer:** {question['expected_answer']}")
                st.write(question["explanation"])
                st.caption(f"Learning objective: {question['learning_objective']}")
                st.caption(
                    f"{subject_names.get(question['subject_id'], 'Subject')} · "
                    f"{chapter_names.get(question['chapter_id'], 'Chapter')} · "
                    f"{topic_names.get(question.get('topic_id'), 'All topics')} · {question['marks']} marks"
                )
    except ApiError as error:
        st.error(error.message)
