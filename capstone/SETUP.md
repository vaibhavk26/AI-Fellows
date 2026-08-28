# Setup Guide

## Local environment

```powershell
cd .\capstone
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Environment variables

Copy `.env.example` to `.env.local` and configure the values for the local PostgreSQL and LLM setup.

## Database setup
'''Start PostgreSQL
'''Open PowerShell as Administrator:
Get-Service *postgres*

'''Find the service name, such as postgresql-x64-18, then start it:
Start-Service postgresql-x64-18

'''Open PostgreSQL’s SQL shell. Enter password set at the time of database creation when prompted to enter password.
psql -U postgres -h localhost

```sql
CREATE USER capstone_user WITH PASSWORD 'replace-local-password';
CREATE DATABASE capstone OWNER capstone_user;
CREATE DATABASE capstone_test OWNER capstone_user;
```

## Database migrations

Run this after every `git pull` that changes `alembic/versions/` — each teammate applies migrations to their own local databases; migrations are not shared by pulling code alone.

```powershell
alembic upgrade head
```

Then apply the same migrations to the test database:

```powershell
$env:DATABASE_URL = $env:TEST_DATABASE_URL
alembic upgrade head
Remove-Item Env:\DATABASE_URL
```

Requires `capstone` and `capstone_test` to already exist (see Database setup above) and `.env.local` to be configured with valid `DATABASE_URL`/`TEST_DATABASE_URL` values.

## Seed reference data

Run this after migrations, against both `capstone` and `capstone_test`, before curriculum ingestion. It is idempotent and safe to re-run.

```powershell
python -m scripts.seed_reference_data
$env:DATABASE_URL = $env:TEST_DATABASE_URL
python -m scripts.seed_reference_data
Remove-Item Env:\DATABASE_URL
```

Verify the seed data landed correctly (repeat with `-d capstone_test` for the test database):

```powershell
psql -U capstone_user -d capstone -c "SELECT (SELECT count(*) FROM subjects) AS subjects, (SELECT count(*) FROM chapters) AS chapters;"
```

Expect `subjects = 2` and `chapters = 7`. Alternatively, verify via SQLAlchemy without `psql`:

```powershell
python -c "from app.db.session import SessionLocal; from app.db.models.curriculum import Subject, Chapter; s = SessionLocal(); [print(sub.name, sub.class_level, [c.name for c in s.query(Chapter).filter_by(subject_id=sub.id).order_by(Chapter.display_order)]) for sub in s.query(Subject).all()]; s.close()"
```

## Run app

```powershell
uvicorn app.main:app --reload --port 8000
```

