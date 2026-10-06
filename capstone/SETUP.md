# Setup Guide

This is the canonical local setup path for Windows PowerShell. Run commands from the `capstone/` directory unless noted otherwise.

## Prerequisites

- Python 3.11 and PostgreSQL (see the database section below).
- **Node.js 20 or newer and npm** for the React UI in `web/` (tested with Node 24). Check with `node -v`.
- Groq API key for question generation (optional for browsing and tests).

## Local environment

```powershell
cd .\capstone
python -m venv .venv
.\.venv\Scripts\Activate.ps1
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Activation is optional. If PowerShell blocks `Activate.ps1`, use the explicit `\.venv\Scripts\python.exe` path shown in every command.

## Environment variables

Copy `.env.example` to `.env.local` and edit the local PostgreSQL, JWT, vector-store, and Groq values:

```powershell
Copy-Item .env.example .env.local
notepad .env.local
```

Step 8 generation uses Groq through its OpenAI-compatible endpoint. Set `LLM_PROVIDER=groq`, `LLM_MODEL`, `LLM_BASE_URL=https://api.groq.com/openai/v1`, `LLM_TIMEOUT_SECONDS=45`, and `GROQ_API_KEY`; never commit `.env.local` or API keys. Tests use mocked models and do not call Groq. If the PostgreSQL password contains URL characters such as `@`, `:`, `/`, or `#`, URL-encode it in both connection strings.

## Database setup

Start PostgreSQL from an elevated PowerShell window. The service name varies by installed PostgreSQL version:

```powershell
Get-Service *postgres*
Get-Service postgresql* | Where-Object Status -eq 'Stopped' | Start-Service
```

Then open PostgreSQL's SQL shell and enter the administrator password when prompted:

```powershell
psql -U postgres -h localhost
```

```sql
CREATE USER capstone_user WITH PASSWORD 'replace-local-password';
CREATE DATABASE capstone OWNER capstone_user;
CREATE DATABASE capstone_test OWNER capstone_user;
```

If the user or databases already exist, skip the `CREATE` statements and continue with migrations.

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

The temporary `DATABASE_URL` override makes Alembic target `capstone_test`; removing it restores the development database setting.

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

Run the complete ingestion process from `capstone/`:

```powershell
.\.venv\Scripts\python.exe -m scripts.ingest_curriculum --all
```

The first run downloads the local `all-MiniLM-L6-v2` embedding model if it is not already cached. The resulting FAISS index and its `curriculum.metadata.json` metadata sidecar are stored in `VECTOR_DB_PATH`. Re-running the same PDF content is idempotent. To rebuild a stale or damaged FAISS index from unchanged PDFs and their existing PostgreSQL source references, use `--rebuild`:

```powershell
.\.venv\Scripts\python.exe -m scripts.ingest_curriculum --all --rebuild
```

This rebuild replaces only the FAISS index and metadata; PostgreSQL source-reference IDs and question citations are preserved. It verifies that PDF hashes and chunk locations match persisted records and refuses changed PDF content. Source-content replacement requires a separate reingestion process.

To ingest one PDF explicitly:

```powershell
.\.venv\Scripts\python.exe -m scripts.ingest_curriculum --pdf .\data\curriculum\physics.pdf --subject Physics
```

## Run app

Start FastAPI in one terminal:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

Verify it from a second terminal:

```powershell
Invoke-RestMethod -Uri http://localhost:8000/health -Method Get
```

Expected output is `status: ok`. 

Start the React app in a third terminal:

```powershell
cd web
npm install
npm run dev
```

The React app calls the API at `http://localhost:8000` by default, and the API allows the Vite origin (`http://localhost:5173`) through CORS, so no extra configuration is needed locally. To point the UI at a different API, create `web/.env.local` with `VITE_API_BASE_URL=<url>` and set `CORS_ORIGINS` on the API to the UI's origin. See [web/README.md](web/README.md).

The Streamlit UI has been retired, so `requirements.txt` no longer includes Streamlit. React dependencies live in `web/package.json` and are installed by `npm install`; re-run it after pulling changes.

Open the app at http://localhost:5173, API docs at http://localhost:8000/docs, and ReDoc at http://localhost:8000/redoc.

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

The current suite collects 89 tests: 48 unit, 25 integration, and 16 Playwright browser tests. Backend coverage is in `tests/unit/` and `tests/integration/`; browser coverage is in `tests/e2e/test_react_browser.py`. Backend tests use mocked LLM responses and do not call Groq or require a live API key.

Run the suite with coverage:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests --cov=app --cov-report=term-missing
```

## Frontend browser tests

The Playwright suite exercises authentication, role restrictions, dashboard/results states, teacher question-bank and generation controls, roster-based exam assignment, assigned-student completion, empty-bank handling, MCQ submission, numerical submission, and a three-question student exam flow. Assignment E2E coverage uses the configured teacher account and requires at least three validated easy MCQs in one chapter. Install the browser binary once:

```powershell
.\.venv\Scripts\python.exe -m playwright install chromium
```

Start FastAPI and the React dev server (`npm run dev` in `web/`) in separate terminals. Add the email and password for a teacher account with at least three validated easy MCQs in one chapter to `.env.local`:

```env
E2E_TEACHER_EMAIL=teacher@example.com
E2E_TEACHER_PASSWORD=replace-with-password
```

The E2E fixtures load these values from `.env.local`; process environment variables with the same names take precedence. Then run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/e2e -m e2e -q
```

The browser tests create temporary users. Populated-bank tests use the configured teacher account and require at least three validated easy MCQs in one chapter. Override `E2E_API_URL` or `E2E_WEB_URL` when services use non-default ports.

Numerical generation requires a safe `formula` and `quantities` response. If Groq omits those fields, the service retries once. If the retry is missing, unsafe, or mathematically inconsistent, the question is stored as `rejected`. Calculation details are internal and are not added to the database schema or API response.

Question retrieval, exams, attempts, scoring, student analytics, teacher roster management, teacher-owned exam assignment, assignment-based teacher analytics, curriculum ingestion/retrieval, and the teacher-only LangGraph question-generation workflow are available. `POST /api/v1/questions/generate` returns `201` on successful generation, validation, and persistence; provider or vector-store failures return `503` without saving a partial batch.

