"""Application settings (environment variables, prefix ``SMIT_``)."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SMIT_", env_file=str(REPO_ROOT / ".env"), extra="ignore")

    # Storage
    data_dir: Path = REPO_ROOT / "data"
    database_url: str | None = None  # default: sqlite:///<data_dir>/smit.db ; PostgreSQL URLs are supported

    # Security
    admin_password: str = "change-me-now"
    secret_key: str = "dev-secret-change-me"
    token_ttl_hours: int = 12
    email_pepper: str = "change-this-pepper"

    # Behaviour
    allow_synthetic_imports: bool = False  # only true inside automated tests
    max_upload_mb: int = 15
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    frontend_dist: Path = REPO_ROOT / "frontend" / "dist"
    default_config_path: Path = REPO_ROOT / "experiment" / "configuration" / "default_config.json"

    @property
    def resolved_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        self.data_dir.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{(self.data_dir / 'smit.db').as_posix()}"

    @property
    def outputs_dir(self) -> Path:
        p = self.data_dir / "outputs"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def using_default_password(self) -> bool:
        return self.admin_password == "change-me-now"


@lru_cache
def get_settings() -> Settings:
    return Settings()
