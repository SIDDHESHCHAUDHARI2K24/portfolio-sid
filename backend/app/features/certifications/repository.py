"""Certifications repository: queries only, never imports FastAPI.

``list_public`` applies ``public_filter``; admin bypasses it.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.models import TopicTag
from app.core.queries import public_filter
from app.features.certifications.models import Certification


async def list_public(session: AsyncSession) -> list[Certification]:
    stmt = (
        select(Certification)
        .where(public_filter(Certification))
        .options(selectinload(Certification.topic_tags))
        .order_by(Certification.kind.asc(), Certification.sort_order.asc())
    )
    return list((await session.scalars(stmt)).unique().all())


async def list_admin(session: AsyncSession) -> list[Certification]:
    stmt = (
        select(Certification)
        .options(selectinload(Certification.topic_tags))
        .order_by(Certification.kind.asc(), Certification.sort_order.asc())
    )
    return list((await session.scalars(stmt)).unique().all())


async def get(session: AsyncSession, cert_id: UUID) -> Certification | None:
    return await session.get(
        Certification, cert_id, options=[selectinload(Certification.topic_tags)]
    )


async def create(
    session: AsyncSession,
    cert: Certification,
    tag_ids: list[UUID] | None = None,
) -> Certification:
    tags: list[TopicTag] = []
    if tag_ids:
        tags = list((await session.scalars(select(TopicTag).where(TopicTag.id.in_(tag_ids)))).all())
    cert.topic_tags = tags
    session.add(cert)
    await session.flush()
    return cert


async def update(
    session: AsyncSession,
    cert: Certification,
    tag_ids: list[UUID] | None = None,
) -> Certification:
    if tag_ids is not None:
        tags = list((await session.scalars(select(TopicTag).where(TopicTag.id.in_(tag_ids)))).all())
        cert.topic_tags = tags
    else:
        _ = cert.topic_tags
    await session.flush()
    return cert


async def delete(session: AsyncSession, cert: Certification) -> None:
    await session.delete(cert)
    await session.flush()
