from fastapi import FastAPI

from app.api.endpoints import auth

app = FastAPI(title="Capstone API", version="0.1.0")

# Include routers
app.include_router(auth.router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
