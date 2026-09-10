# Capstone Project

This folder contains the local scaffold for the capstone MVP.

## Setup

Follow [SETUP.md](SETUP.md) for the complete local setup sequence, including the virtual environment, environment variables, PostgreSQL databases, migrations, curriculum ingestion, application startup, and tests.

The short sequence is:

1. Create the virtual environment and install `requirements.txt`.
2. Configure `.env.local` and PostgreSQL using [SETUP.md](SETUP.md).
3. Add the Physics and Mathematics PDFs and run `python -m scripts.ingest_curriculum --all`.
4. Start FastAPI and verify `/health`.

## Current status

The backend includes authentication, question retrieval and generation, exams with generation fallback, attempts, scoring, analytics, curriculum ingestion, and FAISS retrieval. The teacher-only `POST /api/v1/questions/generate` endpoint uses the LangGraph generation and validation workflow.

## Project structure

- `app/`: FastAPI backend
- `frontend/`: Streamlit app
- `tests/`: unit and integration tests
- `data/curriculum/`: Physics and Mathematics curriculum PDFs
- `scripts/`: ingestion and maintenance utilities; run `python -m scripts.ingest_curriculum --all` after adding PDFs
