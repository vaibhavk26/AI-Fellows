# Capstone Project

This folder contains the local scaffold for the capstone MVP.

## Quick start

1. Create a virtual environment.
2. Install dependencies from `requirements.txt`.
3. Copy `.env.example` to `.env.local` and set local values.
4. Ensure PostgreSQL is running and the `capstone` and `capstone_test` databases exist.
5. Run the FastAPI app and verify `/health`.

## Project structure

- `app/`: FastAPI backend
- `frontend/`: Streamlit app
- `tests/`: unit and integration tests
- `data/curriculum/`: PDF and source curriculum files
- `scripts/`: ingestion and maintenance utilities
