# Capstone Implementation Plan
## AI-Powered Personalized Learning & Examination System
### CBSE Class 10 - Physics & Mathematics

---

## Executive Summary

**MVP Timeline:** 4 weeks (with 2 weeks reserved as a contingency buffer)  
**Team Structure:** 5-6 developers (backend, frontend, AI/ML, QA, tech lead)  
**Tech Stack:** Python 3.11+, FastAPI, Streamlit, LangChain, LangGraph, PostgreSQL, FAISS  
**Delivery:** Working MVP with student exam generation, validation, scoring, and weak-area detection  
**Strategy:** Maximum parallelization, MVP-only scope, aggressive task consolidation  

**Database decision:** Use PostgreSQL locally, for integration tests, and in production. This keeps all environments on the same database engine and avoids dialect-specific behavior during the four-week implementation.

## Execution Guide

Use this document for MVP scope, implementation phases, team ownership, milestones, risks, and delivery criteria.

For exact setup commands, PostgreSQL operations, validation gates, AI coding-tool prompts, and run instructions, follow the [Capstone Development Runbook](capstone-development-runbook.md).

---

## Phase 1: Setup & Infrastructure (Week 1)

### 1.1 Repository & Collaboration Setup

- [ ] **Create dev branches per developer**
  - `dev-backend`, `dev-frontend`, `dev-ai`, `dev-devops`
  - Main integration branch: `dev`
  - Production: `main`

- [ ] **Initialize project structure** (capstone/)
  ```
  capstone/
  ├── app/
  │   ├── api/endpoints/
  │   ├── core/config.py
  │   ├── db/models/
  │   ├── services/
  │   ├── agents/
  │   ├── graph/
  │   └── rag/
  ├── frontend/
  │   └── pages/
  ├── tests/
  ├── data/curriculum/
  ├── requirements.txt
  ├── .env.example
  └── README.md
  ```

- [ ] **Create documentation files**
  - [ ] `docs/TEAM_ROLES.md` — developer assignments
  - [ ] `docs/capstone-development-runbook.md` — local setup and execution guide
  - [ ] `docs/API_DESIGN.md` — API contracts
  - [ ] `CONTRIBUTING.md` — team workflow

### 1.2 Environment & Dependencies

- [ ] **Python 3.11+ environment setup**
  ```bash
  python -m venv venv
  source venv/bin/activate
  ```

- [ ] **Create requirements.txt** with all dependencies
  ```
  # Web Framework
  fastapi==0.104.1
  uvicorn==0.24.0
  pydantic==2.5.0
  pydantic-settings==2.1.0
  
  # AI & LLM
  langchain==0.1.0
  langchain-openai==0.0.5
  langgraph==0.0.15
  langchain-community==0.0.10
  
  # Vector DB
  faiss-cpu==1.7.4
  
  # Embeddings
  sentence-transformers==2.2.2
  
  # Database
  sqlalchemy==2.0.23
  psycopg2-binary==2.9.9
  alembic==1.13.0
  
  # PDF/Document Processing
  pypdf==4.0.0
  
  # Frontend
  streamlit==1.28.1
  
  # Security
  python-jose==3.3.0
  passlib==1.7.4
  bcrypt==4.1.1
  
  # Testing
  pytest==7.4.3
  pytest-asyncio==0.21.1
  httpx==0.25.0
  
  # Utilities
  python-dotenv==1.0.0
  requests==2.31.0
  ```

- [ ] **Setup .env.example template**
  ```
  # Database
  DATABASE_URL=postgresql+psycopg2://capstone_user:password@localhost:5432/capstone
  
  # LLM API
  OPENAI_API_KEY=sk-...
  
  # Security
  SECRET_KEY=your-secret-key-here
  ALGORITHM=HS256
  ACCESS_TOKEN_EXPIRE_MINUTES=30
  
  # Vector DB
  VECTOR_DB_TYPE=faiss
  VECTOR_DB_PATH=./vectors/
  
  # App
  DEBUG=True
  ENVIRONMENT=development
  ```

