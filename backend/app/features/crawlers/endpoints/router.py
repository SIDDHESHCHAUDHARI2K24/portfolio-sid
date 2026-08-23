"""Crawler admin endpoints: hits list + per-agent weekly summary."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.deps import admin_auth
from app.features.crawlers import repository
from app.features.crawlers.schemas import CrawlerHitOut, CrawlerSummaryRow

admin_router = APIRouter(
    prefix="/api/v1/admin/crawlers",
    tags=["admin"],
    dependencies=admin_auth(),
)

DbSession = Annotated[AsyncSession, Depends(get_session)]


@admin_router.get("/hits", response_model=list[CrawlerHitOut])
async def list_hits(
    session: DbSession,
    agent_label: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[CrawlerHitOut]:
    hits = await repository.list_recent(session, limit=limit, agent_label=agent_label)
    return [
        CrawlerHitOut(
            id=hit.id,
            user_agent=hit.user_agent,
            path=hit.path,
            ip_hash=hit.ip_hash,
            agent_label=hit.agent_label,
            timestamp=hit.timestamp,
        )
        for hit in hits
    ]


@admin_router.get("/summary", response_model=list[CrawlerSummaryRow])
async def get_summary(session: DbSession) -> list[CrawlerSummaryRow]:
    rows = await repository.count_by_agent_weekly(session)
    return [CrawlerSummaryRow(**row) for row in rows]
