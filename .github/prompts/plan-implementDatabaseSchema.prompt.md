## Plan: Implement Database Schema (SQLAlchemy Models + Alembic Migration)

Databases `capstone` and `capstone_test` already exist (empty). Next step is to define SQLAlchemy models matching docs/capstone-database-design.md, properly initialize Alembic (currently `capstone/alembic/` folder is EMPTY despite alembic.ini existing), generate the initial migration for ALL tables (core + extension, per user decision), and apply it to both databases. Seed data (subjects/chapters) will be handled in a LATER separate migration/script, not this one.

**Current state findings**
- `capstone/alembic/` is empty — no `env.py`, no `script.py.mako`, no `versions/`. Needs `alembic init`-equivalent setup, NOT just autogenerate.
- Two conflicting `Base` declarations exist: [app/db/models/base.py](../../capstone/app/db/models/base.py) uses `DeclarativeBase`, while [app/db/session.py](../../capstone/app/db/session.py) creates its own `declarative_base()`. Must consolidate to one `Base` so Alembic autogenerate sees all model metadata.
- [app/db/models/user.py](../../capstone/app/db/models/user.py) is a stub (`int` PK, missing role/is_active/timestamps/full_name) — must be rewritten to match the design (UUID PK, all `users` columns/constraints).
- No other model files exist yet for subjects, chapters, topics, curriculum_documents, source_references, questions, question_source_references, question_validation_results, exams, exam_questions, student_attempts, student_answers, topic_performance, exam_assignments, badges, student_badges, practice_recommendations.
- `pgcrypto` extension is required (`gen_random_uuid()`) — must be enabled in the first migration.

**Steps**

Phase A — Fix foundation (sequential, blocks everything else)
1. Consolidate `Base`: remove the duplicate `declarative_base()` in [app/db/session.py](../../capstone/app/db/session.py); import and reuse the single `Base` from [app/db/models/base.py](../../capstone/app/db/models/base.py). `session.py` keeps only `engine` and `SessionLocal`.
2. Initialize Alembic properly inside `capstone/`: create `alembic/env.py` wired to `Settings().database_url`/`TEST_DATABASE_URL` (env override for test runs), `alembic/script.py.mako`, and `alembic/versions/` directory. `env.py` must import `app.db.models.base.Base` plus every model module (so `target_metadata = Base.metadata` sees all tables) and support both offline/online migration modes.

Phase B — Implement SQLAlchemy models (depends on Phase A; can be done file-by-file, but all needed before autogenerate)
3. Add one model module per entity group under `app/db/models/`, matching column types, defaults, checks, uniques and FKs exactly as specified in section 6/22 of [capstone-database-design.md](../../docs/capstone-database-design.md):
   - `user.py`: `User`, `StudentProfile`, `TeacherProfile` (rewrite `User`; add the two profile tables, 1:1 via shared PK/FK).
   - `curriculum.py`: `Subject`, `Chapter`, `Topic`, `CurriculumDocument`, `SourceReference`.
   - `question.py`: `Question`, `QuestionSourceReference`, `QuestionValidationResult` (include the `ck_questions_options_shape` and `ck_qvr_status_checks` raw-SQL `CheckConstraint`s).
   - `exam.py`: `Exam`, `ExamQuestion`.
   - `attempt.py`: `StudentAttempt` (incl. partial unique index `uq_student_attempts_active`), `StudentAnswer`.
   - `analytics.py`: `TopicPerformance`.
   - `extensions.py`: `ExamAssignment`, `Badge`, `StudentBadge`, `PracticeRecommendation`.
   - Use `UUID(as_uuid=True)` with `server_default=text("gen_random_uuid()")` for all `id` PKs; `TIMESTAMP(timezone=True)` with `server_default=func.now()` for timestamps; `JSONB` for `options`/`question_types`/`failure_reasons`.
   - Update `app/db/models/__init__.py` to import all model modules (ensures Alembic metadata discovery).

Phase C — Generate & review migration (depends on Phase B)
4. Add a small standalone migration (or a leading step inside the first revision) that runs `CREATE EXTENSION IF NOT EXISTS pgcrypto;` before table creation.
5. Run `alembic revision --autogenerate -m "Initial MVP schema"` from `capstone/` and manually review/edit the generated script against section 22 DDL — autogenerate will miss: JSONB check constraints, the partial unique index (`postgresql_where`), and the `pgcrypto` extension. Add these by hand in the migration's `upgrade()`/`downgrade()`.
6. Do NOT add seed-data inserts in this migration (per decision) — leave subjects/chapters seeding for a later, separate migration or `scripts/ingest_curriculum.py`.

Phase D — Apply and verify (depends on Phase C)
7. Run `alembic upgrade head` against `capstone` (default `DATABASE_URL`), then temporarily point `DATABASE_URL`/alembic config at `capstone_test` and run `alembic upgrade head` again; restore the dev URL afterward — per runbook section 9.
8. Verify via `psql` (`\dt`, `\d+ questions`, etc.) that all tables, constraints, and indexes from section 6/12/22 exist in both databases.
9. Restart `uvicorn app.main:app --reload` and confirm `/health` still returns 200 (per runbook section 8) to ensure the app boots with the updated `Base`/models.

**Relevant files**
- `capstone/app/db/models/base.py` — shared `Base`, keep as single source of declarative metadata.
- `capstone/app/db/session.py` — remove duplicate `declarative_base()`.
- `capstone/app/db/models/user.py` — rewrite `User`, add `StudentProfile`/`TeacherProfile`.
- `capstone/app/db/models/__init__.py` — import all new model modules.
- `capstone/alembic/` (currently empty) — needs `env.py`, `script.py.mako`, `versions/`.
- `capstone/alembic.ini` — already has `sqlalchemy.url`; may parametrize via `app.core.config.get_settings()` in `env.py` instead of hardcoding.
- `docs/capstone-database-design.md` — authoritative schema/DDL reference (section 22).
- `docs/capstone-development-runbook.md` — section 9 (migration sequence), section 16 (completion gate).

**Verification**
1. `alembic upgrade head` succeeds with no errors against both `capstone` and `capstone_test`.
2. `psql -U capstone_user -d capstone -c "\dt"` lists all ~18 tables (14 core/MVP + 4 extension).
3. `psql -U capstone_user -d capstone -c "\d questions"` shows the `ck_questions_options_shape` constraint and all listed columns.
4. `uvicorn app.main:app --reload` starts; `Invoke-RestMethod http://localhost:8000/health` returns `status: ok`.
5. `pytest tests/unit -v` still passes (existing health test unaffected by model changes).

**Decisions**
- Extension tables (`exam_assignments`, `badges`, `student_badges`, `practice_recommendations`) ARE included in this initial migration.
- Seed data (subjects/chapters) is explicitly EXCLUDED from this migration; deferred to a later migration/script.
- Cross-table hierarchy checks (chapter belongs to subject, topic belongs to chapter) and MCQ option-key validation stay in application/service/Pydantic layer, not DB constraints — per design section 22 closing note.

**Further Considerations**
1. Alembic `env.py` should read `TEST_DATABASE_URL` via an environment variable/flag (e.g. `ALEMBIC_TARGET=test`) so the runbook's manual `$env:DATABASE_URL=$env:TEST_DATABASE_URL` swap isn't error-prone — recommend adding this convenience now rather than relying purely on manual env var swaps.