- [ ] **Install all dependencies**
  ```bash
  pip install -r requirements.txt
  ```

### 1.3 Database Setup (Parallel Track)

- [ ] **PostgreSQL installation & initialization** (can run parallel to section 1.1-1.2)
  - Create databases: `capstone` and `capstone_test`
  - Create user with permissions

- [ ] **Initialize Alembic for migrations**
  ```bash
  alembic init alembic
  ```

- [ ] **Setup SQLAlchemy session factory** (`app/db/session.py`)
  - Use `postgresql+psycopg2://` URLs for development, testing, and production

- [ ] **Quick curriculum data collection**
  - Collect core PDFs: Physics (3 chapters) + Math (4 chapters)
  - Store in `data/curriculum/` folder
  - **NO cleanup/parsing yet** — done in Phase 2

Phase 1 produces the runnable development environment, database connection, migration scaffold, and raw curriculum inputs. RAG processing and retrieval validation begin in Phase 2 after these prerequisites are available.

---

## Phase 2: Core AI Agents & Backend APIs (Weeks 1-2) — PARALLEL EXECUTION

**CRITICAL:** Backend and AI teams work simultaneously on separate branches. Daily integration checks.

### 2.1 Database Models & Schemas (Backend Team)

- [ ] **Define SQLAlchemy models** (`app/db/models/`) — MVP only
  - [ ] `user.py` — User, StudentProfile, TeacherProfile
  - [ ] `question.py` — Question, QuestionMetadata
  - [ ] `exam.py` — Exam, ExamQuestion, StudentAttempt, StudentAnswer
  - [ ] `analytics.py` — TopicPerformance, StudentProgress

- [ ] **Create database migration**
  ```bash
  alembic revision --autogenerate -m "Initial schema"
  alembic upgrade head
  ```

- [ ] **Define Pydantic schemas** (`app/api/schemas/`)
  - [ ] `question_schemas.py` — QuestionGenerationRequest, QuestionResponse
  - [ ] `exam_schemas.py` — ExamCreateRequest, ExamSubmitRequest, ExamResponse
  - [ ] `user_schemas.py` — UserRegister, UserLogin, TokenResponse
  - [ ] `analytics_schemas.py` — TopicPerformanceResponse

### 2.2 RAG Pipeline & Document Processing (AI Team)

- [ ] **Curriculum data ingestion** (`app/rag/ingestion.py`)
  - Load PDFs using pypdf
  - Extract text with basic cleaning

- [ ] **Document chunking** (`app/rag/chunking.py`)
  - Chunk size: 512 tokens, Overlap: 100 tokens
  - Tag metadata: subject, chapter, topic

- [ ] **Vector store setup** (`app/rag/retrieval.py`)
  - Initialize FAISS
  - Ingest curriculum documents
  - Test retrieval (5 sample queries per subject)

- [ ] **Build ingestion script** (`scripts/ingest_curriculum.py`)
  ```bash
  python scripts/ingest_curriculum.py --all
  ```

### 2.3 Question Generator Agent (AI Team)

- [ ] **Minimal generator** (`app/agents/question_generator.py`)
  - Retrieve context via RAG
  - Build generation prompt (MCQ + Numerical focus only)
  - Call LLM, parse JSON response
  - Basic validation

- [ ] **Key question types** (defer long answer, competency-based to Post-MVP)
  - [ ] MCQ (focus: auto-scoreable)
  - [ ] Numerical (focus: auto-scoreable)
  - [ ] ~~Short answer~~ (defer to Post-MVP)

### 2.4 Question Validator Agent (AI Team)

- [ ] **Lightweight validator** (`app/agents/validator.py`)
  - Curriculum relevance (vector similarity only, no LLM)
  - Answer correctness (basic logic check)
  - Difficulty match (schema validation only)
  - Duplicate check (vector similarity)

### 2.5 LangGraph Workflow (AI Team)

- [ ] **Simplified workflow state** (`app/graph/state.py`)
  ```python
  class QuestionGenerationState(TypedDict):
      subject: str
      chapter: str
      topic: str
      difficulty: str
      question_count: int
      questions: list[Question]
      validation_passed: bool
  ```

