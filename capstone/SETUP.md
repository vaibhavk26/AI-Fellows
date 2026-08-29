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

## Authentication and Authorization

Section 10.1 Authentication Foundation is complete. All authentication is handled automatically by the FastAPI backend:

### Key Implementation Details

- **JWT Tokens**: 60-minute expiration via `python-jose==3.3.0` with HS256 algorithm
- **Password Hashing**: Bcrypt via `passlib==1.7.4` (never stored or returned in API responses)
- **Email Validation**: Required field using `email-validator==2.3.0`
- **Timezone Safety**: All JWT token timestamps use `datetime.now(timezone.utc)` for correct handling across all developer timezones (UTC, IST, PST, etc.). No manual timezone configuration needed.
- **Role-Based Access**: Automatic role checking (student/teacher) at endpoint dependencies

### Environment Configuration

The `JWT_SECRET_KEY` in `.env.local` is loaded automatically from `app/core/config.py`. Default:
```
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production-12345678
```

For production, regenerate a strong secret key.

### Endpoints

- `POST /api/v1/auth/register` — Student or teacher registration
- `POST /api/v1/auth/login` — Returns JWT access token (60-minute expiration)
- `POST /api/v1/auth/logout` — Client-side logout (no token blacklist in MVP)
- `GET /api/v1/auth/me` — Current user info (requires Bearer token)

### Testing

All auth endpoints have 10 integration tests in `tests/integration/test_auth_integration.py`, all passing. To run:

```powershell
python -m pytest tests/integration/test_auth_integration.py -v
```

