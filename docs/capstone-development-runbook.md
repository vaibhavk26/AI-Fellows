# Capstone Development Runbook

This document is the execution guide for the MVP defined in [capstone-implementation-plan.md](capstone-implementation-plan.md).

Use it for setup steps, exact commands, validation gates, and the AI prompt sequence. It does not redefine scope or architecture; those decisions live in the implementation plan.

The authoritative design references for the project are:

- [capstone-api-design.md](capstone-api-design.md)
- [capstone-database-design.md](capstone-database-design.md)

These files are the source of truth for API contracts and database design. Do not create duplicate root-level copies of the same contract or schema documents during implementation.

## 0. Current Status

Last updated 2026-08-30.

Completed:

- [x] Prerequisites (Section 2) and PostgreSQL databases (Section 3) — 2026-08-25
- [x] Project scaffold (Section 4) — 2026-08-25
- [x] SQLAlchemy models for all MVP and extension tables in [capstone-database-design.md](capstone-database-design.md) section 6/22
- [x] Alembic initialized (`alembic/env.py`, `alembic/script.py.mako`, `alembic/versions/`) and initial migration `6f0e6720530e_initial_mvp_schema.py` generated and applied to both `capstone` and `capstone_test` (Section 9.1)
- [x] Seed data for Subjects/Chapters loaded into both `capstone` and `capstone_test` via `scripts/seed_reference_data.py` (Section 9.2) — 2026-08-28
- [x] **Section 10.1: Authentication Foundation** — Pydantic schemas, JWT utilities, and auth endpoints fully implemented and tested (10/10 integration tests passing) — 2026-08-29
  - [x] Pydantic schemas for auth request/response validation
  - [x] Password hashing (bcrypt) and JWT utilities in `app/core/security.py`
  - [x] Auth endpoints: register, login, logout, current-user in `app/api/endpoints/auth.py`
  - [x] AuthService business logic in `app/services/auth_service.py`
  - [x] Bearer token dependency in `app/api/dependencies/auth.py`
  - [x] Role-based access control (student/teacher) working
  - [x] **CRITICAL**: JWT tokens use `datetime.now(timezone.utc)` for timezone-safe token expiration across all developer timezones
  - [x] `/health` returns HTTP 200
- [x] All dependencies updated: added `email-validator==2.3.0` to requirements.txt and `JWT_SECRET_KEY` to .env.example
- [x] **Section 10.2 partial: Question retrieval, exams, attempts, scoring, and analytics** — 2026-08-30
   - [x] Authenticated question retrieval and role-aware visibility
   - [x] Validated-question exam generation, attempts, idempotent submission, and answer-key-safe responses
   - [x] Exact-match MCQ scoring, numerical ±5% scoring with unit matching, and transactional topic-performance updates
   - [x] Progress, weak-topic, attempt-history, and teacher dashboard endpoints
   - [x] Focused Section 10.2 unit/integration tests; run `./.venv/Scripts/python.exe -m pytest tests/ -v` from `capstone/` (15 passing)

Not yet done:

- [ ] LLM provider and model selection — `.env.example`/`SETUP.md` still carry placeholder values for LLM_PROVIDER and LLM_MODEL, so the Section 14 completion gate item is not yet satisfied
- [ ] Section 10.2 question generation — `POST /api/v1/questions/generate` intentionally returns `501 Not Implemented` until Section 10.3 steps 7-8 provide the RAG/LangGraph workflow

Next step: proceed with Implementation Sequence (Section 10), steps 7-8 — implement RAG ingestion and the LangGraph generation/validation workflow, then wire it into the existing question-generation endpoint.

## 1. Working Assumptions

This runbook assumes the following decisions from the implementation plan:

- PostgreSQL is the database for local, test, and production environments
- local development uses a Python virtual environment, not Docker
- backend runs on port 8000
- frontend runs on port 8501
- question types are limited to MCQ and Numerical
- question status values are generated, validated, and rejected
- teacher approval and long-answer grading are out of scope for the MVP

## 2. Prerequisites

Completed on 2026-08-25:

- [x] Python 3.11 or newer installed
- [x] PostgreSQL installed and running locally
- [x] psql available in PowerShell
- [x] Git and VS Code installed

