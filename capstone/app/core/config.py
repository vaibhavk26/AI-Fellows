from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    app_name: str = "capstone"
    environment: str = "development"
    debug: bool = True
    database_url: str = "postgresql+psycopg2://capstone_user:password@localhost:5432/capstone"
    test_database_url: str = "postgresql+psycopg2://capstone_user:password@localhost:5432/capstone_test"
    vector_db_type: str = "faiss"
    vector_db_path: str = str(BASE_DIR / "vectors")
    llm_provider: str = "groq"
    llm_model: str = "llama-3.3-70b-versatile"
    llm_base_url: str = "https://api.groq.com/openai/v1"
    groq_api_key: str | None = None
    jwt_secret_key: str = "your-secret-key-change-in-production"

    model_config = SettingsConfigDict(env_file=".env.local", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
