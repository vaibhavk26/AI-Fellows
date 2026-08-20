Updated todo list

I’ll assess the plan as an implementation handoff, focusing on whether an AI coding tool has enough concrete contracts to scaffold safely and which few decisions would still cause rework.

Read , lines 1 to 180

Read , lines 180 to 390

Read , lines 390 to 566

## Assessment

The plan is ready to feed to an AI coding tool for **Phase 1 scaffolding and repository setup**. It is not yet detailed enough for reliable end-to-end feature implementation without clarifying a few contracts first.

### Safe to Start Now

The AI tool can immediately generate:

- `capstone/` directory structure
- Python packages and `__init__.py` files
- `requirements.txt`
- `.env.example`
- FastAPI app skeleton
- Streamlit app skeleton
- SQLAlchemy session setup
- Alembic configuration
- pytest configuration
- FAISS ingestion scaffolding
- basic health-check endpoint
- placeholder services, agents, and repositories

Use the AI tool in small phases. Do not ask it to build the entire application in one prompt.

## Required Before Feature Coding

### 1. Database decision: PostgreSQL throughout

The team has decided to use PostgreSQL locally, for integration tests, and in production. This keeps development and production behavior aligned and avoids database-dialect differences during the four-week implementation.

### 2. Define the API contract

The plan lists endpoints, but not complete request and response payloads. Create `API_DESIGN.md` before asking the AI tool to implement endpoints.

It should define:

- Request fields and types
- Response fields and types
- Authentication requirements
- HTTP status codes
- Error response format
- Pagination and filtering behavior
- Numerical-answer tolerance behavior
- Question validation status values

For example, the question lifecycle is now:

```text
generated → validated
generated → rejected
```

There is no teacher approval step in the MVP.

### 3. Define the database schema in more detail

The plan lists models but not enough field-level detail. Before model implementation, specify:

- Primary keys
- Foreign keys
- Required and nullable fields
- Enum values
- Relationships
- Timestamps
- Unique constraints
- Cascade behavior

The most important MVP entities are:

```text
User
Question
Exam
ExamQuestion
StudentAttempt
StudentAnswer
TopicPerformance
```

The `Subject`, `Chapter`, and `Topic` hierarchy also needs to be represented either as database tables or as controlled seed data. The plan currently refers to subjects, chapters, and topics without explicitly defining their persistence model.

### 4. Choose the LLM provider and model

The plan includes `langchain-openai` and `OPENAI_API_KEY`, but it does not specify:

- Model name
- API endpoint format
- Structured-output support
- Token limits
- Timeout and retry behavior
- Mock behavior for tests

Add something like:

```text
LLM provider: OpenAI-compatible API
MVP model: <specific model name>
Structured output: Pydantic schema
Tests: mocked LLM responses, no API calls in unit tests
```

Without this, an AI coding tool may invent incompatible client code.

### 5. Create the missing project documentation before parallel work

The plan references these files:

- `docs/TEAM_ROLES.md`
- `docs/SETUP.md`
- `docs/API_DESIGN.md`

They should be created before multiple developers or AI agents work in parallel. In particular:

- `TEAM_ROLES.md` prevents overlapping edits.
- `SETUP.md` standardizes commands and environment variables.
- `API_DESIGN.md` prevents backend and frontend contract drift.

### 6. Align the plan with the current repository layout

The current workspace has the reference Markdown files at the repository root, while the plan’s target structure places them under `docs/`.

Decide whether to:

- Move the existing documents into `docs/`, or
- Keep them at the root and update the plan accordingly.

This should be settled before scaffolding so the AI tool does not create a second competing documentation structure.

### 7. Fix the Alembic location and command context

The plan says to run:

```bash
alembic init alembic
```

but the application code lives under `capstone/`. Define where Alembic runs from and where `alembic.ini` lives.

Recommended structure:

```text
capstone/
├── alembic/
├── alembic.ini
├── app/
└── requirements.txt
```

Then run all database commands from `capstone/`:

```powershell
cd capstone
alembic upgrade head
```

### 8. Define test database behavior

Tests should use the dedicated PostgreSQL test database `capstone_test`.

Also define:

- Fixture setup and teardown
- Database reset strategy
- Whether LLM calls are always mocked
- Whether FAISS uses a temporary test index

LLM calls should be mocked in unit tests, and FAISS should use a temporary test index where retrieval tests need an isolated store.

## Recommended Coding Sequence

Feed the plan to the AI tool in this order:

1. **Repository scaffolding**
   - Create folders, packages, configuration, and placeholder modules.

2. **Environment and application bootstrap**
   - Settings, database session, FastAPI health check, Streamlit entry point.

3. **Database models and migrations**
   - Implement the seven MVP entities.
   - Generate and test the initial migration.

4. **API schemas and authentication**
   - Implement Pydantic schemas first.
   - Then JWT authentication and registration/login endpoints.

5. **RAG ingestion**
   - Add curriculum files.
   - Build ingestion, chunking, embeddings, and FAISS retrieval.
   - Verify retrieval before integrating the LLM.

6. **Question generation and validation**
   - Implement only MCQ and Numerical questions.
   - Use mocked LLM responses in tests.

7. **Exam and analytics APIs**
   - Create exam, submit answers, calculate scores, identify weak topics.

8. **Streamlit integration**
   - Build the five agreed pages against the API contracts.

9. **End-to-end testing**
   - Register → login → generate exam → submit → view results.

10. **Deployment**
   - Only after the complete local flow works.

## Final Recommendation

You can start coding now, but use the AI tool for **scaffolding and Phase 1 only**. Before generating database models, API endpoints, or frontend workflows, complete these four items:

1. Create `API_DESIGN.md`.
2. Define the database fields and relationships.
3. Specify the LLM provider and model.

The plan is a strong execution roadmap, but those four items are the implementation contracts. Without them, the AI tool will make assumptions that are likely to create rework across the backend, frontend, and tests.