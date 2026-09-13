# Capstone Project

This folder contains the Capstone MVP: a FastAPI backend, Streamlit frontend, PostgreSQL persistence, FAISS curriculum retrieval, and Groq-backed question generation.

## Setup

Follow [SETUP.md](SETUP.md) for the canonical local setup sequence, including the virtual environment, environment variables, PostgreSQL databases, migrations, curriculum ingestion, both application servers, backend tests, and browser tests. For Windows PostgreSQL troubleshooting, see [docs/capstone-local-postgresql-setup.md](../docs/capstone-local-postgresql-setup.md).

The short sequence is:

1. From `capstone/`, create `.venv` and install `requirements.txt`.
2. Create `.env.local`, PostgreSQL databases, and apply Alembic migrations.
3. Add readable Physics and Mathematics PDFs and run `python -m scripts.ingest_curriculum --all`.
4. Start FastAPI on port `8000` and Streamlit on port `8501`.
5. Open http://localhost:8501 and register a student or teacher account.

## Current status

The MVP includes authentication, curriculum browsing, question retrieval and teacher-only generation, exams with generation fallback, attempts, scoring, analytics, curriculum ingestion, FAISS retrieval, and Streamlit workflows for students and teachers. The automated suite currently contains 66 tests, including 9 browser tests. Teacher generation and generation fallback require a valid `GROQ_API_KEY`; deterministic tests do not.

## Project structure

- `app/`: FastAPI backend
- `frontend/`: Streamlit app
- `tests/`: unit and integration tests
- `data/curriculum/`: Physics and Mathematics curriculum PDFs
- `scripts/`: ingestion and maintenance utilities; run `python -m scripts.ingest_curriculum --all` after adding PDFs
