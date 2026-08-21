# Capstone API Design

## 1. Purpose and Scope

This document defines the REST API for the AI-powered personalized learning and examination system for CBSE Class 10 Physics and Mathematics. The API is implemented with FastAPI, Pydantic, SQLAlchemy, PostgreSQL, FAISS, LangChain, and LangGraph.

The MVP supports:

- Student and teacher registration and JWT authentication
- Curriculum browsing for the configured subjects, chapters, and topics
- RAG-grounded generation and validation of MCQ and numerical questions
- Student practice-exam generation, attempt submission, scoring, and explanations
- Topic-level performance and weak-topic analysis
- Teacher access to generated questions and a validated question bank

The following are designed as post-MVP extensions and are not required by the initial runbook: teacher approval checkpoints, exam assignment, AI grading for written answers, learning-coach recommendations, badges, and advanced class analytics.

## 2. API Conventions

### 2.1 Base URLs and versioning

- Local API base URL: `http://localhost:8000`
- Versioned application base path: `/api/v1`
- Health check: `GET /health`
- OpenAPI documentation: `/docs`
- ReDoc documentation: `/redoc`

All feature endpoints use `/api/v1`. The health endpoint is intentionally unversioned so deployment checks remain stable across API versions. A future breaking contract is introduced under `/api/v2`; existing versions remain supported during a documented deprecation period.

### 2.2 Transport and headers

- JSON request and response bodies use `Content-Type: application/json`.
- Protected endpoints require `Authorization: Bearer <access_token>`.
- Timestamps are UTC ISO 8601 strings, for example `2026-08-21T10:30:00Z`.
- IDs are UUID strings in the public API.
- Clients should send `Accept: application/json`.

### 2.3 Standard response envelope

Successful single-resource responses use:

```json
{
  "data": {},
  "meta": null
}
```

Collection responses use:

```json
{
  "data": [],
  "meta": {
    "page": 1,
    "page_size": 20,
    "total": 42,
    "has_next": true
  }
}
```

The `data` property contains the resource or list. `meta` is `null` for non-paginated single-resource responses.

### 2.4 Pagination and filtering

Paginated collection endpoints accept:

- `page`: positive integer, default `1`
- `page_size`: integer from `1` to `100`, default `20`

Filters are passed as query parameters. Unknown filter values return `400 Bad Request`; invalid UUIDs or numeric values return `422 Unprocessable Entity`.

### 2.5 Enumerations

| Field | Values |
|---|---|
| `role` | `student`, `teacher` |
| `question_type` | `mcq`, `numerical` for MVP; `short_answer`, `long_answer`, `competency` reserved |
| `difficulty` | `easy`, `medium`, `hard` |
| `question_status` | `generated`, `validated`, `rejected` |
| `attempt_status` | `in_progress`, `submitted` |
| `bloom_level` | `remember`, `understand`, `apply`, `analyze` |

The API rejects reserved question types until their corresponding evaluation behavior is implemented.

## 3. Authentication and Authorization

### 3.1 Authentication model

The API uses short-lived JWT access tokens signed by a server-side secret. Passwords are hashed with Argon2 or bcrypt and are never returned. The LLM provider key and database credentials remain server-side and are never included in API responses.

The MVP does not require refresh tokens. A client logs in again after access-token expiry.

### 3.2 Role rules

- `student`: may manage their own attempts, answers, progress, and practice exams.
- `teacher`: may generate questions, list questions, inspect validation results, and use validated questions when creating exams.
- A student cannot read another student's attempt, answers, or progress.
- Teacher-only routes return `403 Forbidden` for students.
- Resource ownership is checked in the service layer, not only in the frontend.

### 3.3 Authentication endpoints

#### `POST /api/v1/auth/register`

Creates a user and role profile.

Authentication: none.

Request:

```json
{
  "email": "student@example.com",
  "password": "StrongPassword123!",
  "full_name": "Asha Sharma",
  "role": "student",
  "class_level": 10
}
```

Rules:

- Email is normalized to lowercase and must be unique.
- Password must be at least 8 characters.
- `class_level` is required for students and must be `10` for the MVP.
- Teacher registration may be restricted to an approved invite or local seed process.

Response: `201 Created` with `UserResponse` (without password).

#### `POST /api/v1/auth/login`

Authenticates a user.

Authentication: none.

Request:

```json
{
  "email": "student@example.com",
  "password": "StrongPassword123!"
}
```

Response: `200 OK`.

