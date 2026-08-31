"""PgBouncer pool-tuning regression tests (no DB required).

Verifies ``Settings`` parsing for the new pgBouncer fields and that
``create_async_engine`` is called with ``pool_size`` / ``max_overflow`` /
``pool_pre_ping`` on the default QueuePool (not NullPool) — safe for
PgBouncer transaction mode with asyncpg (see ``app/core/database.py``).
"""

from typing import Any, cast

import pytest
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import AsyncAdaptedQueuePool, NullPool

from app.core.config import Settings


def test_settings_defaults() -> None:
    s = Settings(_env_file=None)
    assert s.database_pool_size == 10
    assert s.database_max_overflow == 5
    assert s.pgbouncer_enabled is False
    # default URL stays on 5432 direct
    assert ":5432/" in s.database_url


def test_settings_pool_overrides_via_constructor() -> None:
    s = Settings(
        _env_file=None,
        database_pool_size=20,
        database_max_overflow=10,
        pgbouncer_enabled=True,
    )
    assert s.database_pool_size == 20
    assert s.database_max_overflow == 10
    assert s.pgbouncer_enabled is True


def test_settings_pgbouncer_env_parsing(monkeypatch: pytest.MonkeyPatch) -> None:
    # pydantic-settings reads env case-insensitively; verify bool coercion
    import os

    monkeypatch.setenv("PGBOUNCER_ENABLED", "true")
    monkeypatch.setenv("DATABASE_POOL_SIZE", "7")
    monkeypatch.setenv("DATABASE_MAX_OVERFLOW", "3")
    s = Settings(_env_file=None)
    assert s.pgbouncer_enabled is True
    assert s.database_pool_size == 7
    assert s.database_max_overflow == 3
    # also verify falsy
    monkeypatch.setenv("PGBOUNCER_ENABLED", "false")
    s2 = Settings(_env_file=None)
    assert s2.pgbouncer_enabled is False
    # cleanup extra vars (monkeypatch will undo PGBOUNCER_ENABLED on teardown,
    # but DATABASE_* are not auto-restored if we pop manually)
    os.environ.pop("DATABASE_POOL_SIZE", None)
    os.environ.pop("DATABASE_MAX_OVERFLOW", None)


def test_settings_pgbouncer_url_mapping_documented() -> None:
    """When pgBouncer is enabled the URL should point at 6432.

    This is a documentation/behaviour contract: the code does not auto-rewrite
    the URL, the operator sets DATABASE_URL to the pgbouncer port. Verify the
    Settings model accepts such URLs and retains pool tuning.
    """
    s = Settings(
        _env_file=None,
        pgbouncer_enabled=True,
        database_url="postgresql+asyncpg://portfolio:portfolio@localhost:6432/portfolio",
        database_pool_size=10,
        database_max_overflow=5,
    )
    assert s.pgbouncer_enabled is True
    assert ":6432/" in s.database_url
    assert s.database_pool_size == 10


def test_database_url_coercion_still_works() -> None:
    s = Settings(_env_file=None, database_url="postgresql://portfolio:portfolio@localhost:5432/portfolio")
    assert s.database_url.startswith("postgresql+asyncpg://")
    s2 = Settings(_env_file=None, database_url="postgres://portfolio:portfolio@localhost:5432/portfolio")
    assert s2.database_url.startswith("postgresql+asyncpg://")


def test_engine_pool_args_no_db_required() -> None:
    """Engine created with pool_size/max_overflow/pool_pre_ping=QueuePool."""
    s = Settings(_env_file=None, database_pool_size=10, database_max_overflow=5)
    engine = create_async_engine(
        s.database_url,
        pool_size=s.database_pool_size,
        max_overflow=s.database_max_overflow,
        pool_pre_ping=True,
    )
    # Must be QueuePool family, NOT NullPool (see database.py docstring)
    assert isinstance(engine.pool, AsyncAdaptedQueuePool)
    assert not isinstance(engine.pool, NullPool)
    pool = cast(Any, engine.pool)
    assert pool.size() == 10
    assert pool._max_overflow == 5
    assert pool._pre_ping is True


def test_engine_custom_pool_sizes() -> None:
    s = Settings(_env_file=None, database_pool_size=20, database_max_overflow=10)
    engine = create_async_engine(
        s.database_url,
        pool_size=s.database_pool_size,
        max_overflow=s.database_max_overflow,
        pool_pre_ping=True,
    )
    pool = cast(Any, engine.pool)
    assert pool.size() == 20
    assert pool._max_overflow == 10


def test_global_engine_uses_pool_tuning() -> None:
    """The module-level engine in app.core.database respects Settings tuning."""
    from app.core import database as db_module
    from app.core.config import get_settings

    settings = get_settings()
    pool = cast(Any, db_module.engine.pool)
    assert pool.size() == settings.database_pool_size
    assert pool._max_overflow == settings.database_max_overflow
    assert pool._pre_ping is True
    assert isinstance(db_module.engine.pool, AsyncAdaptedQueuePool)