- [ ] **Core workflow nodes** (`app/graph/nodes.py`, `app/graph/workflow.py`)
  - `retrieve_context_node()` → `generate_questions_node()` → `validate_questions_node()` → `save_node()`
  - **Automated validation workflow** (MVP: no teacher approval)
  - Questions that pass validation are stored with status `validated`.
  - Questions that fail validation are stored with status `rejected`.
  - No conditional routing complexity

### 2.6 Authentication & Core API (Backend Team)

- [ ] **Security module** (`app/core/security.py`)
  - Password hashing (bcrypt)
  - JWT generation/verification

- [ ] **Auth endpoints** (`app/api/endpoints/auth.py`)
  - `POST /auth/register` (student + teacher)
  - `POST /auth/login`
  - `GET /auth/me`

- [ ] **Question endpoints** (`app/api/endpoints/questions.py`)
  - `POST /questions/generate` → call LangGraph workflow
  - `GET /questions/{id}`
  - `GET /questions/` (with filters)

- [ ] **Exam endpoints** (`app/api/endpoints/exams.py`)
  - `POST /exams/create` (MCQ + Numerical only)
  - `GET /exams/{id}`
  - `POST /exams/{id}/submit` (auto-evaluate MCQ/Numerical)
  - `GET /exams/{id}/results`

- [ ] **Analytics endpoints** (`app/api/endpoints/analytics.py`)
  - `GET /analytics/student/{id}/performance`
  - `GET /analytics/student/{id}/weak-topics`

### 2.7 Support Services (Backend Team)

- [ ] **Exam service** (`app/services/exam_service.py`)
  - Create exam (select random validated questions)
  - Submit & auto-evaluate (MCQ: exact match, Numerical: tolerance ±5%)
  - Calculate topic performance

- [ ] **Analytics service** (`app/services/analytics_service.py`)
  - Calculate performance per topic
  - Identify weak topics (score < 60%)
  - Return weak-topic data for the student dashboard; personalized recommendations are Post-MVP

- [ ] **Main FastAPI app** (`app/main.py`)
  ```bash
  uvicorn app.main:app --reload --port 8000
  ```

---

## Phase 3: Frontend & Integration Testing (Weeks 2-3)

### 3.1 Streamlit Multi-Page App (Frontend Team)

- [ ] **Create Streamlit multi-page app** (`frontend/streamlit_app.py`)
  ```
  frontend/
  ├── streamlit_app.py          # Main entry point
  ├── pages/
  │   ├── 1_Dashboard.py        # Student/teacher home
  │   ├── 2_Exam.py             # Practice exam flow
  │   ├── 3_Results.py          # Exam results and feedback
  │   ├── 4_Teacher.py          # Basic teacher statistics
  │   └── 5_Generate.py         # Teacher question generation
  └── components/
      ├── sidebar.py
      ├── auth_widgets.py
      └── charts.py
  ```

### 3.2 Authentication & Session Management

- [ ] **Build auth UI** (`frontend/components/auth_widgets.py`)
  - [ ] Login form
  - [ ] Register form (student vs teacher)
  - [ ] Session state management

- [ ] **Implement navigation** (`frontend/components/sidebar.py`)
  - Role-based menu
  - User info display
  - Logout button

### 3.3 Student Pages (MVP Only)

- [ ] **Student Dashboard** (`pages/1_Dashboard.py`)
  - User stats (total exams, avg score)
  - Quick action button: "Take Exam"

- [ ] **Practice Exam Page** (`pages/2_Exam.py`)
  - Subject & chapter dropdown
  - Difficulty: Easy/Medium/Hard
  - Question count slider
  - "Generate Exam" button
  - Display MCQ/Numerical questions
  - Answer submission form

- [ ] **Exam Results Page** (`pages/3_Results.py`)
  - Overall score & percentage
  - Topic-wise performance table
  - Question review (Q&A)

### 3.4 Teacher Pages (Minimal MVP)