```json
{
  "data": {
    "access_token": "<jwt>",
    "token_type": "bearer",
    "expires_in": 3600,
    "user": {
      "id": "uuid",
      "email": "student@example.com",
      "full_name": "Asha Sharma",
      "role": "student"
    }
  },
  "meta": null
}
```

Invalid credentials return `401` with error code `AUTH_INVALID_CREDENTIALS`.

#### `POST /api/v1/auth/logout`

Client-side token disposal endpoint. The MVP does not maintain a token blacklist.

Authentication: bearer token required.

Response: `204 No Content`.

#### `GET /api/v1/auth/me`

Returns the authenticated user and role profile.

Authentication: bearer token required.

Response: `200 OK` with `UserResponse`.

## 4. Health and Curriculum APIs

### `GET /health`

Returns service liveness.

Response: `200 OK`.

```json
{"status": "ok"}
```

A database connectivity failure returns `503 Service Unavailable` with code `SERVICE_UNAVAILABLE`.

### `GET /api/v1/curriculum/subjects`

Lists subjects enabled for Class 10. Authentication: bearer token required.

Response: paginated `SubjectResponse` collection. The MVP seed data contains `Physics` and `Mathematics`.

### `GET /api/v1/curriculum/subjects/{subject_id}/chapters`

Lists chapters for a subject. Authentication: bearer token required.

Response: paginated `ChapterResponse` collection.

### `GET /api/v1/curriculum/chapters/{chapter_id}/topics`

Lists topics for a chapter. Authentication: bearer token required.

Response: paginated `TopicResponse` collection.

A subject/chapter/topic relationship mismatch returns `404` with code `CURRICULUM_NOT_FOUND` rather than exposing unrelated records.

## 5. Pydantic Schemas

### 5.1 User schemas

```python
class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    role: Literal["student", "teacher"]
    class_level: int | None
    created_at: datetime

class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"]
    expires_in: int
    user: UserResponse
```

### 5.2 Question schemas

```python
class QuestionOption(BaseModel):
    key: str  # A, B, C, or D
    text: str

class QuestionResponse(BaseModel):
    id: UUID
    subject_id: UUID
    chapter_id: UUID
    topic_id: UUID
    class_level: int
    question_type: Literal["mcq", "numerical"]
    difficulty: Literal["easy", "medium", "hard"]
    bloom_level: Literal["remember", "understand", "apply", "analyze"] | None
    marks: PositiveInt
    question_text: str
    options: list[QuestionOption] | None
    expected_answer: str
    explanation: str
    learning_objective: str
    source_references: list[SourceReference]
    status: Literal["generated", "validated", "rejected"]
    created_by: UUID
    created_at: datetime
```

`correct_answer` is never returned by student exam or attempt endpoints. It is available only to the scoring service and teacher-authorized question-detail responses where appropriate.

### 5.3 Exam schemas

```python
class ExamGenerationRequest(BaseModel):
    subject_id: UUID
    chapter_id: UUID | None = None
    topic_id: UUID | None = None
    difficulty: Literal["easy", "medium", "hard"]
    question_types: list[Literal["mcq", "numerical"]]
    question_count: int = Field(ge=1, le=50)
    time_limit_minutes: int = Field(ge=1, le=180)
    title: str | None = Field(default=None, max_length=200)

class ExamQuestionResponse(BaseModel):
    id: UUID
    sequence_no: PositiveInt
    question: QuestionForAttemptResponse

class ExamResponse(BaseModel):
    id: UUID
    title: str
    subject_id: UUID
    chapter_id: UUID | None
    topic_id: UUID | None
    question_count: int
    time_limit_minutes: int
    questions: list[ExamQuestionResponse]
    created_by: UUID
    created_at: datetime
```

`QuestionForAttemptResponse` contains question text, options, type, difficulty, marks, and topic metadata, but no correct answer or answer key.

### 5.4 Attempt schemas

```python
class AnswerSubmission(BaseModel):
    question_id: UUID
    answer: str = Field(min_length=1, max_length=4000)

class AttemptSubmissionRequest(BaseModel):
    answers: list[AnswerSubmission]

class StudentAnswerResult(BaseModel):
    question_id: UUID
    submitted_answer: str | None
    is_correct: bool
    score_awarded: Decimal
    max_score: PositiveInt
    correct_answer: str
    explanation: str

class AttemptResultResponse(BaseModel):
    id: UUID
    exam_id: UUID
    student_id: UUID
    status: Literal["submitted"]
    score: Decimal
    max_score: PositiveInt
    percentage: Decimal
    submitted_at: datetime
    answers: list[StudentAnswerResult]
    weak_topics: list[TopicPerformanceResponse]
```

