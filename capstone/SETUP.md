# Setup Guide

## Local environment

```powershell
cd .\capstone
python -m venv .venv
.\.venv\Scripts\Activate.ps1
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Environment variables

Copy `.env.example` to `.env.local` and configure the local PostgreSQL and JWT values. `LLM_PROVIDER`, `LLM_MODEL`, and `OPENAI_API_KEY` may retain their placeholders until the Section 10.3 generation workflow is implemented; the current tests do not call an LLM.

## Database setup

Start PostgreSQL from an elevated PowerShell window:

```powershell
Get-Service *postgres*
Start-Service postgresql-x64-18
```

Replace `postgresql-x64-18` with the service name returned by `Get-Service`. Then open PostgreSQL's SQL shell and enter the administrator password when prompted:

```powershell
psql -U postgres -h localhost
```

```sql
CREATE USER capstone_user WITH PASSWORD 'replace-local-password';
CREATE DATABASE capstone OWNER capstone_user;
CREATE DATABASE capstone_test OWNER capstone_user;
```

## Database migrations

Run this after every `git pull` that changes `alembic/versions/` — each teammate applies migrations to their own local databases; migrations are not shared by pulling code alone.

```powershell
.\.venv\Scripts\alembic.exe upgrade head
```

Then apply the same migrations to the test database:

```powershell
$env:DATABASE_URL = $env:TEST_DATABASE_URL
.\.venv\Scripts\alembic.exe upgrade head
Remove-Item Env:\DATABASE_URL
```

Requires `capstone` and `capstone_test` to already exist (see Database setup above) and `.env.local` to be configured with valid `DATABASE_URL`/`TEST_DATABASE_URL` values.

## Temporary sample curriculum data

The following script creates sample Subjects and Chapters for local backend development and Section 10.2 tests. It is optional and is not used to classify production curriculum. Section 10.3 ingestion discovers and persists the authoritative curriculum hierarchy from the supplied PDFs.

```powershell
.\.venv\Scripts\python.exe -m scripts.seed_reference_data
$env:DATABASE_URL = $env:TEST_DATABASE_URL
.\.venv\Scripts\python.exe -m scripts.seed_reference_data
Remove-Item Env:\DATABASE_URL
```

Verify sample data only when you need it for local backend testing (repeat with `-d capstone_test` for the test database):

```powershell
psql -U capstone_user -d capstone -c "SELECT (SELECT count(*) FROM subjects) AS subjects, (SELECT count(*) FROM chapters) AS chapters;"
```

Alternatively, inspect the temporary rows via SQLAlchemy without `psql`:

```powershell
.\.venv\Scripts\python.exe -c "from app.db.session import SessionLocal; from app.db.models.curriculum import Subject, Chapter; s = SessionLocal(); [print(sub.name, sub.class_level, [c.name for c in s.query(Chapter).filter_by(subject_id=sub.id).order_by(Chapter.display_order)]) for sub in s.query(Subject).all()]; s.close()"
```

## Curriculum PDFs

For Section 10.3, place one text-readable PDF per subject in this directory:

```text
data/curriculum/
	physics.pdf
	mathematics.pdf
```

Do not split PDFs by chapter or prepare chapter/topic mappings. Ingestion will discover the document hierarchy, persist the resulting Subjects, Chapters, and Topics, then associate source chunks and FAISS vectors with the discovered records. Image-only/scanned PDFs require OCR, which is not part of the current `pypdf` ingestion scope.

## Run app

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
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

#### Generating JWT_SECRET_KEY

The default placeholder is acceptable for **local development only**. For any shared environment (staging, production, or team dev), generate a cryptographically secure key.

**Option 1: Python (Recommended)**
```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Option 2: OpenSSL**
```powershell
openssl rand -base64 32
```

**Option 3: Python token_hex**
```powershell
python -c "from secrets import token_hex; print(token_hex(32))"
```

Copy the generated key (without quotes) and update `.env.local`:
```env
JWT_SECRET_KEY=<paste-generated-key-here>
```

**For production deployments:**
- Generate a fresh key using one of the above methods
- Store in a secrets manager (AWS Secrets Manager, HashiCorp Vault, Kubernetes Secrets, etc.)
- Never commit keys to version control
- Rotate periodically (note: this invalidates existing tokens)

### Endpoints

- `POST /api/v1/auth/register` — Student or teacher registration
- `POST /api/v1/auth/login` — Returns JWT access token (60-minute expiration)
- `POST /api/v1/auth/logout` — Client-side logout (no token blacklist in MVP)
- `GET /api/v1/auth/me` — Current user info (requires Bearer token)

### Testing

Run the complete suite using the project interpreter:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/ -v
```

The current suite has 15 tests. Section 10.2 coverage is in `tests/integration/test_question_exam_analytics_integration.py` and `tests/unit/test_exam_scoring.py`; it uses deterministic PostgreSQL fixtures and does not call an LLM or FAISS.

Question retrieval, exams, attempts, scoring, and analytics are available. `POST /api/v1/questions/generate` intentionally returns `501 Not Implemented` until the RAG and LangGraph generation workflow is completed in Section 10.3.

