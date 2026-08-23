"""Relevance repository: tag-map reads and atomic replace.

Never imports FastAPI (conventions invariant 5).
"""

import uuid
from collections.abc import Sequence

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.enums import Audience
from app.core.models import TopicTag
from app.features.relevance.models import AudienceTagMap


async def load_tag_map(session: AsyncSession) -> dict[str, set[str]]:
    """Full audience → tag-slug map in ONE query.

    Loaded once per request; per-item resolution against it is pure set
    intersection. Audiences with no rows are simply absent from the dict.
    """
    rows = (
        await session.execute(
            select(AudienceTagMap.audience, TopicTag.slug).join(
                TopicTag, AudienceTagMap.topic_tag_id == TopicTag.id
            )
        )
    ).all()
    tag_map: dict[str, set[str]] = {}
    for audience, slug in rows:
        tag_map.setdefault(audience.value, set()).add(slug)
    return tag_map


async def list_map_rows(session: AsyncSession) -> Sequence[AudienceTagMap]:
    """Every map row with its tag loaded, for the admin matrix view."""
    return (
        (
            await session.execute(
                select(AudienceTagMap)
                .options(selectinload(AudienceTagMap.topic_tag))
                .order_by(AudienceTagMap.audience, TopicTag.slug)
            )
        )
        .scalars()
        .all()
    )


async def replace_map(session: AsyncSession, mapping: dict[str, list[str]]) -> None:
    """Delete every row and insert the new mapping in ONE transaction.

    The caller commits. Unknown slugs raise ``ValueError`` before anything
    is written. Duplicate slugs per audience are collapsed so the payload
    itself can never violate the unique constraint.
    """
    slugs = sorted({slug for tags in mapping.values() for slug in tags})
    slug_to_id: dict[str, uuid.UUID] = {}
    if slugs:
        rows = (
            await session.execute(
                select(TopicTag.slug, TopicTag.id).where(TopicTag.slug.in_(slugs))
            )
        ).all()
        slug_to_id = {slug: tag_id for slug, tag_id in rows}
        missing = sorted(set(slugs) - slug_to_id.keys())
        if missing:
            raise ValueError(f"unknown topic tag slugs: {', '.join(missing)}")

    await session.execute(delete(AudienceTagMap))
    session.add_all(
        AudienceTagMap(audience=Audience(audience), topic_tag_id=slug_to_id[slug])
        for audience, tags in mapping.items()
        for slug in sorted(set(tags))
    )


async def list_tags(session: AsyncSession) -> Sequence[TopicTag]:
    return (await session.execute(select(TopicTag).order_by(TopicTag.slug))).scalars().all()


async def create_tag(session: AsyncSession, slug: str, label: str) -> TopicTag:
    tag = TopicTag(slug=slug, label=label)
    session.add(tag)
    await session.flush()
    return tag


async def get_tag(session: AsyncSession, tag_id: uuid.UUID) -> TopicTag | None:
    return await session.get(TopicTag, tag_id)


async def rename_tag(session: AsyncSession, tag_id: uuid.UUID, label: str) -> TopicTag | None:
    tag = await session.get(TopicTag, tag_id)
    if tag is None:
        return None
    tag.label = label
    await session.flush()
    return tag


async def delete_tag(session: AsyncSession, tag_id: uuid.UUID) -> bool:
    tag = await session.get(TopicTag, tag_id)
    if tag is None:
        return False
    await session.delete(tag)
    await session.flush()
    return True


async def tag_in_use(session: AsyncSession, tag_id: uuid.UUID) -> bool:
    from sqlalchemy import text as sa_text

    row = (
        await session.execute(
            sa_text("SELECT 1 FROM audience_tag_map WHERE topic_tag_id = :tid LIMIT 1"),
            {"tid": tag_id},
        )
    ).first()
    if row is not None:
        return True
    row = (
        await session.execute(
            sa_text("SELECT 1 FROM timeline_topic_tags WHERE topic_tag_id = :tid LIMIT 1"),
            {"tid": tag_id},
        )
    ).first()
    return row is not None