### 5.5 Generation and analytics schemas

```python
class QuestionGenerationRequest(BaseModel):
    subject_id: UUID
    chapter_id: UUID
    topic_id: UUID | None = None
    difficulty: Literal["easy", "medium", "hard"]
    question_type: Literal["mcq", "numerical"]
    marks: PositiveInt
    number_of_questions: int = Field(ge=1, le=50)
    bloom_level: Literal["remember", "understand", "apply", "analyze"] | None = None

class ValidationSummary(BaseModel):
    question_id: UUID
    status: Literal["validated", "rejected"]
    curriculum_relevance: bool
    answer_correctness: bool
    difficulty_match: bool
    type_match: bool
    duplicate_check: bool
    learning_objective_alignment: bool
    failure_reasons: list[str]

class TopicPerformanceResponse(BaseModel):
    topic_id: UUID
    topic_name: str
    attempts: int
    correct_answers: int
    score_percentage: Decimal
    status: Literal["strong", "good", "needs_practice"]
    last_updated: datetime
```

## 6. Question APIs

### `POST /api/v1/questions/generate`

Generates and validates a question set through the LangGraph MVP flow:

`retrieve_context → generate_questions → validate_questions → save`.

Authentication: teacher role required.

Request: `QuestionGenerationRequest`.

Response: `201 Created`.

```json
{
  "data": {
    "questions": ["QuestionResponse"],
    "validation": ["ValidationSummary"]
  },
  "meta": {"requested": 2, "validated": 2, "rejected": 0}
}
```

Only validated questions may be selected for exams. Failed validation is persisted with `status: rejected`, its reasons, and the workflow run ID for diagnosis. The endpoint returns `503` with `AI_PROVIDER_UNAVAILABLE` if generation cannot complete; it does not save a partially generated exam.

### `GET /api/v1/questions`

Lists questions visible to the caller.

Authentication: bearer token required.

Supported filters:

- `subject_id`, `chapter_id`, `topic_id`
- `question_type`, `difficulty`, `status`
- `page`, `page_size`

Students receive only validated questions that are used through an exam. Teachers may list generated, validated, and rejected questions they created, and validated question-bank items.

Response: `200 OK`, paginated `QuestionResponse` collection.

### `GET /api/v1/questions/{question_id}`

Returns one question and its source and validation metadata.

Authentication: bearer token required. Students may access only validated questions exposed through one of their exams.

Responses: `200`, `404 QUESTION_NOT_FOUND`, or `403 FORBIDDEN`.

### `GET /api/v1/questions/{question_id}/validation`

Returns validator checks and failure reasons.

Authentication: teacher role required.

Response: `200 OK` with `ValidationSummary`.

### `POST /api/v1/questions/{question_id}/revalidate`

Re-runs the validator against the stored question and current curriculum index.

Authentication: teacher role required. Only `generated` or `rejected` questions may be revalidated.

Response: `200 OK` with updated `QuestionResponse` and `ValidationSummary`.

Teacher approval endpoints are reserved for the post-MVP checkpoint. When implemented, they should add an explicit `approved` lifecycle state rather than treating `validated` as teacher approval.

## 7. Exam APIs

### `POST /api/v1/exams/generate`

Creates a student practice exam from validated questions matching the request. If the question bank does not contain enough matching items, the API invokes the generation and validation workflow before creating the exam.

Authentication: student or teacher.

- For a student, `created_by` is the authenticated student and the exam is private.
- For a teacher, the endpoint creates a teacher-owned exam from validated questions.

Request: `ExamGenerationRequest`.

Validation:

- `chapter_id` and `topic_id` must belong to `subject_id`.
- `question_types` must be non-empty and contain no duplicates.
- At least one validated question must be available or successfully generated for every requested slot.
- The requested count must not exceed `50`.

Response: `201 Created` with `ExamResponse`. Questions are ordered by `sequence_no`.

### `GET /api/v1/exams/{exam_id}`

Returns an exam and its questions.

Authentication: owner, assigned student, or teacher who created the exam. The response is always answer-key safe for students.

Response: `200 OK` with `ExamResponse`.

### `GET /api/v1/exams`

Lists exams visible to the caller.

Authentication: bearer token required.

Filters: `subject_id`, `created_by`, `page`, `page_size`.

Response: `200 OK`, paginated exam summaries.

### `POST /api/v1/exams/{exam_id}/attempts`

Starts an attempt for the authenticated student.

Authentication: student role required.

A student may have one active attempt for an exam. Repeating the request returns the existing active attempt with `200 OK`.