- [ ] **Teacher Dashboard** (`pages/4_Teacher.py`)
  - Basic class statistics (student count, average score)
  - Quick action button: "Generate Questions"

- [ ] **Generate Questions Page** (`pages/5_Generate.py`)
  - Subject, chapter, topic dropdowns
  - Difficulty picker
  - Question count slider
  - "Generate Questions" button (calls API)
  - Preview generated questions

### 3.5 Streamlit Configuration & Testing

- [ ] **Setup authentication** (`frontend/components/auth_widgets.py`)
  - Simple login/register form
  - Call auth API endpoints

- [ ] **Implement sidebar** (`frontend/components/sidebar.py`)
  - Role-based navigation
  - Logout button

- [ ] **Create `.streamlit/config.toml`**
  ```toml
  [theme]
  primaryColor = "#0066cc"
  
  [client]
  showErrorDetails = true
  ```

- [ ] **Manual testing**
  ```bash
  streamlit run frontend/streamlit_app.py --server.port 8501
  ```

### 3.6 Integration Testing (Parallel with Frontend)

- [ ] **API + Frontend Integration Tests**
  - [ ] Register flow → Login → Navigate pages
  - [ ] Generate questions → Verify API response
  - [ ] Create exam → Submit answers → Check results

- [ ] **Test database operations**
  - User CRUD operations
  - Question storage & retrieval
  - Exam attempt recording

---

## Phase 4: Testing, Optimization & Deployment (Week 3-4)

### 4.1 Core Testing

- [ ] **Unit tests** (`tests/unit/`)
  - [ ] Test RAG retrieval (10 samples per subject)
  - [ ] Test question generation (valid JSON, schema compliance)
  - [ ] Test exam evaluation (MCQ auto-scoring, Numerical tolerance)
  - [ ] Test analytics (performance calculation)
  - Target: 60%+ code coverage, with all critical-path flows tested

- [ ] **Run test suite**
  ```bash
  pytest tests/unit/ -v
  pytest tests/integration/ -v
  pytest tests/ --cov=app --cov-report=term-missing
  ```

### 4.2 Bug Fixes & Performance Tuning

- [ ] **Fix integration issues**
  - Frontend ↔ Backend communication
  - Database connection pooling
  - LLM call timeouts

- [ ] **Performance optimization**
  - Cache curriculum retrieval
  - Optimize vector DB queries
  - Batch LLM calls if possible

- [ ] **Error handling**
  - Try-catch blocks in APIs
  - Meaningful error messages
  - Logging to file

### 4.3 Demo Preparation

- [ ] **Create test data**
  - 2 test students, 1 test teacher
  - 50 pre-generated questions (validated)
  - 5 sample exam attempts

- [ ] **Validation checklist**
  - [ ] Student can register & login
  - [ ] Student can generate exam
  - [ ] System auto-evaluates MCQ/Numerical questions
  - [ ] Student sees score & topic performance
  - [ ] Teacher can generate questions
  - [ ] System validates & stores questions

- [ ] **Demo scripts** (`scripts/demo_scenario.py`)
  - Automated demo flow
  - Sample data seeding

### 4.4 Deployment Preparation (MVP to Cloud)

- [ ] **Production environment** (`.env.production`)
  - PostgreSQL connection string (cloud DB)
  - LLM API key
  - Secret key (strong random)

- [ ] **Docker setup** (`Dockerfile`, optional)
  ```dockerfile
  FROM python:3.11-slim
  WORKDIR /app
  COPY requirements.txt .
  RUN pip install -r requirements.txt
  COPY . .
  EXPOSE 8000
  CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
  ```

- [ ] **Cloud deployment** (Render.com / Railway.app)
  - Create PostgreSQL database in cloud
  - Deploy backend service (uvicorn)
  - Deploy frontend service (Streamlit)
  - Run migrations: `alembic upgrade head`
  - Ingest curriculum: `python scripts/ingest_curriculum.py --all`
  - Verify endpoints work in production

- [ ] **Post-deployment checks**
  - Test login on production
  - Generate sample exam
  - Verify scoring
  - Check error logs

