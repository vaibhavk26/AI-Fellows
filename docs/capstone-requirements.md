# Capstone Requirements Document

## 1. Introduction

This capstone project is an AI-powered personalized learning and examination system for CBSE Class 10 Physics and Mathematics students. The solution supports automated question generation, curriculum-grounded validation, student exam-taking, performance analysis, and targeted practice for weak learning areas. The system is designed to help students practice effectively, support teachers in question preparation and review, and demonstrate the value of Generative AI, RAG, and agentic workflows in a real educational context.

---

## 2. Requirements Index and Traceability

| Req ID | Priority | Section | Requirement Summary | Source / Trace |
|---|---|---|---|---|
| FR-MH-01 | Must Have | Functional | Student can choose subject, chapter, topic, difficulty, and test options | Student use case |
| FR-MH-02 | Must Have | Functional | System generates personalized exam questions | Student use case |
| FR-MH-03 | Must Have | Functional | Exam supports multiple question types and scoring | Question types |
| FR-MH-04 | Must Have | Functional | System evaluates answers and returns score + explanation | Student use case |
| FR-MH-05 | Must Have | Functional | System identifies weak chapters/topics and flags them | Personalization |
| FR-MH-06 | Must Have | Functional | System generates targeted practice based on weak areas | Learning coach |
| FR-MH-07 | Must Have | Functional | Teacher can create and review AI-generated questions | Teacher workflow |
| FR-MH-08 | Must Have | Functional | Teacher can approve questions into a reusable bank | Teacher workflow |
| FR-MH-09 | Must Have | Functional | System uses curriculum-grounded retrieval via RAG | RAG knowledge base |
| FR-MH-10 | Must Have | Functional | Validation agent checks correctness, relevance, and duplicate issues | Question validation |
| FR-MH-11 | Must Have | Functional | System stores questions, exams, attempts, performance, and progress data | Database model |
| FR-MH-12 | Must Have | Functional | System orchestrates generation, validation, approval, and personalization through a stateful agent workflow | LangGraph workflow design |
| FR-SH-01 | Should Have | Functional | Learning coach recommends question mix and difficulty | Learning coach |
| FR-SH-02 | Should Have | Functional | Student progress is tracked over time with topic performance | Student personalization |
| FR-SH-03 | Should Have | Functional | Basic gamification with points and badges | Gamification |
| FR-SH-04 | Should Have | Functional | Teacher can assign examinations to students | Teacher workflow |
| FR-SH-05 | Should Have | Functional | Dashboard displays student performance and outcomes | Teacher workflow |
| FR-CH-01 | Could Have | Functional | Additional chapters/subjects can be added beyond MVP scope | Academic scope |
| FR-CH-02 | Could Have | Functional | Advanced AI-assisted evaluation for long-form answers | Question types |
| FR-CH-03 | Could Have | Functional | More advanced coaching and streak-based personalization | Gamification |
| NFR-MH-01 | Must Have | Non-Functional | System should provide secure access for students and teachers | Architecture |
| NFR-MH-02 | Must Have | Non-Functional | Question generation and validation should be accurate and curriculum-aware | Problem statement |
| NFR-MH-03 | Must Have | Non-Functional | System should be maintainable and extensible for new chapters | Architecture |
| NFR-SH-01 | Should Have | Functional/Non-Functional | System should respond within acceptable user waiting times | Performance requirement |
| NFR-SH-02 | Should Have | Non-Functional | System should be easy to use with clear UI flows | UX requirement |
| NFR-SH-03 | Should Have | Non-Functional | Data should be persisted and recoverable | Database requirement |
| NFR-CH-01 | Could Have | Non-Functional | System supports multi-user concurrency and scaling for more students | Future scalability |

---

## 3. Functional Requirements

### 3.1 Student Learning Experience

#### FR-MH-01: Student Exam Configuration
- Priority: Must Have
- Requirement: The system shall allow a student to select subject, chapter, topic, difficulty, number of questions, question type, and time limit for a practice examination.
- Acceptance criteria:
  - Student can choose from Physics and Mathematics.
  - Student can select a chapter and topic from the configured curriculum scope.
  - Student can choose difficulty level and mixed or specific question types.
  - Student can set total question count and exam duration.

#### FR-MH-02: AI-Generated Personalized Examination
- Priority: Must Have
- Requirement: The system shall generate a personalized examination based on the selected academic parameters.
- Acceptance criteria:
  - A unique exam is created for the student request.
  - Questions are generated according to selected chapter/topic/difficulty.
  - Generated exam includes the configured number of questions.

#### FR-MH-03: Multi-Type Assessment Support
- Priority: Must Have
- Requirement: The system shall support at least five question types: MCQ, numerical, short answer, long answer, and competency/application-based questions.
- Acceptance criteria:
  - Each question has a recognized type.
  - MCQ questions are automatically scored.
  - Numerical questions are answer-checkable.
  - Short and long answer questions can be evaluated with AI-assisted comparison.

