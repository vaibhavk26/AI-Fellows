# Capstone Implementation Plan

This document is the single source of truth for project scope, architecture, milestones, and delivery criteria.

The companion runbook, [capstone-development-runbook.md](capstone-development-runbook.md), defines the exact operational steps, commands, and validation gates used to execute this plan. The runbook should not redefine scope or technical decisions.

## 1. Project Purpose

Build an MVP for an AI-powered personalized learning and examination system for CBSE Class 10 Physics and Mathematics.

The system must:
- let students register and log in
- generate exam questions from curriculum material using RAG + LLM
- validate generated questions before storage
- auto-score MCQ and numerical questions
- calculate topic-level performance and weak-topic indicators
- provide a minimal teacher workflow for generating and reviewing questions
- run locally with PostgreSQL and later deploy to a cloud environment

## 2. Scope Definition

### In scope for MVP
- Python 3.11+
- FastAPI backend on port 8000
- Streamlit frontend on port 8501
- PostgreSQL for development, test, and production
- SQLAlchemy + Alembic
- FAISS vector store
- PDF ingestion via pypdf
- RAG retrieval over curriculum content
- LangGraph workflow for question generation and validation
- MCQ and Numerical question types only
- Question status lifecycle: generated -> validated or rejected
- Auto-evaluation with exact match for MCQ and ±5% tolerance for numerical answers
- Student performance and weak-topic analytics
- Teacher page for generating questions and basic class statistics

### Out of scope for MVP
- short-answer or long-answer grading
- teacher approval workflow
- learning-coach recommendations
- advanced analytics dashboards
- competency-based question types
- multi-stage approval logic or complex agent routing

## 3. Technical Decisions

- Database: PostgreSQL in local, test, and production environments
- Local environment: Python virtual environment, no Docker for local development
- Backend: FastAPI
- Frontend: Streamlit
- ORM: SQLAlchemy
- Migrations: Alembic
- Vector store: FAISS
- Embeddings: sentence-transformers
- PDF extraction: pypdf
- Question workflow: retrieve context -> generate -> validate -> save
- Question status values: generated, validated, rejected
- Numerical scoring tolerance: ±5%

## 4. Architecture Overview

### Backend
- app/main.py: FastAPI application entry point
- app/core/: config, settings, security, JWT utilities
- app/api/endpoints/: auth, questions, exams, analytics
- app/api/schemas/: request and response models
- app/db/: models, session, migrations
- app/services/: exam logic, analytics logic, RAG service layer
- app/agents/: question generation and validation logic
- app/graph/: LangGraph state and workflow nodes
- app/rag/: ingestion, chunking, retrieval, FAISS integration

### Frontend
- frontend/streamlit_app.py: entry point
- frontend/pages/: Dashboard, Exam, Results, Teacher, Generate
- frontend/components/: auth widgets, sidebar, charts

### Data and tests
- data/curriculum/: Physics and Mathematics content
- tests/unit/: isolated logic tests
- tests/integration/: API and DB flow tests
- scripts/: ingestion, demo data, seeding utilities

## 5. Team Ownership

- Backend lead: API contracts, auth, database models, services, exam logic
- AI lead: RAG pipeline, embeddings, question generation, validation, LangGraph workflow
- Frontend lead: Streamlit pages, session handling, dashboard and exam UX
- QA lead: unit and integration tests, regression validation, acceptance checks
- Tech lead: guardrails, scope control, merge discipline, release readiness
- DevOps/Environment lead: local environment setup, environment variables, deployment support

## 6. Delivery Phases

### Phase 1: Setup and infrastructure
- create repository and branch structure
- create project scaffold under capstone/
- install Python dependencies
- create local PostgreSQL databases and user
- initialize Alembic
- configure environment files and settings
- collect curriculum input files

### Phase 2: Backend and AI foundation
- define database schema and contracts
- implement models and initial migration
- add auth, JWT, and user endpoints
- implement question generation and retrieval pipeline
- implement validation and LangGraph workflow
- add exam scoring and weak-topic analytics

### Phase 3: Frontend and integration
- build Streamlit auth, dashboard, exam, results, teacher, and generate pages
- connect frontend to backend APIs
- verify registration -> login -> exam flow -> results flow
- run end-to-end validation

### Phase 4: Testing, hardening, and deployment
- run unit and integration suites
- fix bugs and optimize performance
- validate coverage and critical flows
- prepare production env vars and deployment files
- deploy backend and frontend
- run migrations and ingest curriculum in production

## 7. Project Structure

```text
AI-Fellows/
├── docs/
│   ├── capstone-proposal.md
│   ├── capstone-requirements.md
│   ├── capstone-architecture.md
│   ├── capstone-technical-design.md
│   ├── capstone-implementation-plan.md
│   └── capstone-development-runbook.md
├── capstone/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── core/
│   │   ├── api/
│   │   │   ├── endpoints/
│   │   │   └── schemas/
│   │   ├── db/
│   │   │   ├── models/
│   │   │   └── session.py
│   │   ├── services/
│   │   ├── agents/
│   │   ├── graph/
│   │   └── rag/
│   ├── frontend/
│   │   ├── streamlit_app.py
│   │   ├── pages/
│   │   └── components/
│   ├── tests/
│   │   ├── unit/
│   │   └── integration/
│   ├── data/curriculum/
│   ├── scripts/
│   ├── alembic/
│   ├── requirements.txt
│   ├── .env.example
│   ├── .env.local
│   ├── alembic.ini
│   ├── pytest.ini
│   └── README.md
├── CONTRIBUTING.md
└── README.md
```

## 8. MVP Acceptance Criteria

The MVP is considered complete when all of the following are true:
- a student can register and log in
- the student can generate an exam with MCQ and numerical questions
- the system validates generated questions before storing them
- the system auto-scores answers using exact match for MCQ and ±5% tolerance for numerical questions
- weak-topic analysis is computed and surfaced to the student
- a teacher can generate questions and view basic statistics
- all critical flows are covered by automated tests
- PostgreSQL test DB is isolated from development data
- local end-to-end workflow passes before production deployment

## 9. Risk and Scope Guardrails

- Do not broaden the project beyond MCQ and numerical question types
- Do not add teacher approval or learning-coach recommendations in the MVP
- Do not depend on the real LLM in unit tests
- Do not proceed to deployment before local validation passes
- Keep the plan aligned with the runbook; if needed, update the runbook only after the plan is adjusted

## 10. Delivery Timeline

### Week 1
- environment and data setup
- PostgreSQL ready
- app scaffold ready
- first health check and DB connection validated

### Week 2
- models and auth complete
- RAG + validation flow working
- question generation and scoring logic in place

### Week 3
- frontend pages complete
- API and frontend connected
- end-to-end exam flow working

### Week 4
- tests complete
- bug fixes and polish
- deployment readiness and final demo

## 11. Document Relationship

- This plan is the product and technical design source of truth.
- The runbook is the execution checklist used to implement the plan.
- If a command, process, or validation gate conflicts with the scope in this plan, the plan wins.
