from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    app_name: str = "capstone"
    environment: str = "development"
    debug: bool = True
    allow_teacher_signup: bool | None = None
    database_url: str = "postgresql+psycopg2://capstone_user:password@localhost:5432/capstone"
    test_database_url: str = "postgresql+psycopg2://capstone_user:password@localhost:5432/capstone_test"
    vector_db_type: str = "faiss"
    vector_db_path: str = str(BASE_DIR / "vectors")
    llm_provider: str = "groq"
    llm_model: str = "openai/gpt-oss-20b"
    llm_base_url: str = "https://api.groq.com/openai/v1"
    llm_timeout_seconds: float = 45.0
    llm_max_tokens: int = 8192
    llm_temperature: float = 0.7
    groq_api_key: str | None = None
    jwt_secret_key: str = "your-secret-key-change-in-production"

    model_config = SettingsConfigDict(env_file=".env.local", extra="ignore")

    @property
    def teacher_signup_enabled(self) -> bool:
        """Allow teacher signup explicitly, or default off in production."""
        if self.allow_teacher_signup is not None:
            return self.allow_teacher_signup
        return self.environment.strip().lower() not in {"prod", "production"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