### 4.5 Final Demo & Handoff

- [ ] **Live demo** (15-20 minutes)
  - Show student exam generation → scoring → weak areas
  - Show teacher question generation → validation
  - Live API Swagger UI (FastAPI docs)

- [ ] **Documentation for Post-MVP**
  - [ ] Features to add (short answer, long answer, competency-based)
  - [ ] Performance optimizations
  - [ ] Teacher review and approval workflow
  - [ ] Advanced analytics (trends, badges)

---

## 4-Week Milestone Schedule

### Week 1
- **End of Day 3:** Project setup complete, all environments ready
- **End of Day 5:** Curriculum ingestion and retrieval prototype working; LangGraph interfaces defined
- **Progress check:** Can retrieve curriculum context, LLM responds with JSON

### Week 2
- **End of Day 8:** Question generator & validator working, API endpoints operational
- **End of Day 10:** Frontend scaffolding complete, can call backend APIs
- **Progress check:** Can generate MCQ questions, auto-evaluate exam, view results

### Week 3
- **End of Day 13:** All student pages working (dashboard, exam, results)
- **End of Day 15:** Teacher pages working, integration tests passing
- **Progress check:** Full workflow works end-to-end (register → exam → results)

### Week 4
- **End of Day 18:** Bug fixes, demo data loaded, performance tuned
- **End of Day 20:** Deployed to cloud, live demo ready
- **Final:** MVP shipped & deployable

---

## Project Structure (Simplified for MVP)

```
AI-Fellows/
├── docs/
│   ├── capstone-proposal.md
│   ├── capstone-requirements.md
│   ├── capstone-architecture.md
│   ├── capstone-technical-design.md
│   ├── capstone-implementation-plan.md
│   └── capstone-development-runbook.md
│
├── capstone/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/ (config.py, security.py)
│   │   ├── api/endpoints/ (auth.py, questions.py, exams.py, analytics.py)
│   │   ├── api/schemas/
│   │   ├── db/ (models/, session.py)
│   │   ├── services/ (exam_service.py, analytics_service.py, rag_service.py)
│   │   ├── agents/ (question_generator.py, validator.py)
│   │   ├── graph/ (workflow.py, state.py, nodes.py)
│   │   └── rag/ (ingestion.py, chunking.py, retrieval.py)
│   │
│   ├── frontend/
│   │   ├── streamlit_app.py
│   │   ├── pages/ (1_Dashboard.py, 2_Exam.py, 3_Results.py, 4_Teacher.py, 5_Generate.py)
│   │   └── components/ (auth_widgets.py, sidebar.py)
│   │
│   ├── tests/ (unit/, integration/)
│   ├── data/curriculum/ (physics/, mathematics/)
│   ├── scripts/ (ingest_curriculum.py, seed_test_data.py)
│   ├── requirements.txt
│   ├── .env.example
│   ├── pytest.ini
│   └── README.md
│
├── CONTRIBUTING.md
└── README.md
```

---

## Key Compressed Scope Changes

### ✅ MVP Focus (Keep)
- MCQ questions (auto-scoreable)
- Numerical questions (auto-scoreable)
- Question generation + validation
- Student exam attempts
- Auto-evaluation & scoring
- Topic performance tracking
- Weak area identification

### ⏸️ Post-MVP Features (Defer)
- Short answer questions (need LLM grading)
- Long answer questions (complex validation)
- Competency-based questions
- Teacher review and approval workflow
- Advanced analytics (trends, growth, badges)
- Student personalization recommendations
- Detailed learning coach workflow
- Class-level dashboards

---

## Recommended Dependencies Matrix (MVP)

