"""Async SQLAlchemy engine, session factory, and session dependency.

PgBouncer notes
---------------
* Local docker-compose exposes a ``pgbouncer`` sidecar on 6432 -> postgres:5432
  (``POOL_MODE=transaction``). Set ``PGBOUNCER_ENABLED=true`` and point
  ``DATABASE_URL`` at ``...@localhost:6432/...`` to route through it.
* Railway production runs a dedicated ``pgbouncer`` service
  (``edoburu/pgbouncer``, 6432) in front of the Postgres plugin — every
  backend/cron connection goes through it, and ``alembic/env.py`` applies the
  same statement-cache disable as this module (via ``pgbouncer_connect_args``).

Pool choice justification
-------------------------
We intentionally keep SQLAlchemy's default ``AsyncAdaptedQueuePool`` with
``pool_size`` / ``max_overflow`` / ``pool_pre_ping`` even when PgBouncer is
in ``transaction`` mode, and we do **NOT** use ``poolclass=NullPool``.

Why not NullPool:

* ``NullPool`` disables SQLAlchemy client-side pooling entirely, opening a
  new DBAPI connection for every checkout. That defeats PgBouncer's purpose
  (amortising connection establishment) and increases churn under agent load.
* Transaction pooling at PgBouncer recycles server connections per
  transaction; SQLAlchemy's QueuePool recycles *client* connections to
  PgBouncer. The two layers are complementary.

Why transaction mode is safe with asyncpg:

* The classic incompatibility is server-side prepared statements and
  ``LISTEN/NOTIFY`` / advisory locks that assume session affinity. SQLAlchemy's
  asyncpg dialect keeps a *client-side* prepared statement cache
  (``prepared_statement_cache_size``, default 100), which conflicts with
  PgBouncer transaction pooling: the server-side connection changes between
  transactions, so a cached ``__asyncpg_stmt_N__`` lands on a server connection
  that already has it (``DuplicatePreparedStatementError``) or lost it.
* When ``PGBOUNCER_ENABLED`` is true we therefore disable the prepared
  statement cache (``prepared_statement_cache_size=0``); queries then use
  simple/extended protocol without server-side ``PREPARE``.
* ``asyncpg`` itself does not use server-prepared statements implicitly; the
  cache lives in SQLAlchemy's dialect, hence the dialect-level knob above.
* This codebase never uses ``LISTEN/NOTIFY`` or session-level advisory locks.
  Hence ``POOL_MODE=transaction`` is safe with the cache disabled.
* ``pool_pre_ping=True`` guards against stale connections that PgBouncer
  may have recycled server-side while the client pool still holds them.
"""

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import Settings, get_settings

settings = get_settings()


def pgbouncer_connect_args(settings: Settings) -> dict[str, int]:
    """Connect args that disable asyncpg statement caches under PgBouncer.

    SQLAlchemy's asyncpg dialect prepares statements by default
    (``prepared_statement_cache_size``, default 100). Under PgBouncer
    ``transaction`` pooling the server-side connection changes between
    transactions, so cached ``__asyncpg_stmt_N__`` names collide with
    statements left behind by other clients
    (``DuplicatePreparedStatementError``). Disabling both knobs forces the
    simple/extended protocol without server-side ``PREPARE``.

    Returns an empty dict when PgBouncer is not in the path. Shared by
    ``build_engine`` and ``alembic/env.py`` so every engine created in
    production is pgbouncer-safe.
    """
    if not settings.pgbouncer_enabled:
        return {}
    return {
        "statement_cache_size": 0,
        "prepared_statement_cache_size": 0,
    }


def build_engine(settings: Settings) -> AsyncEngine:
    """Create the async engine from ``settings``.

    See module docstring for PgBouncer/pool justification — QueuePool, not
    NullPool, and the asyncpg prepared statement cache disabled when routing
    through PgBouncer transaction pooling.
    """
    return create_async_engine(
        settings.database_url,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        pool_pre_ping=True,
        connect_args=pgbouncer_connect_args(settings),
    )


engine: AsyncEngine = build_engine(settings)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with async_session_factory() as session:
        yield session
