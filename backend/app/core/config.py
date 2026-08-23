"""Application settings via pydantic-settings.

Every field maps to an env var of the same name (case-insensitive),
e.g. ``database_url`` <- ``DATABASE_URL``. See ``.env.example``.
"""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"
    database_url: str = "postgresql+asyncpg://portfolio:portfolio@localhost:5432/portfolio"

    storage_kind: Literal["s3", "local"] = "s3"
    local_storage_dir: str = ".storage"

    r2_endpoint: str | None = None
    r2_access_key_id: str | None = None
    r2_secret_access_key: str | None = None
    r2_bucket: str = "portfolio-media"
    r2_public_base_url: str | None = None

    resend_api_key: str | None = None
    resend_from: str = "portfolio@siddhesh-chaudhari.com"
    admin_email: str | None = None

    turnstile_secret_key: str | None = None
    turnstile_site_key: str | None = None

    session_secret: str = "dev-only-secret"
    admin_password_hash: str | None = None

    cors_allow_origins: list[str] = []

    cf_access_enabled: bool = False
    cf_access_team_domain: str | None = None
    cf_access_aud: str | None = None

    revalidation_secret: str | None = None
    next_public_base_url: str = "http://localhost:3000"

    admin_static_dir: str = "static"

    glitchtip_dsn: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