Response: `201 Created` for a new attempt.

```json
{
  "data": {
    "id": "uuid",
    "exam_id": "uuid",
    "status": "in_progress",
    "started_at": "2026-08-21T10:30:00Z"
  },
  "meta": null
}
```

### `GET /api/v1/attempts/{attempt_id}`

Returns the authenticated student's in-progress attempt and its questions, or a completed result after submission.

Authentication: attempt owner or teacher.

Students do not receive answer keys until the attempt is submitted.

### `POST /api/v1/attempts/{attempt_id}/submit`

Submits answers and evaluates the attempt atomically.

Authentication: attempt owner, student role required.

Request: `AttemptSubmissionRequest`.

Rules:

- The attempt must be `in_progress`.
- Every answer question must belong to the exam.
- Duplicate `question_id` values are rejected.
- Missing questions are recorded as unanswered and receive zero marks.
- Submission after the configured time limit returns `409 ATTEMPT_EXPIRED`.
- A repeated submission returns the existing result with `200 OK` and does not double-count performance.

Scoring:

- MCQ: exact match against the answer key.
- Numerical: normalized numeric comparison within ±5% of the expected value. The expected answer must include a parseable numeric value and compatible unit where applicable.
- Score is the sum of marks awarded; percentage is `score / max_score * 100`, rounded to two decimal places.

Response: `201 Created` for the first submission, `200 OK` for an idempotent repeat, with `AttemptResultResponse`.

## 8. Student Progress and Analytics APIs

### `GET /api/v1/students/me/progress`

Returns topic-level performance for the authenticated student.

Authentication: student role required.

Query filters: `subject_id`, `chapter_id`, `topic_id`.

Response: `200 OK`, paginated `TopicPerformanceResponse` collection.

Status thresholds for the MVP:

- `strong`: percentage >= 80
- `good`: percentage >= 60 and < 80
- `needs_practice`: percentage < 60

### `GET /api/v1/students/me/weak-topics`

Returns topics with `needs_practice` status, ordered by lowest score and then oldest update.

Authentication: student role required.

Response: `200 OK`, paginated topic-performance collection.

### `GET /api/v1/students/me/attempts`

Lists the authenticated student's submitted and in-progress attempts.

Authentication: student role required.

Filters: `exam_id`, `status`, `from_date`, `to_date`, `page`, `page_size`.

Response: `200 OK`, paginated attempt summaries.

### `GET /api/v1/teachers/me/dashboard`

Returns teacher-visible summary counts for generated, validated, and rejected questions and exams created by the teacher.

Authentication: teacher role required.

The MVP does not expose aggregate performance across all students unless the teacher has an explicit relationship to those students. Assignment and class analytics are post-MVP.

## 9. Post-MVP Extension Contracts

These routes are intentionally excluded from the MVP implementation gate but define stable extension points:

- `POST /api/v1/teacher/exams` creates an exam from approved questions.
- `POST /api/v1/teacher/exams/{exam_id}/assignments` assigns an exam to one or more students.
- `GET /api/v1/teacher/students/{student_id}/performance` returns authorized student analytics.
- `POST /api/v1/students/me/practice-recommendations` invokes the Learning Coach Agent.
- `GET /api/v1/students/me/badges` returns points and badge progress.
- `POST /api/v1/questions/{question_id}/approve` and `POST /api/v1/questions/{question_id}/reject` implement the teacher approval checkpoint.

These endpoints must reuse the existing schemas and authorization dependencies and must not expose answer keys to students.

## 10. Error Handling

All errors use one consistent body:

```json
{
  "error": {
    "code": "QUESTION_NOT_FOUND",
    "message": "Question was not found.",
    "details": {"question_id": "uuid"},
    "request_id": "uuid"
  }
}
```

`message` is safe for display; `details` contains structured, non-sensitive diagnostics; `request_id` is included in logs for troubleshooting.

