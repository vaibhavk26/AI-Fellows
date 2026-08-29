# Capstone Project

This folder contains the local scaffold for the capstone MVP.

## Quick start

1. Create a virtual environment.
2. Install dependencies from `requirements.txt` (includes Python-jose, passlib, bcrypt, and email-validator).
3. Copy `.env.example` to `.env.local` and set local values (ensure `JWT_SECRET_KEY` is configured).
4. Ensure PostgreSQL is running and the `capstone` and `capstone_test` databases exist.
5. Run database migrations: `alembic upgrade head`
6. Seed reference data: `python -m scripts.seed_reference_data`
7. Run the FastAPI app: `uvicorn app.main:app --reload`
8. Verify `/health` endpoint returns HTTP 200

## Project structure

- `app/`: FastAPI backend
- `frontend/`: Streamlit app
- `tests/`: unit and integration tests
- `data/curriculum/`: PDF and source curriculum files
- `scripts/`: ingestion and maintenance utilities
