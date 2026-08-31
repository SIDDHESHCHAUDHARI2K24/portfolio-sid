"""Async SQLAlchemy engine, session factory, and session dependency.

PgBouncer notes
---------------
* Local docker-compose exposes a ``pgbouncer`` sidecar on 6432 -> postgres:5432
  (``POOL_MODE=transaction``). Set ``PGBOUNCER_ENABLED=true`` and point
  ``DATABASE_URL`` at ``...@localhost:6432/...`` to route through it.
* Railway production already has an internal pgbouncer for Postgres; no
  sidecar service is needed — only the pool tuning below applies.

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
  ``LISTEN/NOTIFY`` / advisory locks that assume session affinity. ``asyncpg``
  via SQLAlchemy's async dialect does **not** use server-prepared statements
  by default (unlike ``psycopg`` with ``prepare_threshold``), and this
  codebase never uses ``LISTEN/NOTIFY`` or session-level advisory locks.
  Hence ``POOL_MODE=transaction`` is safe without ``statement_cache_size=0``.
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

from app.core.config import get_settings

settings = get_settings()

# See module docstring for PgBouncer/pool justification — QueuePool, not NullPool.
engine: AsyncEngine = create_async_engine(
    settings.database_url,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    pool_pre_ping=True,
)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with async_session_factory() as session:
        yield session
