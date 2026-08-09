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