Run:

```powershell
python --version
psql --version
git status
```

If psql is not recognized, add the PostgreSQL bin directory to PATH or use SQL Shell (psql).

For virtual environment creation, dependency installation, database setup, and starting the app, refer to the [capstone/SETUP.md](../capstone/SETUP.md) quick-start guide.

## 2.1 Dependency Baseline

Use the following dependency baseline for the MVP before implementation starts:

The installation commands are in the [capstone/SETUP.md](../capstone/SETUP.md) quick-start guide; this section defines the approved package versions.

```text
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0
langchain==0.1.0
langchain-openai==0.0.5
langgraph==0.0.15
langchain-community==0.0.10
faiss-cpu==1.7.4
sentence-transformers==2.2.2
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
alembic==1.13.0
pypdf==4.0.0
streamlit==1.28.1
python-jose==3.3.0
passlib==1.7.4
bcrypt==4.1.1
email-validator==2.3.0
pytest==7.4.3
pytest-asyncio==0.21.1
httpx==0.25.0
python-dotenv==1.0.0
requests==2.31.0
```

## 2.2 Git and Branch Hygiene

Use these branch names for the implementation team:

- dev-backend
- dev-frontend
- dev-ai
- dev-devops
- dev (integration branch)
- main (production)

Create the working branch before starting code for each area:

```powershell
git checkout -b dev-backend
```

## 2.3 Repository Hygiene

Add the following to .gitignore before committing any project code:

```gitignore
.env.local
.venv/
__pycache__/
*.pyc
.pytest_cache/
.DS_Store
```

## 3. Create PostgreSQL Databases

Completed on 2026-08-25.

Use a PostgreSQL admin account to create the required databases.

```sql
CREATE USER capstone_user WITH PASSWORD 'replace-local-password';
CREATE DATABASE capstone OWNER capstone_user;
CREATE DATABASE capstone_test OWNER capstone_user;
```

Verify both databases:

```powershell
psql -U capstone_user -d capstone -c "SELECT current_database();"
psql -U capstone_user -d capstone_test -c "SELECT current_database();"
```

## 4. Create the Project Scaffold

Completed on 2026-08-25.

From the repository root:

