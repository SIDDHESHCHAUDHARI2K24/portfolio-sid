"""Crawler repository: queries only, never imports FastAPI."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.crawlers.models import CrawlerHit


async def create(session: AsyncSession, hit: CrawlerHit) -> CrawlerHit:
    session.add(hit)
    await session.flush()
    return hit


async def list_recent(
    session: AsyncSession,
    limit: int = 100,
    agent_label: str | None = None,
) -> list[CrawlerHit]:
    stmt = select(CrawlerHit).order_by(CrawlerHit.timestamp.desc())
    if agent_label is not None:
        stmt = stmt.where(CrawlerHit.agent_label == agent_label)
    stmt = stmt.limit(limit)
    return list((await session.scalars(stmt)).all())


async def count_by_agent_weekly(
    session: AsyncSession,
) -> list[dict[str, object]]:
    stmt = (
        select(
            CrawlerHit.agent_label,
            func.date_trunc("week", CrawlerHit.timestamp).label("week_start"),
            func.count().label("count"),
        )
        .group_by(CrawlerHit.agent_label, text("week_start"))
        .order_by(text("week_start DESC"), CrawlerHit.agent_label)
    )
    rows = (await session.execute(stmt)).all()
    return [
        {
            "agent_label": row.agent_label,
            "week_start": str(row.week_start),
            "count": row.count,
        }
        for row in rows
    ]


async def delete_older_than(session: AsyncSession, days: int) -> int:
    cutoff = datetime.now(UTC) - timedelta(days=days)
    stmt_count = select(func.count()).select_from(CrawlerHit).where(CrawlerHit.timestamp < cutoff)
    count = (await session.execute(stmt_count)).scalar_one()
    if count == 0:
        return 0
    stmt_delete = delete(CrawlerHit).where(CrawlerHit.timestamp < cutoff)
    await session.execute(stmt_delete)
    await session.flush()
    return count
