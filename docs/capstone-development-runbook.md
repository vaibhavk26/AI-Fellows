# Capstone Build Checklist

This runbook contains the commands, setup procedures, validation gates, and AI coding-tool sequence for executing the roadmap in [capstone-implementation-plan.md](capstone-implementation-plan.md).

Use the implementation plan for MVP scope, phases, ownership, milestones, risks, and delivery criteria. Use this runbook for the step-by-step operational work.

## Current Decisions

- Database: PostgreSQL locally, in tests, and in production.
- Local development: Python virtual environment, not Docker.
- Backend: FastAPI on port `8000`.
- Frontend: Streamlit on port `8501`.
- Relational ORM: SQLAlchemy.
- Migrations: Alembic.
- Vector store: FAISS.
- PDF extraction: `pypdf`.
- MVP question types: MCQ and Numerical.
- MVP question statuses: `validated` and `rejected`.
- MVP does not include teacher approval, LLM grading for written answers, learning-coach recommendations, or advanced class analytics.

## Target Databases

Create two local PostgreSQL databases:

```text
capstone       Development database
capstone_test  Automated-test database
```

Use these connection strings in `capstone/.env.local`:

```env
DATABASE_URL=postgresql+psycopg2://capstone_user:password@localhost:5432/capstone
TEST_DATABASE_URL=postgresql+psycopg2://capstone_user:password@localhost:5432/capstone_test
```

Do not commit `.env.local` or real credentials.

## Step 1: Verify Prerequisites

- [ ] Install Python 3.11 or newer.
- [ ] Install PostgreSQL locally.
- [ ] Confirm PostgreSQL is running.
- [ ] Confirm `psql` is available in PowerShell.
- [ ] Confirm Git and VS Code are available.

Run:

```powershell
python --version
psql --version
git status
```

If `psql` is not recognized, add the PostgreSQL `bin` directory to PATH or use `SQL Shell (psql)`.

## Step 2: Create PostgreSQL User and Databases

Run these commands using a PostgreSQL administrator account. Replace the password with a local secret and do not commit it.

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

## Step 3: Create the Project Scaffold

From the repository root:

```powershell
New-Item -ItemType Directory -Force capstone
Set-Location capstone
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Create this structure before feature implementation:

```text
capstone/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── core/
│   ├── api/endpoints/
│   ├── api/schemas/
│   ├── db/models/
│   ├── db/repositories/
│   ├── services/
│   ├── agents/
│   ├── graph/
│   └── rag/
├── frontend/
│   ├── streamlit_app.py
│   ├── pages/
│   └── components/
├── tests/unit/
├── tests/integration/
├── scripts/
├── data/curriculum/physics/
├── data/curriculum/mathematics/
├── alembic/
├── requirements.txt
├── alembic.ini
├── .env.example
├── .env.local
├── pytest.ini
└── README.md
```

Add `__init__.py` files to Python package directories.

## Step 4: Create Project Documentation

Keep the existing reference documents at the repository root. Do not create a second copy under `docs/` unless the team deliberately moves them.

Create these files inside `capstone/`:

- [ ] `SETUP.md` - environment, PostgreSQL, migration, and run commands.
- [ ] `API_DESIGN.md` - endpoint contracts and error formats.
- [ ] `DATABASE_SCHEMA.md` - entities, fields, relationships, and constraints.
- [ ] `TEAM_ROLES.md` - ownership and branch assignments.

## Step 5: Install Dependencies and Configure Environment

Create `requirements.txt` with the versions from `capstone-implementation-plan.md`, then run:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Copy `.env.example` to `.env.local` and set:

```env
DATABASE_URL=postgresql+psycopg2://capstone_user:password@localhost:5432/capstone
TEST_DATABASE_URL=postgresql+psycopg2://capstone_user:password@localhost:5432/capstone_test
VECTOR_DB_TYPE=faiss
VECTOR_DB_PATH=./vectors
DEBUG=True
ENVIRONMENT=development
```

The LLM variables must be selected before AI-agent implementation:

```env
LLM_PROVIDER=openai-compatible
LLM_MODEL=replace-with-approved-model
OPENAI_API_KEY=replace-with-local-secret
```

Use mocked LLM responses in unit tests. Never require an API key to run unit tests.

## Step 6: Define Contracts Before Coding Features

Complete `API_DESIGN.md` and `DATABASE_SCHEMA.md` before implementing endpoints or frontend pages.

### Required API decisions

- [ ] Request and response fields for every endpoint.
- [ ] Authentication requirements per endpoint.
- [ ] HTTP status codes.
- [ ] Standard error response shape.
- [ ] Question filters and pagination behavior.
- [ ] Numerical scoring tolerance: `+-5%` unless the contract specifies otherwise.
- [ ] Question lifecycle: `generated` -> `validated` or `rejected`.

### Required database decisions

- [ ] Primary and foreign keys.
- [ ] Required and nullable fields.
- [ ] Enum values for roles, question types, difficulty, and status.
- [ ] Relationships and cascade behavior.
- [ ] Unique constraints.
- [ ] Timestamp conventions.
- [ ] Subject, chapter, and topic persistence or seed-data strategy.

Minimum MVP entities:

```text
User
Question
Exam
ExamQuestion
StudentAttempt
StudentAnswer
TopicPerformance
```

## Step 7: Bootstrap and Validate the Application

From `capstone/`:

```powershell
alembic init alembic
uvicorn app.main:app --reload --port 8000
```

Implement and verify the first endpoint:

```text
GET /health -> {"status": "ok"}
```

Open the API documentation at `http://localhost:8000/docs`.

