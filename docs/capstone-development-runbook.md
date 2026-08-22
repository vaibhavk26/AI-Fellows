# Capstone Development Runbook

This document is the execution guide for the MVP defined in [capstone-implementation-plan.md](capstone-implementation-plan.md).

Use it for setup steps, exact commands, validation gates, and the AI prompt sequence. It does not redefine scope or architecture; those decisions live in the implementation plan.

The authoritative design references for the project are:

- [capstone-api-design.md](capstone-api-design.md)
- [capstone-database-design.md](capstone-database-design.md)

These files are the source of truth for API contracts and database design. Do not create duplicate root-level copies of the same contract or schema documents during implementation.

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

Verify the development machine is ready:

- Python 3.11 or newer installed
- PostgreSQL installed and running locally
- psql available in PowerShell
- Git and VS Code installed

Run:

```powershell
python --version
psql --version
git status
```

If psql is not recognized, add the PostgreSQL bin directory to PATH or use SQL Shell (psql).

## 2.1 Dependency Baseline

Use the following dependency baseline for the MVP before implementation starts:

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
```

Do not commit .env.local or real credentials.

Use mocked LLM responses in unit tests. Unit tests must not require a live API key.

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

From the capstone/ directory:

```powershell
alembic init alembic
uvicorn app.main:app --reload --port 8000
```

Test the initial app health endpoint:

```text
GET /health -> {"status": "ok"}
```

Open the Swagger docs at http://localhost:8000/docs.

The gate is complete only when:
- FastAPI starts successfully
- /health returns HTTP 200
- settings load from .env.local
- the app connects to the capstone database

## 9. Database Migration Sequence

Implement models from the schema, then run:

```powershell
alembic revision --autogenerate -m "Initial MVP schema"
alembic upgrade head
$env:DATABASE_URL=$env:TEST_DATABASE_URL
alembic upgrade head
```

Restore the development DATABASE_URL after the test migration step.

Do not proceed until both databases are migrated successfully.

## 10. Implementation Sequence

Build in this order:

1. Pydantic schemas
2. password hashing and JWT utilities
3. register, login, current-user endpoints
4. question generation and retrieval endpoints
5. exam creation, submission, results endpoints
6. weak-topic and performance endpoints
7. RAG ingestion and FAISS retrieval
8. LangGraph generation + validation workflow
9. exam scoring and analytics service logic
10. Streamlit pages and frontend flow
11. unit and integration tests
12. production readiness checks

## 11. RAG and AI Workflow

Required implementation details:

- add curriculum PDF groups and subject/chapter/topic metadata
- extract text using pypdf
- chunk with roughly 512 tokens and 100-token overlap
- generate embeddings with sentence-transformers
- persist and query a FAISS index
- test at least five retrieval queries per subject
- generate MCQ and numerical questions only
- validate relevance, schema, difficulty, answer data, and duplicate detection
- store valid questions as validated and invalid ones as rejected

Workflow:

```text
retrieve_context -> generate_questions -> validate_questions -> save
```

Do not add teacher approval or learning-coach routing in the MVP.

## 12. Frontend Validation Flow

The frontend gate is complete when this user flow works end-to-end:

```text
register -> login -> choose topic -> generate exam -> submit answers -> view results
```

The app should include these pages:

```text
frontend/pages/1_Dashboard.py
frontend/pages/2_Exam.py
frontend/pages/3_Results.py
frontend/pages/4_Teacher.py
frontend/pages/5_Generate.py
```

Run from capstone/ with:

```powershell
streamlit run frontend/streamlit_app.py --server.port 8501
```

## 13. Test and Quality Gates

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

## 14. Deployment Gate

Only after local validation succeeds:

- set production environment variables
- create cloud PostgreSQL database
- deploy FastAPI backend
- deploy Streamlit frontend
- run alembic upgrade head in production
- run python scripts/ingest_curriculum.py --all
- test login, exam generation, scoring, and results in production

Local development continues to use the virtual environment and PostgreSQL. Docker is reserved for deployment, not local development.

## 15. AI Prompt Sequence

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

## 16. Completion Gate

Feature implementation may begin only when all of the following are true:

- PostgreSQL capstone and capstone_test are reachable
- project scaffold exists under capstone/
- .env.local is ignored by Git
- API_DESIGN.md is complete
- DATABASE_SCHEMA.md is complete
- FastAPI /health passes
- Alembic migration applies to both databases
- LLM provider and model are recorded in SETUP.md
- backend, frontend, AI, and QA ownership are assigned

## 17. Documentation Relationship

- [capstone-implementation-plan.md](capstone-implementation-plan.md) defines the product intent, architecture, scope, and release criteria.
- This runbook defines the exact execution path to realize that plan.
- If a decision conflicts, the plan wins; the runbook is updated to match it.
