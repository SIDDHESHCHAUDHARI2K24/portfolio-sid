"""Relevance service: the pure resolver plus map payload orchestration.

``is_relevant`` is the contract (conventions invariant 10): plain data in,
bool out, no ORM objects, no database access. It is mirrored exactly in
``frontend/src/lib/relevance.ts`` — keep the signature and body identical.
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core import cache_tags
from app.core.enums import Audience
from app.core.revalidation import revalidate
from app.features.relevance import repository
from app.features.relevance.schemas import TagCreate, TagOut, TagUpdate


def is_relevant(
    item_tag_slugs: set[str], overrides: set[str], audience: str, tag_map: dict[str, set[str]]
) -> bool:
    if audience in overrides:
        return True
    return bool(item_tag_slugs & tag_map.get(audience, set()))


async def get_map_payload(session: AsyncSession) -> dict[str, list[str]]:
    """Public map shape: every audience present (empty list when unmapped),
    slugs sorted for stable JSON."""
    tag_map = await repository.load_tag_map(session)
    return {a.value: sorted(tag_map.get(a.value, set())) for a in Audience}


async def update_map(session: AsyncSession, mapping: dict[str, list[str]]) -> dict[str, list[str]]:
    """Replace the map, commit, THEN revalidate (conventions invariant 8).

    Revalidating before the commit would publish a lie if the transaction
    rolled back. Unknown slugs raise ``ValueError`` before any write.
    """
    await repository.replace_map(session, mapping)
    await session.commit()
    await revalidate([cache_tags.RELEVANCE])
    return await get_map_payload(session)


async def list_tags(session: AsyncSession) -> list[TagOut]:
    tags = await repository.list_tags(session)
    return [TagOut(id=t.id, slug=t.slug, label=t.label) for t in tags]


async def create_tag(session: AsyncSession, body: TagCreate) -> TagOut:
    tag = await repository.create_tag(session, body.slug, body.label)
    await session.commit()
    await revalidate([cache_tags.RELEVANCE])
    return TagOut(id=tag.id, slug=tag.slug, label=tag.label)


async def rename_tag(session: AsyncSession, tag_id: uuid.UUID, body: TagUpdate) -> TagOut:
    label = body.label
    if label is None:
        raise ValueError("label is required")
    tag = await repository.rename_tag(session, tag_id, label)
    if tag is None:
        raise ValueError("Tag not found")
    await session.commit()
    await revalidate([cache_tags.RELEVANCE])
    return TagOut(id=tag.id, slug=tag.slug, label=tag.label)


async def delete_tag(session: AsyncSession, tag_id: uuid.UUID) -> None:
    if await repository.tag_in_use(session, tag_id):
        raise ValueError("Tag is in use by content entries or the relevance map")
    ok = await repository.delete_tag(session, tag_id)
    if not ok:
        raise ValueError("Tag not found")
    await session.commit()
    await revalidate([cache_tags.RELEVANCE])
