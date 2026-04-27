from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    storage_mode: Literal["postgres", "memo", "1c"] = "postgres"
    database_url: str = "postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/mini_crm_simple"
    log_level: str = "INFO"
    session_secret: str = "mini-crm-simple-dev-secret"
    cors_allowed_origins: str = ",".join([
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ])
    session_https_only: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
