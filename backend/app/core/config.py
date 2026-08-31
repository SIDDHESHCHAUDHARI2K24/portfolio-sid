"""Application settings via pydantic-settings.

Every field maps to an env var of the same name (case-insensitive),
e.g. ``database_url`` <- ``DATABASE_URL``. See ``.env.example``.
"""

from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"
    database_url: str = "postgresql+asyncpg://portfolio:portfolio@localhost:5432/portfolio"
    # QueuePool tuning for asyncpg. When PGBOUNCER_ENABLED=true, point
    # DATABASE_URL at the pgbouncer endpoint instead of postgres directly:
    #   local:  postgresql+asyncpg://portfolio:portfolio@localhost:6432/portfolio
    #           (docker-compose pgbouncer sidecar on 6432 -> postgres:5432)
    #   Railway production: dedicated `pgbouncer` service
    #           (edoburu/pgbouncer) on pgbouncer.railway.internal:6432 ->
    #           postgres.railway.internal:5432. Keep PGBOUNCER_ENABLED=true so
    #           database.py disables the asyncpg prepared-statement cache
    #           (unsafe with pgbouncer transaction pooling).
    database_pool_size: int = 10
    database_max_overflow: int = 5
    pgbouncer_enabled: bool = False

    @field_validator("database_url")
    @classmethod
    def _coerce_asyncpg_driver(cls, v: str) -> str:
        # Railway Postgres emits a sync `postgresql://` URL; SQLAlchemy's async
        # engine requires the `postgresql+asyncpg://` driver. Coerce when absent.
        if v.startswith("postgresql://"):
            return "postgresql+asyncpg://" + v[len("postgresql://") :]
        if v.startswith("postgres://"):
            return "postgresql+asyncpg://" + v[len("postgres://") :]
        return v

    storage_kind: Literal["s3", "local"] = "s3"
    local_storage_dir: str = ".storage"
    media_base_url: str | None = None

    r2_endpoint: str | None = None
    r2_access_key_id: str | None = None
    r2_secret_access_key: str | None = None
    r2_bucket: str = "portfolio-media"
    r2_public_base_url: str | None = None

    resend_api_key: str | None = None
    resend_from: str = "portfolio@siddhesh-chaudhari.com"
    admin_email: str | None = None

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
