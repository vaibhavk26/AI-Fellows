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

The MVP includes authentication, curriculum browsing, question retrieval and teacher-only generation, exams with generation fallback, attempts, scoring, analytics, curriculum ingestion, FAISS retrieval, and Streamlit workflows for students and teachers. Curriculum routes use async FastAPI handlers, while the Streamlit frontend uses cached reads and background loading for chained selectors. Teacher generation and generation fallback require a valid `GROQ_API_KEY`; deterministic tests do not.

## Frontend caching note

The Streamlit frontend follows a cache-first pattern for repeated data fetches. Use `@st.cache_data` for read-heavy API results and reuse cached values across reruns instead of triggering fresh requests for the same subject, chapter, topic, attempts, or dashboard data. When a parent selection changes, load only the dependent child data, and keep parent/child selection state in `st.session_state` so the UI stays responsive and does not refetch the same payloads repeatedly. Chained curriculum loads use a shared `ThreadPoolExecutor` helper; keep the generation and exam forms usable while child data is still loading, and validate the selected child before submitting.

For browser tests, install the Playwright browser binary once after installing Python dependencies:

```powershell
.\.venv\Scripts\python.exe -m playwright install chromium
```

## Project structure

- `app/`: FastAPI backend
- `frontend/`: Streamlit app
- `tests/`: unit and integration tests
- `data/curriculum/`: Physics and Mathematics curriculum PDFs
- `scripts/`: ingestion and maintenance utilities; run `python -m scripts.ingest_curriculum --all` after adding PDFs