| HTTP status | Error codes | Use |
|---:|---|---|
| 400 | `INVALID_FILTER`, `INVALID_WORKFLOW_INPUT` | Valid shape but invalid business input |
| 401 | `AUTH_REQUIRED`, `AUTH_INVALID_TOKEN`, `AUTH_INVALID_CREDENTIALS` | Missing or invalid authentication |
| 403 | `FORBIDDEN`, `RESOURCE_NOT_OWNED` | Authenticated but unauthorized |
| 404 | `USER_NOT_FOUND`, `CURRICULUM_NOT_FOUND`, `QUESTION_NOT_FOUND`, `EXAM_NOT_FOUND`, `ATTEMPT_NOT_FOUND` | Resource is absent or not visible |
| 409 | `EMAIL_ALREADY_EXISTS`, `ATTEMPT_ALREADY_SUBMITTED`, `ATTEMPT_EXPIRED`, `INVALID_STATUS_TRANSITION` | State or uniqueness conflict |
| 422 | `VALIDATION_ERROR` | Pydantic validation failure |
| 429 | `RATE_LIMITED` | Request or AI-provider rate limit |
| 500 | `INTERNAL_ERROR` | Unexpected server failure |
| 503 | `AI_PROVIDER_UNAVAILABLE`, `VECTOR_STORE_UNAVAILABLE`, `DATABASE_UNAVAILABLE` | Required dependency unavailable |

FastAPI validation errors are normalized into the same envelope. Stack traces, prompts, API keys, database details, and raw LLM output are never returned.

## 11. Persistence and Consistency Rules

- PostgreSQL is the source of truth for users, curriculum metadata, questions, exams, attempts, answers, and topic performance.
- FAISS stores retrieval vectors and is rebuildable from curated curriculum documents.
- An exam stores a stable `ExamQuestion` snapshot relationship so later question edits cannot change a submitted exam.
- Attempt submission, answer persistence, score calculation, and topic-performance update occur in one database transaction.
- A failed transaction leaves the attempt `in_progress` and does not partially update analytics.
- All created and updated timestamps are stored in UTC.
- Repository methods enforce foreign keys and ownership checks.

## 12. OpenAPI and Implementation Structure

FastAPI should organize routes by router and apply shared dependencies:

```text
app/
├── api/
│   ├── endpoints/
│   │   ├── auth.py
│   │   ├── curriculum.py
│   │   ├── questions.py
│   │   ├── exams.py
│   │   └── analytics.py
│   ├── dependencies/
│   │   ├── auth.py
│   │   └── database.py
│   └── schemas/
├── services/
│   ├── auth_service.py
│   ├── question_service.py
│   ├── exam_service.py
│   └── analytics_service.py
├── agents/
├── graph/
├── rag/
└── main.py
```

Each router declares response models and status codes so FastAPI generates an accurate OpenAPI contract. Pydantic schemas are separate from SQLAlchemy models. Services own business rules; route handlers translate HTTP requests into service calls and do not contain scoring or authorization logic.

## 13. API Acceptance Checklist

- [ ] `GET /health` returns `200` and `{"status":"ok"}`.
- [ ] Registration rejects duplicate emails and never returns password data.
- [ ] Login returns a bearer JWT and invalid credentials return `401`.
- [ ] Student and teacher route dependencies enforce role and ownership checks.
- [ ] Curriculum endpoints expose only seeded Class 10 Physics and Mathematics data.
- [ ] Question generation uses RAG context and LangGraph generation/validation states.
- [ ] Failed validation is stored as `rejected`; passing validation is stored as `validated`.
- [ ] Student exam responses contain no answer keys before submission.
- [ ] MCQ scoring uses exact matching.
- [ ] Numerical scoring uses ±5% tolerance.
- [ ] Missing answers receive zero and do not cause a partial result.
- [ ] Repeated attempt submission is idempotent.
- [ ] Submission updates topic performance exactly once.
- [ ] All errors use the documented error envelope and request ID.
- [ ] OpenAPI documentation is available at `/docs`.
- [ ] Unit tests mock LLM calls; integration tests use the isolated `capstone_test` PostgreSQL database.

## 14. Traceability

| API area | Requirements covered |
|---|---|
| Authentication and role dependencies | NFR-MH-01, NFR-MH-02 |
| Curriculum endpoints and metadata filters | FR-MH-01, FR-CH-01 |
| Question generation, validation, and source references | FR-MH-02, FR-MH-09, FR-MH-10, FR-MH-12, NFR-MH-03 |
| Exam creation and question types | FR-MH-01, FR-MH-02, FR-MH-03, FR-MH-13 |
| Attempt submission and results | FR-MH-04, FR-MH-11 |
| Progress and weak-topic analytics | FR-MH-05, FR-MH-06, FR-SH-02 |
| Teacher question access and dashboard | FR-MH-07, FR-MH-08, FR-SH-05 |
| Post-MVP extension routes | FR-SH-01, FR-SH-03, FR-SH-04, FR-CH-02, FR-CH-03 |
| Pagination, persistence, transactions, and error handling | NFR-SH-01, NFR-SH-03, NFR-MH-04, NFR-CH-01 |
