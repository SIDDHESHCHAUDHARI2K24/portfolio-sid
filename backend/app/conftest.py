"""Shared fixtures: portfolio_test database, engine, and async session.

The test database is created once per session against the ``postgres``
maintenance db (owner = dev db user) and the full schema comes from
``models_registry`` metadata — never mocked, never the dev database.
"""

from collections.abc import AsyncIterator

import httpx
import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.engine import URL, make_url
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.app import create_app
from app.core import models_registry
from app.core.config import Settings, get_settings
from app.core.database import get_session
from app.core.security import hash_password
from app.features.auth.endpoints.router import limiter
from app.tests.helpers import TEST_ADMIN_PASSWORD

TEST_DB_NAME = "portfolio_test"


def _base_url() -> URL:
    return make_url(get_settings().database_url)


def _test_url() -> URL:
    return _base_url().set(database=TEST_DB_NAME)


async def _ensure_test_database() -> None:
    """CREATE DATABASE portfolio_test if missing (needs autocommit: CREATE
    DATABASE cannot run inside a transaction)."""
    base = _base_url()
    owner = base.username or "portfolio"
    maintenance = create_async_engine(base.set(database="postgres"), isolation_level="AUTOCOMMIT")
    async with maintenance.connect() as conn:
        exists = (
            await conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": TEST_DB_NAME},
            )
        ).scalar()
        if exists is None:
            await conn.execute(text(f'CREATE DATABASE "{TEST_DB_NAME}" OWNER "{owner}"'))
    await maintenance.dispose()


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def db_engine() -> AsyncIterator[AsyncEngine]:
    await _ensure_test_database()
    engine = create_async_engine(_test_url())
    async with engine.begin() as conn:
        # drop first: a crashed previous session could leave stale rows
        # behind that break unique-constraint tests.
        await conn.run_sync(models_registry.metadata.drop_all)
        await conn.run_sync(models_registry.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(models_registry.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(loop_scope="session")
async def session_factory(db_engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(db_engine, expire_on_commit=False)


@pytest_asyncio.fixture(loop_scope="session")
async def session(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    async with session_factory() as session:
        yield session


@pytest.fixture(autouse=True)
def reset_rate_limiter() -> None:
    """In-memory slowapi counters must never leak between tests."""
    limiter.reset()


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def admin_settings(db_engine: AsyncEngine) -> AsyncIterator[Settings]:
    """Configure a known admin password hash + recipient for auth tests."""
    settings = get_settings()
    old_hash = settings.admin_password_hash
    old_email = settings.admin_email
    settings.admin_password_hash = hash_password(TEST_ADMIN_PASSWORD)
    settings.admin_email = "admin@example.com"
    yield settings
    settings.admin_password_hash = old_hash
    settings.admin_email = old_email


@pytest_asyncio.fixture(loop_scope="session")
async def clean_auth_tables(db_engine: AsyncEngine) -> AsyncIterator[None]:
    async with db_engine.begin() as conn:
        await conn.execute(text("DELETE FROM otp_challenges"))
        await conn.execute(text("DELETE FROM login_attempts"))
    yield


@pytest_asyncio.fixture(loop_scope="session")
async def client(
    admin_settings: Settings, session_factory: async_sessionmaker[AsyncSession]
) -> AsyncIterator[httpx.AsyncClient]:
    """ASGI client whose DB dependency points at the test database."""
    app = create_app()

    async def override_get_session() -> AsyncIterator[AsyncSession]:
        async with session_factory() as override_session:
            yield override_session

    app.dependency_overrides[get_session] = override_get_session
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app)) as http_client:
        yield http_client
    app.dependency_overrides.clear()
