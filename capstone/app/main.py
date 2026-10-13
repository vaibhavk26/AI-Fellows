import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.endpoints import analytics, auth, curriculum, exams, questions, teachers

app = FastAPI(title="Capstone API", version="0.1.0")

# Origins allowed to call the API from a browser (the React app). Comma-separated.
_cors_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(curriculum.router)
app.include_router(questions.router)
app.include_router(exams.router)
app.include_router(analytics.router)
app.include_router(analytics.teacher_router)
app.include_router(teachers.router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