The first gate is complete only when:

- [ ] FastAPI starts successfully.
- [ ] `/health` returns HTTP 200.
- [ ] Settings load from `.env.local`.
- [ ] The application connects to `capstone`.

## Step 8: Implement Database Models and Migration

- [ ] Implement the seven MVP model groups.
- [ ] Configure Alembic `target_metadata`.
- [ ] Generate the initial migration.
- [ ] Apply it to `capstone`.
- [ ] Apply it to `capstone_test`.
- [ ] Add model and relationship tests.

Commands:

```powershell
alembic revision --autogenerate -m "Initial MVP schema"
alembic upgrade head
$env:DATABASE_URL=$env:TEST_DATABASE_URL
alembic upgrade head
```

Restore the development `DATABASE_URL` after the test migration command.

Do not continue until both databases migrate successfully.

## Step 9: Implement Authentication and Core APIs

Implement in this order:

1. Pydantic schemas.
2. Password hashing and JWT utilities.
3. Register, login, and current-user endpoints.
4. Question generation and retrieval endpoints.
5. Exam creation, submission, and results endpoints.
6. Topic-performance and weak-topic endpoints.

Test each endpoint with FastAPI `TestClient` before connecting Streamlit.

## Step 10: Implement RAG and AI Workflow

- [ ] Add the seven curriculum chapter PDF groups.
- [ ] Extract text with `pypdf`.
- [ ] Chunk at approximately 512 tokens with 100-token overlap.
- [ ] Attach subject, chapter, topic, and page metadata.
- [ ] Generate embeddings with `sentence-transformers`.
- [ ] Persist and query a FAISS index.
- [ ] Test at least five retrieval queries per subject.
- [ ] Implement MCQ and Numerical generation only.
- [ ] Validate relevance, schema, difficulty, answer data, and duplicates.
- [ ] Store passing questions as `validated` and failing questions as `rejected`.

LangGraph MVP flow:

```text
retrieve_context -> generate_questions -> validate_questions -> save
```

Do not add teacher approval or learning-coach routing to this MVP workflow.

## Step 11: Build the Streamlit MVP

Implement exactly these pages:

```text
frontend/pages/1_Dashboard.py
frontend/pages/2_Exam.py
frontend/pages/3_Results.py
frontend/pages/4_Teacher.py
frontend/pages/5_Generate.py
```

Run from `capstone/`:

```powershell
streamlit run frontend/streamlit_app.py --server.port 8501
```

The frontend gate is complete when this flow works:

```text
register -> login -> choose topic -> generate exam -> submit answers -> view results
```

## Step 12: Test the Complete MVP

Run:

```powershell
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/ --cov=app --cov-report=term-missing
```

Acceptance criteria:

- [ ] Coverage is at least 60%.
- [ ] All critical-path flows are tested.
- [ ] No unit test calls the real LLM.
- [ ] PostgreSQL test database is isolated from development data.
- [ ] MCQ scoring is exact-match accurate.
- [ ] Numerical scoring applies the agreed tolerance.
- [ ] Weak-topic calculation is reproducible.

## Step 13: Prepare Deployment

Only after the local end-to-end flow passes:

- [ ] Create production environment variables.
- [ ] Create the cloud PostgreSQL database.
- [ ] Deploy the FastAPI backend.
- [ ] Deploy the Streamlit frontend.
- [ ] Run `alembic upgrade head` in production.
- [ ] Run `python scripts/ingest_curriculum.py --all`.
- [ ] Test login, exam generation, scoring, and results in production.

Docker is for cloud deployment. Local development continues to use the Python virtual environment and PostgreSQL.

## AI Coding Tool Prompt Sequence

Use separate prompts and validate after each one:

1. Scaffold the `capstone/` project structure and package files.
2. Add PostgreSQL settings, SQLAlchemy session, Alembic, and `/health`.
3. Implement models from `DATABASE_SCHEMA.md` and the initial migration.
4. Implement Pydantic schemas and authentication.
5. Implement the RAG ingestion and FAISS retrieval slice.
6. Implement MCQ/Numerical generation, validation, and LangGraph flow.
7. Implement exam scoring and weak-topic analytics.
8. Implement the five Streamlit pages against `API_DESIGN.md`.
9. Add and run unit, integration, and end-to-end tests.
10. Prepare deployment files only after local validation passes.

Never ask the AI tool to generate the entire application in one prompt. Each prompt should name the files it may change, the contract it must follow, and the command used to validate the change.

## Completion Gate Before Feature Work

Feature implementation may begin only when all of these are true:

- [ ] PostgreSQL `capstone` and `capstone_test` are reachable.
- [ ] Project scaffold exists under `capstone/`.
- [ ] `.env.local` is ignored by Git.
- [ ] `API_DESIGN.md` is complete.
- [ ] `DATABASE_SCHEMA.md` is complete.
- [ ] FastAPI `/health` passes.
- [ ] Alembic initial migration applies to both databases.
- [ ] LLM provider and model are recorded in `SETUP.md`.
- [ ] The team has assigned ownership for backend, frontend, AI, and QA.
