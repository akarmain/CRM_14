from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Leetbook API"
    database_url: str = "sqlite+aiosqlite:///./data/app.db"
    cors_origins: str = "*"
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


def _ensure_sqlite_directory(database_url: str) -> None:
    url = make_url(database_url)
    if not url.get_backend_name().startswith("sqlite"):
        return
    if not url.database or url.database == ":memory:":
        return
    path = Path(url.database)
    if not path.is_absolute():
        path = Path.cwd() / path
    path.parent.mkdir(parents=True, exist_ok=True)


settings = Settings()
_ensure_sqlite_directory(settings.database_url)
