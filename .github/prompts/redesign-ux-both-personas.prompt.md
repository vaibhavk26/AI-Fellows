# ExamIQ Streamlit UX Review and Redesign Prompt

You are a senior product designer and frontend engineer specializing in education products and Streamlit applications.

Review and improve the existing **ExamIQ Student and Teacher experiences** in this repository. The demo deadline is **03 October 2026**, so keep the solution practical to implement in Streamlit. Aim for the polish and interaction clarity of a well-designed React application while retaining Streamlit as the frontend framework.

## Non-negotiable constraints

- Use Streamlit only. Do not introduce React, another frontend framework, a separate frontend server, or a build pipeline.
- Preserve the existing GitHub Dark theme, palette, spacing, and typography. Treat `capstone/.streamlit/config.toml` as the theme source of truth. In particular, retain the existing background, panel, text, and blue accent colors.
- Do not modify backend logic, database operations, API endpoints, request/response shapes, or API calls.
- Preserve all existing Student and Teacher functionality and persona restrictions.
- Do not break the exam lifecycle: assigned exam start/resume, practice exam generation, active attempt state, saved answers, timer, previous/next navigation, submit confirmation, submission, and result review must continue to work as they do now.
- Keep existing session-state keys and widget keys used by exam flows unless a change is essential; if one must change, preserve the existing state and behavior through a safe migration.
- Do not replace working flows with mock data or static visual-only controls. Do not remove functionality to shorten a page.

## Review the current implementation first

Inspect the current page files, shared components, navigation, theme, and relevant tests before editing. The main UI is under `capstone/frontend/`:

- Student: `pages/0_Student.py`, `pages/1_Dashboard.py`, `pages/2_Exam.py`, `pages/3_Results.py`, and `components/student_pages.py` / `components/dashboard.py`.
- Teacher: `pages/4_Teacher.py`, `pages/5_Generate.py`, `components/teacher_pages.py`, and `components/navigation.py`.
- Shared app shell: `Home.py`, `components/sidebar.py`, and `.streamlit/config.toml`.

Keep the current persona-aware navigation architecture. The Student Hub and Teacher Hub already exist; refine their clarity and visual hierarchy instead of rebuilding the information architecture without a concrete reason.

Before implementing, summarize the main UX issues you find and the proposed UI-only changes. Then make the changes in the existing Streamlit app.

## Design direction

Create a cohesive, modern learning workspace with clear hierarchy, calm density, and predictable interactions:

- Use Streamlit-native primitives first: `st.container`, columns, forms, tabs, expanders, metrics, progress, and dialogs where they fit the existing workflow.
- Use small, focused CSS enhancements for polish: consistent spacing, borders, card surfaces, responsive stacking, and clear focus/hover states. Scope CSS with stable app-specific classes or containers. Do not depend on fragile Streamlit-generated class names or broad selectors that restyle unrelated controls.
- Preserve theme tokens and typography. Use the existing blue for primary actions and focus; use status colors sparingly and keep contrast legible against the dark backgrounds.
- Establish consistent page headers, section titles, helper text, card padding, button hierarchy, empty states, loading states, and error placement across both personas.
- Keep layouts responsive at narrower browser widths. Avoid fixed widths and layouts that require horizontal scrolling.
- Prefer concise labels and helpful, contextual descriptions. Give each screen one clear primary action and visually distinguish secondary actions.
- Make the app feel polished through alignment, information hierarchy, and interaction feedback rather than excessive decoration or animations.
- Keep accessibility in view: meaningful labels, readable contrast, visible focus, and do not communicate correctness or status by color alone.

## Student experience

### Student Hub

- Make the next actions immediately understandable: review progress, continue or start an exam, and review results.
- Keep the existing routes and destinations. Use compact, consistent cards with a short description and clear action.
- If showing summary information, use only information already available without adding API calls.

### Dashboard

- Improve scanability of the existing KPIs, filters, trend, subject/chapter/topic performance, and exam history.
- Group filters as one compact control area and make the selected scope obvious.
- Establish a useful top-to-bottom hierarchy so the most actionable summary appears first and detailed breakdowns remain easy to find.
- Reduce the feeling of an endless report with sensible grouping or progressive disclosure, without hiding important information or changing analytics behavior.
- Preserve current loading, no-attempt, and empty-filter states.

### Exam

- Clearly distinguish exam setup from an active attempt and assigned exams from practice setup.
- Make the active question, answer control, time remaining, current position, and primary navigation easy to scan.
- Keep Previous, Next, and Submit behavior intact. Keep the timer visible and working during reruns.
- Preserve the submit confirmation and unanswered-question warning. Keep answers intact as the student moves between questions and while the attempt is active.
- Improve the assigned exam list and practice setup hierarchy while retaining their existing controls and request behavior.
- Preserve clear feedback for loading curriculum, missing curriculum, and API errors.

### Results

- Make attempt selection, score summary, topic performance, and question review hierarchy clear.
- Keep the selected attempt and all answer explanations available. Make correct answers, submitted answers, and incorrect responses understandable in text as well as visually.
- Preserve empty and loading/error states.

## Teacher experience

### Teacher Hub and navigation

- Keep the existing Teacher destinations and persona-aware sidebar routing.
- Make the hub cards consistent with the Student Hub and give each card a direct, understandable action.
- Keep account controls visually separate from page navigation and preserve sign-out behavior.

### Analytics, Roster, Assessments, Question Bank, and Generate Questions

- Improve consistency in headers, spacing, panels, form grouping, primary actions, success/error feedback, and empty states across all Teacher screens.
- Keep analytics read-only and preserve all current metrics and exam records.
- Keep roster add/search/list behavior and all existing API calls.
- Keep assessment creation and assignment workflows intact, including the transition from successful creation to assignment.
- Keep question-bank filters and question details intact; make the filter area and results easier to scan.
- Keep generation inputs, asynchronous progress, generated results, rejection details, and rate-limit feedback intact.
- Do not add optional destructive actions such as removing roster students unless they already exist and are wired to the backend.

## Implementation and handoff

- Make UI-only changes in the existing Streamlit frontend and shared styling/components where appropriate. Do not edit backend or database files.
- Reuse existing data and functions. Avoid adding API calls solely to populate decorative elements.
- Keep code modular and avoid duplicating style or layout logic across pages when a shared component is appropriate.
- Inspect the diff to confirm that backend files, API contracts, and database code were not changed.
- Run the existing relevant frontend/navigation checks if available, and report exactly which checks were run and their outcomes. Do not claim end-to-end validation unless it was actually performed.
- Finish with a concise summary of the UX improvements, files changed, checks run, and any remaining limitations.

The desired result is a polished, coherent Streamlit learning application that feels deliberate and professional, stays recognizably GitHub Dark, and preserves every existing Student and Teacher workflow.
