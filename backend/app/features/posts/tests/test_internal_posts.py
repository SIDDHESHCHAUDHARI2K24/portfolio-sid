"""Internal (native) posts: DB rules, schema validation, API, slug endpoint."""

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app.features.posts.models import Post, PostPlatform


@pytest_asyncio.fixture(loop_scope="session")
async def clean_posts_tables(db_engine: AsyncEngine) -> None:
    async with db_engine.begin() as conn:
        await conn.execute(text("DELETE FROM post_topic_tags"))
        await conn.execute(text("DELETE FROM posts"))


# --- Task 1: DB-level rules -------------------------------------------------


async def test_check_rejects_internal_without_slug_or_body(
    session: AsyncSession, clean_posts_tables: None
) -> None:
    session.add(Post(title="x", platform=PostPlatform.INTERNAL, slug="a"))
    with pytest.raises(IntegrityError):
        await session.commit()
    await session.rollback()
    session.add(Post(title="x", platform=PostPlatform.INTERNAL, body="b"))
    with pytest.raises(IntegrityError):
        await session.commit()


async def test_check_rejects_external_without_url(
    session: AsyncSession, clean_posts_tables: None
) -> None:
    session.add(Post(title="x", platform=PostPlatform.MEDIUM))
    with pytest.raises(IntegrityError):
        await session.commit()


async def test_check_allows_internal_without_url(
    session: AsyncSession, clean_posts_tables: None
) -> None:
    session.add(Post(title="x", platform=PostPlatform.INTERNAL, slug="ok", body="# hi"))
    await session.commit()


async def test_slug_unique_in_db(session: AsyncSession, clean_posts_tables: None) -> None:
    session.add(Post(title="a", platform=PostPlatform.INTERNAL, slug="dup", body="b"))
    await session.commit()
    session.add(Post(title="b", platform=PostPlatform.INTERNAL, slug="dup", body="b"))
    with pytest.raises(IntegrityError):
        await session.commit()
