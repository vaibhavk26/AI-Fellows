# ExamIQ web (React)

Modern React client for the existing FastAPI backend. The legacy Streamlit app has been retired; this is the project's UI.

```powershell
npm install
npm run dev        # http://localhost:5173 (backend on :8000)
npm test           # unit tests
npm run build      # type-check + production build
```

Environment (optional, `.env.local`):

| Variable | Default | Purpose |
|---|---|---|
| `VITE_API_BASE_URL` | `http://localhost:8000` | Backend URL |
| `VITE_ALLOW_TEACHER_SIGNUP` | on in dev, off in prod build | Show teacher option on signup |

Backend CORS origins are set with `CORS_ORIGINS` (comma-separated, defaults to the Vite dev origin).

## Migration status

- Done: sign in / sign up, student Home (XP, level, streak, badges, assigned quests), Progress dashboard
- Done: Exam (setup, timed runner, submit), Results review, Teacher console (hub, roster, assessments, question bank) and Generate
- Migration complete: all screens ported, Playwright e2e ported, Streamlit retired

## E2E tests

With the API (:8000) and `npm run dev` (:5173) running: `python -m pytest tests/e2e/test_react_browser.py -m e2e`. Override the URL with `E2E_WEB_URL`. Tests needing a populated bank also need `E2E_TEACHER_EMAIL` / `E2E_TEACHER_PASSWORD`.

## Exam experience
A 3-2-1 countdown precedes each exam (skipped with reduced motion), and the runner offers a Focus mode (desktop) that hides navigation. A read-only profile page is at `/profile`; the teacher hub shows class insights derived from existing dashboard data.