```powershell
New-Item -ItemType Directory -Force capstone
Set-Location capstone
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Create the project structure:

```text
capstone/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── core/
│   ├── api/
│   │   ├── endpoints/
│   │   ├── dependencies/
│   │   └── schemas/
│   ├── db/
│   │   ├── models/
│   │   └── session.py
│   ├── services/
│   ├── agents/
│   ├── graph/
│   └── rag/
├── frontend/
│   ├── streamlit_app.py
│   ├── pages/
│   └── components/
├── tests/
│   ├── unit/
│   └── integration/
├── data/curriculum/
├── scripts/
├── alembic/
├── requirements.txt
├── .env.example
├── .env.local
├── alembic.ini
├── pytest.ini
├── README.md
└── .gitignore
```

Add __init__.py files to Python packages as needed.

## 5. Authoritative Documentation

Use the following design documents as the authority for implementation contracts:

- [capstone-api-design.md](capstone-api-design.md): endpoint contracts, auth model, request/response shapes, status codes, error patterns, and pagination rules
- [capstone-database-design.md](capstone-database-design.md): entities, constraints, relationships, enumerations, and schema decisions

Optional project supporting docs may still live inside the capstone folder if they help onboarding or operations, but they must not duplicate or overwrite the authoritative API and schema design documents above.

## 6. Install Dependencies and Configure Env

Create requirements.txt based on the approved dependency list, then run:

For the complete local setup sequence, including virtual environment creation and activation, start with the [capstone/SETUP.md](../capstone/SETUP.md) quick-start guide.

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Create .env.local from .env.example and set the values:

```env
DATABASE_URL=postgresql+psycopg2://capstone_user:password@localhost:5432/capstone
TEST_DATABASE_URL=postgresql+psycopg2://capstone_user:password@localhost:5432/capstone_test
VECTOR_DB_TYPE=faiss
VECTOR_DB_PATH=./vectors
DEBUG=True
ENVIRONMENT=development
LLM_PROVIDER=openai-compatible
LLM_MODEL=replace-with-approved-model
OPENAI_API_KEY=replace-with-local-secret
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production
```

Do not commit .env.local or real credentials.

Use mocked LLM responses in unit tests. Unit tests must not require a live API key.

**Important for distributed teams**: The `JWT_SECRET_KEY` is automatically handled correctly across all timezones. The codebase uses `datetime.now(timezone.utc)` for all JWT token timestamp operations, ensuring developers in any timezone (UTC, IST, PST, etc.) can generate and validate tokens without any timezone-related configuration. No special timezone setup is needed.

## 7. Contract Gate Before Feature Work

Complete the following before building the application logic:

### API contract checks
- request and response shapes for every endpoint
- auth requirements per endpoint
- HTTP status codes
- standard error response format
- filters and pagination decisions
- numerical scoring tolerance of ±5%
- question lifecycle: generated -> validated or rejected

### Database contract checks
- primary and foreign keys
- required and nullable fields
- enum values for roles, question type, difficulty, and status
- relationship and cascade behavior
- unique constraints
- timestamp conventions
- subject/chapter/topic strategy for curriculum metadata

Only continue after API_DESIGN.md and DATABASE_SCHEMA.md are drafted and reviewed.

## 8. Bootstrapping and Health Validation

From the capstone/ directory, confirm that the existing Alembic setup is present:

```powershell
Test-Path .\alembic
Test-Path .\alembic.ini
```

Both commands should return `True`. Do not run `alembic init alembic`; Alembic is already initialized in this repository. That command is only needed when setting up Alembic in a brand-new project.

Start the API:

```powershell
uvicorn app.main:app --reload
```

In a second PowerShell terminal, from the `capstone/` directory, call the health endpoint:

```powershell
Invoke-RestMethod -Uri http://localhost:8000/health -Method Get
```

Expected response:

```text
status
------
ok
```

Open the Swagger docs at http://localhost:8000/docs.

The gate is complete only when:
- FastAPI starts successfully
- /health returns HTTP 200
- settings load from .env.local
- the app connects to the capstone database

## 9. Database Migration Sequence

### 9.1 Initial Migration

Completed on 2026-08-27: models implemented for every table in [capstone-database-design.md](capstone-database-design.md) section 6/22 (core MVP plus extension tables), and the initial migration `6f0e6720530e_initial_mvp_schema.py` was generated, reviewed (pgcrypto extension added manually; autogenerate does not detect it), and applied to both `capstone` and `capstone_test`. Seed data for Subjects/Chapters was intentionally excluded from this migration and is deferred to a later, separate migration or `scripts/ingest_curriculum.py`.

For teammates pulling these changes, the exact commands to apply the migration locally are in the [capstone/SETUP.md](../capstone/SETUP.md) "Database migrations" section — run this after every `git pull` that changes `alembic/versions/`, since applying a migration is a local, per-database action that git cannot distribute.

Summary of the sequence used for the initial migration (for reference when adding future migrations):

```powershell
alembic revision --autogenerate -m "<description>"
alembic upgrade head
$env:DATABASE_URL=$env:TEST_DATABASE_URL
alembic upgrade head
```

Restore the development DATABASE_URL after the test migration step.

Do not proceed until both databases are migrated successfully.

### 9.2 Seed Data for Subjects/Chapters

Completed on 2026-08-28: `scripts/seed_reference_data.py` inserts the exact Subjects and Chapters rows from [capstone-database-design.md](capstone-database-design.md) section 17 using the SQLAlchemy session (`app/db/session.py`), and is idempotent (queries for an existing row by its unique key before inserting, so re-running is safe). It intentionally excludes the extension badge seed values, which are post-MVP/gamification-only per section 17.

The exact commands to run it locally, against both `capstone` and `capstone_test`, are in the [capstone/SETUP.md](../capstone/SETUP.md) "Seed reference data" section — run this after migrations and before curriculum ingestion (`scripts/ingest_curriculum.py`), since Chapters foreign-key to Subjects and Topics foreign-key to Chapters. That same section also has the `psql`/SQLAlchemy commands to verify the row counts (2 subjects, 7 chapters) after seeding each database.

Do not proceed to curriculum ingestion until this seed step has been run and verified against both databases.

## 10. Implementation Sequence

Build in this order. Each step names the primary files to add or modify under `capstone/app/` (packages already scaffolded per Section 4) and its hard dependencies. Endpoint/response contracts are defined in [capstone-api-design.md](capstone-api-design.md); do not invent request/response shapes ad hoc. Steps are grouped below by area for scannability, but the numbering (1-12) is one continuous sequence and dependency references (e.g. "depends on step 4") refer to that single sequence, not the subheadings.

### 10.1 Authentication Foundation (backend lead)

1. **Pydantic schemas** — extend `app/api/schemas/base.py` and `app/api/schemas/auth.py`; add `question.py`, `exam.py`, `attempt.py`, `analytics.py`. Depends on: Section 9.1 models (complete).
2. **password hashing and JWT utilities** — add security helpers (e.g. `app/core/security.py`) for Argon2/bcrypt hashing and JWT encode/decode, per API design section 3.1. Depends on: step 1 for the payload/token schemas.
3. **register, login, current-user endpoints** — `app/api/endpoints/auth.py` + `app/services/auth_service.py` + a bearer-token dependency in `app/api/dependencies/auth.py` (currently a placeholder). Implements API design section 3.3. Depends on: steps 1-2.

### 10.2 Question, Exam, and Analytics API (backend lead)

4. **question generation and retrieval endpoints** — `app/api/endpoints/questions.py` + `app/services/question_service.py`. Split this step in two:
   - *Retrieval* (`GET /questions`, `GET /questions/{id}`) only needs steps 1-3 and existing rows; build and test this now.
   - *Generation* (`POST /questions/generate`) is a thin endpoint that delegates to the RAG/LangGraph pipeline built in step 7-8 below — it has no real implementation until those steps exist. Stub it (e.g. return `501 Not Implemented` or a mocked response) if you need to unblock frontend/exam work sooner; do not consider step 4 complete until the real pipeline is wired in.
5. **exam creation, submission, results endpoints** — `app/api/endpoints/exams.py` + `app/services/exam_service.py`. Depends on: step 4's retrieval (exam generation selects from `validated` questions only, per [capstone-database-design.md](capstone-database-design.md) section 9).
6. **weak-topic and performance endpoints** — extend `app/api/endpoints/analytics.py` + `app/services/analytics_service.py`. Depends on: step 5, since `topic_performance` is populated by attempt submission.

Current implementation note: retrieval, exam, attempt, scoring, and analytics routes are implemented and covered by deterministic tests that do not call an LLM. `POST /api/v1/questions/generate` remains a teacher-authorized `501 Not Implemented` stub until steps 7-8 are complete. Do not replace it with synthetic generation data; wire the real workflow when Section 10.3 is implemented.

### 10.3 RAG and AI Generation Pipeline (AI lead)

7. **RAG ingestion and FAISS retrieval** — implement inside `app/rag/` (currently an empty package). This is the real blocker for step 4's generation endpoint. Required details:
   - add curriculum PDF groups and subject/chapter/topic metadata (feeds `curriculum_documents`/`source_references` per [capstone-database-design.md](capstone-database-design.md) section 6)
   - extract text using pypdf
   - chunk with roughly 512 tokens and 100-token overlap
   - generate embeddings with sentence-transformers
   - persist and query a FAISS index (`VECTOR_DB_PATH` from `.env.local`) — ingestion entry point is `scripts/ingest_curriculum.py` (currently a placeholder)
   - test at least five retrieval queries per subject
8. **LangGraph generation + validation workflow** — implement inside `app/graph/` and `app/agents/` (both currently empty packages). Completes step 4's generation endpoint end to end. Required details:
   - generate MCQ and numerical questions only
   - validate relevance, schema, difficulty, answer data, and duplicate detection
   - store valid questions as validated and invalid ones as rejected, persisting `question_validation_results` rows per question generation run
   - workflow: `retrieve_context -> generate_questions -> validate_questions -> save`
   - do not add teacher approval or learning-coach routing in the MVP

### 10.4 Scoring and Analytics Logic (backend lead)

9. **exam scoring and analytics service logic** — finalize scoring rules (exact-match MCQ, ±5% numerical tolerance) inside `app/services/exam_service.py` and `app/services/analytics_service.py`, per the attempt-submission contract in the API design doc.

### 10.5 Frontend (frontend lead)

10. **Streamlit pages and frontend flow** — `frontend/pages/1_Dashboard.py` through `5_Generate.py` and `frontend/components/sidebar.py` (all currently scaffolded but empty). Depends on steps 1-9 for the endpoints each page calls (a page can be stubbed against mocked data earlier, but the end-to-end flow below requires the real backend):
    - `1_Dashboard.py` -> weak-topic / progress summary (step 6)
    - `2_Exam.py` -> attempt an exam (step 5)
    - `3_Results.py` -> attempt results and explanations (step 9)
    - `4_Teacher.py` -> teacher question bank view (step 4 retrieval)
    - `5_Generate.py` -> trigger question generation (step 4 generation, needs steps 7-8)
    - Gate: the end-to-end flow `register -> login -> choose topic -> generate exam -> submit answers -> view results` must work.
    - Run from `capstone/` with `streamlit run frontend/streamlit_app.py --server.port 8501`.

### 10.6 Tests and Production Readiness (QA lead / DevOps lead)

11. **unit and integration tests** — `tests/unit/`, `tests/integration/` (health tests already exist as a template: `tests/unit/test_health.py`, `tests/integration/test_health_integration.py`). See Section 11 (Test and Quality Gates) below.
12. **production readiness checks** — see Section 12 (Deployment Gate) below.

## 11. Test and Quality Gates

Run:

```powershell
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/ --cov=app --cov-report=term-missing
```

Required quality checks:

- coverage at least 60%
- critical flows tested
- no unit test calls the real LLM
- PostgreSQL test database is isolated from development data
- MCQ score calculation is exact-match
- numerical scoring uses ±5% tolerance
- weak-topic calculation is reproducible

## 12. Deployment Gate

Only after local validation succeeds:

- set production environment variables
- create cloud PostgreSQL database
- deploy FastAPI backend
- deploy Streamlit frontend
- run alembic upgrade head in production
- run python scripts/ingest_curriculum.py --all
- test login, exam generation, scoring, and results in production

Local development continues to use the virtual environment and PostgreSQL. Docker is reserved for deployment, not local development.

## 13. AI Prompt Sequence

Use separate prompts and validate after each one:

1. scaffold the capstone project structure and package files
2. add PostgreSQL settings, session factory, Alembic setup, and /health
3. implement the models from DATABASE_SCHEMA.md and the initial migration
4. implement auth and Pydantic schemas
5. implement the RAG ingestion and FAISS retrieval slice
6. implement MCQ and numerical generation, validation, and LangGraph flow
7. implement exam scoring and weak-topic analytics
8. implement the five Streamlit pages against API_DESIGN.md
9. add and run unit and integration tests
10. create deployment artifacts after local validation passes

Each prompt should name the files it may change, the contract it must follow, and the validation command to run after the change.

## 14. Completion Gate

Feature implementation may begin only when all of the following are true:

- [x] PostgreSQL capstone and capstone_test are reachable
- [x] project scaffold exists under capstone/
- [x] .env.local is ignored by Git
- [x] API_DESIGN.md is complete ([capstone-api-design.md](capstone-api-design.md))
- [x] DATABASE_SCHEMA.md is complete ([capstone-database-design.md](capstone-database-design.md))
- [x] FastAPI /health passes (see Section 0 note: does not yet verify DB connectivity)
- [x] Alembic migration applies to both databases (Section 9.1, completed 2026-08-27)
- [ ] LLM provider and model are recorded in SETUP.md — outstanding; `.env.example` still has placeholder values
- [ ] backend, frontend, AI, and QA ownership are assigned — [TEAM_ROLES.md](../capstone/TEAM_ROLES.md) defines roles but no individuals are assigned yet

## 15. Documentation Relationship

- [capstone-implementation-plan.md](capstone-implementation-plan.md) defines the product intent, architecture, scope, and release criteria.
- This runbook defines the exact execution path to realize that plan.
- [capstone/SETUP.md](../capstone/SETUP.md) is the quick-start guide for local environment, dependency, database, and application startup commands.
- If a decision conflicts, the plan wins; the runbook is updated to match it.