#### FR-MH-04: Exam Evaluation and Feedback
- Priority: Must Have
- Requirement: After a student completes an exam, the system shall evaluate responses, calculate the score, and provide answer explanations.
- Acceptance criteria:
  - Total score is computed and displayed.
  - Correct and incorrect answers are shown.
  - Explanations are provided for learning reinforcement.

#### FR-MH-05: Weak Area Detection
- Priority: Must Have
- Requirement: The system shall analyze exam performance at chapter/topic level and identify strong and weak areas.
- Acceptance criteria:
  - Performance is tracked per chapter and topic.
  - Weak topics are flagged for focused practice.
  - Strong topics are highlighted for student confidence and progression.

#### FR-MH-06: Targeted Practice Generation
- Priority: Must Have
- Requirement: The system shall generate targeted practice questions for topics where the student underperforms.
- Acceptance criteria:
  - A student can trigger “Improve My Weak Areas” flow.
  - New questions focus on the weakest topic(s).
  - Practice generation uses the same curriculum-grounded rules.

#### FR-SH-01: Learning Coach Recommendations
- Priority: Should Have
- Requirement: The system shall recommend an appropriate question mix, difficulty, and focus areas using a lightweight learning coach agent.
- Acceptance criteria:
  - Learning coach identifies strong and weak topics.
  - It recommends question count and difficulty.
  - Suggested question mix aligns with previous performance.

#### FR-SH-02: Topic-Level Progress Tracking
- Priority: Should Have
- Requirement: The system shall persist and display student performance trends by topic over time.
- Acceptance criteria:
  - Student can see performance history for each topic.
  - Progress can be compared across multiple attempts.

#### FR-SH-03: Basic Gamification
- Priority: Should Have
- Requirement: The system shall provide simple gamified motivation through points and badges.
- Acceptance criteria:
  - Students earn points for correct answers and completed tests.
  - Badges are awarded based on milestones and improvements.
  - Progress summaries show achievement status.

#### FR-CH-01: Extensible Curriculum Coverage
- Priority: Could Have
- Requirement: The architecture shall support extending the system to additional chapters and subjects beyond the initial MVP set.
- Acceptance criteria:
  - New subjects or chapters can be added without redesigning the core system.
  - Existing question-generation flow remains valid for new content.

---

### 3.2 Teacher and Admin Workflow

#### FR-MH-07: Teacher Question Generation
- Priority: Must Have
- Requirement: The teacher shall be able to select subject, chapter, topic, difficulty, question type, marks, and number of questions to generate a question set.
- Acceptance criteria:
  - Teacher can specify generation parameters.
  - Generated questions are created in a structured format.
  - Teacher can review generated items before publishing.

#### FR-MH-08: Question Review and Approval
- Priority: Must Have
- Requirement: The system shall allow teachers to review, reject, or approve AI-generated questions and add approved questions to the question bank.
- Acceptance criteria:
  - Question review workflow is available.
  - Each question can be accepted or rejected.
  - Approved questions are saved to reusable question bank data.

#### FR-SH-04: Examination Assignment
- Priority: Should Have
- Requirement: The teacher shall be able to create examinations and assign them to students.
- Acceptance criteria:
  - Teacher can build an exam from approved questions.
  - Teacher can assign the exam to one or more students.
  - Assignment records are stored for tracking.

#### FR-SH-05: Results Dashboard
- Priority: Should Have
- Requirement: The teacher shall be able to view student attempts and performance analytics.
- Acceptance criteria:
  - Teacher can access student scores and progress.
  - Results are grouped by exam and student.
  - Performance trends are visible for review.

---

### 3.3 AI Generation, Validation, and Knowledge Grounding

#### FR-MH-09: Curriculum-Grounded Retrieval
- Priority: Must Have
- Requirement: The system shall retrieve relevant curriculum material from a curated knowledge base before generating questions.
- Acceptance criteria:
  - Relevant syllabus and reference material are retrieved based on selected subject/chapter/topic.
  - Retrieved material is used as context for generation.
  - The process is grounded in approved educational material rather than free-form generation alone.

#### FR-MH-10: Question Validator Agent
- Priority: Must Have
- Requirement: The system shall validate each generated question for curriculum relevance, correctness, difficulty, type alignment, answer consistency, duplication, and learning objective match.
- Acceptance criteria:
  - Generated questions pass quality checks before approval.
  - Invalid questions are rejected or regenerated.
  - Validation results are logged for review and improvement.

#### FR-CH-02: Advanced Evaluation for Long-Form Answers
- Priority: Could Have
- Requirement: The system shall support deeper AI-assisted evaluation for long answer and competency-based responses.
- Acceptance criteria:
  - Long answer evaluation compares structure, concept coverage, and expected answer quality.
  - AI can provide constructive feedback beyond binary scoring.

#### FR-CH-03: Advanced Personalization Model
- Priority: Could Have
- Requirement: The system shall support increasingly adaptive recommendations using richer student learning patterns.
- Acceptance criteria:
  - Coaching has stronger personalization logic over time.
  - The system can adapt to topic-specific learning trends.

---

### 3.4 Data, Analytics, and System Backbone