| Component | Library | Version | Purpose |
|-----------|---------|---------|---------|
| **Web Framework** | FastAPI | 0.104.1 | Backend API |
| | Uvicorn | 0.24.0 | ASGI server |
| **UI Framework** | Streamlit | 1.28.1 | Frontend |
| **AI/LLM** | LangChain | 0.1.0 | RAG orchestration |
| | LangGraph | 0.0.15 | Workflow state management |
| | sentence-transformers | 2.2.2 | Embeddings |
| **Vector DB** | FAISS | 1.7.4 | Vector storage |
| **Database** | SQLAlchemy | 2.0.23 | ORM |
| | psycopg2-binary | 2.9.9 | PostgreSQL driver |
| | Alembic | 1.13.0 | Migrations |
| **Document Processing** | pypdf | 4.0.0 | PDF parsing |
| **Validation** | Pydantic | 2.5.0 | Schema validation |
| **Security** | python-jose | 3.3.0 | JWT |
| | bcrypt | 4.1.1 | Password hashing |
| **Testing** | pytest | 7.4.3 | Test framework |
| | pytest-asyncio | 0.21.1 | Async tests |
| **Utilities** | python-dotenv | 1.0.0 | Environment variables |

---

## Success Criteria (4-Week MVP)

### MVP Completion (Week 4)
- [ ] ✅ Student can register & login
- [ ] ✅ Student can generate MCQ + Numerical exams
- [ ] ✅ System auto-evaluates MCQ (exact match) & Numerical (±5% tolerance)
- [ ] ✅ Student sees score, topic performance, & explanations
- [ ] ✅ System identifies weak topics (score < 60%)
- [ ] ✅ Teacher can generate questions  
- [ ] ✅ Teacher can view basic class statistics
- [ ] ✅ Deployed to cloud & accessible
- [ ] ✅ Live demo working (register → exam → results)

### Quality Metrics
- [ ] API response time < 2 seconds (excluding LLM)
- [ ] Question generation accuracy ≥ 80% on a manually reviewed holdout set
- [ ] Vector retrieval working across Physics and Mathematics curriculum
- [ ] Auto-evaluation 100% accurate (MCQ/Numerical)
- [ ] Test coverage ≥ 60%, including all critical-path flows

### Demo Requirements
- [ ] Live system (not pre-recorded)
- [ ] 2 test users (student + teacher)
- [ ] Generate exam → Take exam → View results (< 5 minutes end-to-end)
- [ ] Explain RAG + LLM generation + validation
- [ ] Show API docs (Swagger UI)

---

## Risk Mitigation (Compressed Timeline)

| Risk | Impact | Mitigation |
|------|--------|-----------|
| LLM API issues | High | Have mock responses ready, test early & often |
| Vector DB not working | High | Test RAG pipeline by Day 3 of Week 1 |
| Database schema issues | Medium | Use Alembic, test migrations weekly |
| Scope creep (trying to do too much) | Critical | Strict MVP definition, defer teacher review, recommendations, and complex grading |
| Team falling behind | High | Daily standups, daily integration checks, parallel execution |
| Deployment failures | Medium | Docker setup early, test cloud deployment by Week 3 |

---

## Daily Workflow & Communication

### Daily Standup (10 minutes)
- What did you complete yesterday?
- What will you do today?
- Any blockers?

### Code Integration (Daily)
- Merge your branch to `dev` daily (if possible)
- Run full test suite after merge
- Address merge conflicts immediately

### Blockers Escalation
- If stuck > 2 hours, ping tech lead
- Tech lead removes blockers same day

---

## Quick Start Commands

```bash
# Setup
python -m venv venv
source venv/bin/activate  # Mac/Linux
# OR
venv\Scripts\activate     # Windows
pip install -r requirements.txt

# Database
alembic upgrade head
python scripts/ingest_curriculum.py --all

# Run Backend (Terminal 1)
uvicorn app.main:app --reload --port 8000

# Run Frontend (Terminal 2)
streamlit run frontend/streamlit_app.py --server.port 8501

# Run Tests
pytest tests/ -v --cov=app

# API Documentation
# Open: http://localhost:8000/docs (Swagger UI)
# Open: http://localhost:8501 (Streamlit)
```

---

## Document Version

**Version:** 2.0 (Compressed from 6 weeks to 4 weeks)  
**Last Updated:** 2026-08-20  
**Status:** Ready for Execution  
**Author:** Tech Lead
