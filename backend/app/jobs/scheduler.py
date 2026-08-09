"""Scheduled-publish cron (conventions invariant 8).

Promotes every publishable model row with ``status == SCHEDULED`` and
``publish_at <= now()`` to ``PUBLISHED``, then revalidates the affected
cache tags. Registry-driven (``models_registry.publishables``) — never a
hardcoded list. Idempotent by construction: a second run finds nothing
due and revalidates nothing.

Runs every 5 minutes in production (TD-M4 cron), so scheduled content
appears up to 5 minutes late — by design, documented in conventions.md.

Runnable directly: ``uv run python -m app.jobs.scheduler``.
"""

import asyncio
import logging
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.database import async_session_factory as _default_session_factory
from app.core.enums import PublishStatus
from app.core.models_registry import publishables
from app.core.revalidation import revalidate

logger = logging.getLogger(__name__)


async def run_once(factory: async_sessionmaker[AsyncSession]) -> tuple[int, list[str]]:
    """One scheduler pass. Returns ``(promoted_count, touched_tags)``.

    All promotions happen in a single transaction; revalidation fires
    after the commit (invariant 8).
    """
    promoted = 0
    tags: set[str] = set()
    now = datetime.now(UTC)
    async with factory() as session:
        for model, tag in publishables():
            due = (
                (
                    await session.execute(
                        select(model).where(
                            model.status == PublishStatus.SCHEDULED,
                            model.publish_at <= now,
                        )
                    )
                )
                .scalars()
                .all()
            )
            for row in due:
                row.status = PublishStatus.PUBLISHED
                row.published_at = now
            if due:
                promoted += len(due)
                tags.add(tag)
        await session.commit()
    tag_list = sorted(tags)
    if tag_list:
        await revalidate(tag_list)
    return promoted, tag_list


async def main(
    session_factory: async_sessionmaker[AsyncSession] | None = None,
) -> int:
    """Run one scheduler pass. Returns the process exit code (always 0)."""
    factory = session_factory if session_factory is not None else _default_session_factory
    registered = publishables()
    if not registered:
        logger.info("scheduler: no publishable models registered; nothing to do")
        return 0
    promoted, tags = await run_once(factory)
    logger.info(
        "scheduler: promoted %d row(s) across %d model(s); revalidated tags=%s",
        promoted,
        len(registered),
        tags,
    )
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    raise SystemExit(asyncio.run(main()))