#### FR-MH-11: Core Data Model
- Priority: Must Have
- Requirement: The system shall maintain structured data for users, subjects, chapters, topics, questions, exams, attempts, answers, performance, and badges.
- Acceptance criteria:
  - Database stores all necessary entities for student and teacher operations.
  - Question metadata is preserved for future filtering and analytics.
  - Performance histories can be queried and reported.

#### FR-MH-12: Agentic Workflow Orchestration
- Priority: Must Have
- Requirement: The system shall orchestrate the AI pipeline through a stateful workflow that coordinates generation, validation, teacher approval, and targeted practice recommendations.
- Acceptance criteria:
  - The workflow can move from question generation to validation and retry/regeneration when needed.
  - Teacher approval is represented as an explicit checkpoint before questions enter the official bank.
  - Personalized practice recommendations are triggered based on topic-level student performance.

#### FR-MH-13: API and Application Integration
- Priority: Must Have
- Requirement: The system shall expose backend APIs for authentication, exam generation, question management, student actions, teacher actions, and analytics.
- Acceptance criteria:
  - Frontend interacts with backend through structured APIs.
  - CRUD operations for questions, exams, users, and results are supported.
  - APIs are testable via Swagger/OpenAPI or equivalent.

---

## 4. Non-Functional Requirements

### 4.1 Security and Access

#### NFR-MH-01: Role-Based Access Control
- Priority: Must Have
- Requirement: The system shall provide secure access for students and teachers with appropriate role separation.
- Acceptance criteria:
  - Student and teacher roles are distinct.
  - Access to teacher functions is restricted to authorized users.
  - Authentication protects student and teacher data.

#### NFR-MH-02: Data Confidentiality
- Priority: Must Have
- Requirement: Student records, exam results, and learning analytics shall be protected from unauthorized access.
- Acceptance criteria:
  - Personal data is not exposed in public interfaces.
  - Sensitive functionality requires authenticated sessions.

---

### 4.2 Quality, Accuracy, and Trust

#### NFR-MH-03: Curriculum Accuracy
- Priority: Must Have
- Requirement: The system shall prioritize curriculum relevance and correctness over raw generation volume.
- Acceptance criteria:
  - Questions are aligned with CBSE Class 10 topics.
  - The validation flow rejects incorrect or off-syllabus questions.
  - The system reduces hallucination by grounding responses in retrieved educational material.

#### NFR-SH-01: Acceptable Response Time
- Priority: Should Have
- Requirement: The system shall generate and validate practice questions within acceptable user waiting times.
- Acceptance criteria:
  - Typical question-generation request completes within a reasonable interactive timeframe.
  - Users receive feedback indicating processing status when the request is longer-running.

#### NFR-SH-02: Usability and Clarity
- Priority: Should Have
- Requirement: The application shall provide simple, understandable workflows for both students and teachers.
- Acceptance criteria:
  - Interfaces are easy to navigate.
  - Student and teacher actions are clearly labeled.
  - Core flows require minimal training.

---

### 4.3 Reliability, Scalability, and Maintainability

#### NFR-SH-03: Data Persistence and Recovery
- Priority: Should Have
- Requirement: The system shall persist generated content, attempts, and progress data reliably.
- Acceptance criteria:
  - Data is stored in a relational database.
  - Important records are not lost during normal operations.
  - Recovery procedures can restore core application data.

#### NFR-MH-04: Maintainability and Extensibility
- Priority: Must Have
- Requirement: The system architecture shall be modular and extensible for future chapters, subjects, or additional AI workflows.
- Acceptance criteria:
  - Frontend, backend, database, and AI components are separated.
  - New curriculum areas can be added with minimal architectural changes.
  - Code is organized for straightforward iteration and enhancement.

#### NFR-CH-01: Scalability for Growth
- Priority: Could Have
- Requirement: The system should support increased user load and larger question sets as adoption grows.
- Acceptance criteria:
  - The app can handle more concurrent users without major redesign.
  - Database and AI pipelines can expand as more content is added.

---

## 5. Priority Summary

### Must Have
- Core student exam generation and evaluation flow
- Teacher review, approval, and question bank creation
- RAG-backed curriculum grounding and validation
- Basic performance tracking and weak-area personalization
- Structured persistence for questions, exams, attempts, and progress

### Should Have
- Learning coach recommendations
- Student motivation features such as points and badges
- Teacher assignment and performance dashboards
- Usability and responsiveness improvements

### Could Have
- Expanded subject and chapter coverage
- More advanced answer evaluation and coaching logic
- Greater scalability and richer personalization features

---

## 6. Assumptions and Constraints

- MVP scope is limited to CBSE Class 10 Physics and Mathematics.
- Initial curriculum coverage includes the recommended chapters listed in the proposal.
- The system uses AI and RAG to improve quality but should not rely solely on ungrounded generation.
- The design should remain modular so the MVP can evolve into a broader educational system.

---

## 7. Requirements Validation Note

The requirements in this document are derived from the project proposal and are intended to serve as a baseline for design, development, and evaluation. They should be reviewed with stakeholders during the planning phase and refined as the application evolves from MVP into a fuller learning platform.
