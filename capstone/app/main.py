from fastapi import FastAPI

from app.api.endpoints import analytics, auth, exams, questions

app = FastAPI(title="Capstone API", version="0.1.0")

# Include routers
app.include_router(auth.router)
app.include_router(questions.router)
app.include_router(exams.router)
app.include_router(analytics.router)
app.include_router(analytics.teacher_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
