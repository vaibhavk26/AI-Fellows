# Capstone Project

This folder contains the Capstone MVP: a FastAPI backend, React (Vite + TypeScript + Tailwind) frontend, PostgreSQL persistence, FAISS curriculum retrieval, and Groq-backed question generation.

## Setup

Follow [SETUP.md](SETUP.md) for the canonical local setup sequence, including the virtual environment, environment variables, PostgreSQL databases, migrations, curriculum ingestion, both application servers, backend tests, and browser tests. For Windows PostgreSQL troubleshooting, see [docs/capstone-local-postgresql-setup.md](../docs/capstone-local-postgresql-setup.md).

The short sequence is:

1. From `capstone/`, create `.venv` and install `requirements.txt`.
2. Create `.env.local`, PostgreSQL databases, and apply Alembic migrations.
3. Add readable Physics and Mathematics PDFs and run `python -m scripts.ingest_curriculum --all`.
4. Start FastAPI on port `8000`, then run `npm install && npm run dev` in `web/` (port `5173`).
5. Open http://localhost:5173 and register a student or teacher account.

## Current status

The current implementation includes authentication, curriculum browsing, teacher-only question generation and question-bank access, student practice exams, teacher-owned rosters and exam assignments, attempt scoring, student analytics, and teacher assignment/completion/score analytics. Curriculum ingestion and FAISS retrieval support question generation. Curriculum routes use async FastAPI handlers, while the React frontend loads chained selectors on demand. Teacher generation and generation fallback require a valid `GROQ_API_KEY`; deterministic tests do not.

## Frontend

The UI lives in `web/` (React, Vite, TypeScript, Tailwind) and consumes the FastAPI backend.

For browser tests, install the Playwright browser binary once after installing Python dependencies:

```powershell
.\.venv\Scripts\python.exe -m playwright install chromium
```

## Project structure

- `app/`: FastAPI backend
- `web/`: React app (see [web/README.md](web/README.md))
- `tests/`: unit and integration tests
- `data/curriculum/`: Physics and Mathematics curriculum PDFs
- `scripts/`: ingestion and maintenance utilities; run `python -m scripts.ingest_curriculum --all` after adding PDFs
