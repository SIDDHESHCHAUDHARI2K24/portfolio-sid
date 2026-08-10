"""Posts service: returns dicts (not ORM) to avoid MissingGreenlet."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import Audience, PublishStatus
from app.core.models import TopicTag
from app.features.posts import repository
from app.features.posts.models import Post, PostCollection, PostPlatform
from app.features.posts.schemas import PostCreate, PostUpdate


def _post_to_dict(post: Post) -> dict[str, object]:
    def _s(v: object) -> str:
        return v.value if hasattr(v, "value") else str(v)

    return {
        "id": post.id,
        "title": post.title,
        "summary": post.summary,
        "url": post.url,
        "platform": _s(post.platform),
        "published_date": post.published_date,
        "collections": [_s(c) for c in (post.collections or [])],
        "sort_order": post.sort_order,
        "created_at": post.created_at,
        "updated_at": post.updated_at,
        "status": _s(post.status),
        "publish_at": post.publish_at,
        "published_at": post.published_at,
        "audience_override": (
            [_s(a) for a in post.audience_override] if post.audience_override else None
        ),
        "topic_tags": [
            {"id": t.id, "slug": t.slug, "label": t.label} for t in (post.topic_tags or [])
        ],
    }


async def list_public_dicts(session: AsyncSession) -> list[dict[str, object]]:
    posts = await repository.list_public(session)
    return [_post_to_dict(p) for p in posts]


async def list_by_collection_dict(
    session: AsyncSession, collection: PostCollection
) -> list[dict[str, object]]:
    posts = await repository.list_by_collection(session, collection)
    return [_post_to_dict(p) for p in posts]


async def list_admin_dicts(session: AsyncSession) -> list[dict[str, object]]:
    posts = await repository.list_admin(session)
    return [_post_to_dict(p) for p in posts]


async def get_dict(session: AsyncSession, post_id: UUID) -> dict[str, object] | None:
    post = await repository.get(session, post_id)
    if post is None:
        return None
    return _post_to_dict(post)


async def _resolve_tags(session: AsyncSession, slugs: list[str]) -> list[UUID]:
    if not slugs:
        return []
    tags = list((await session.scalars(select(TopicTag).where(TopicTag.slug.in_(slugs)))).all())
    found = {t.slug for t in tags}
    missing = set(slugs) - found
    if missing:
        raise ValueError(f"unknown topic tag slugs: {', '.join(sorted(missing))}")
    return [t.id for t in tags]


async def create_dict(session: AsyncSession, data: PostCreate) -> dict[str, object]:
    tag_ids = await _resolve_tags(session, data.tag_slugs)
    entry_data = data.model_dump(exclude={"tag_slugs"})

    raw_platform = entry_data["platform"]
    entry_data["platform"] = (
        PostPlatform(raw_platform) if isinstance(raw_platform, str) else raw_platform
    )

    raw_collections = entry_data.get("collections", [])
    entry_data["collections"] = [
        PostCollection(c) if isinstance(c, str) else c for c in raw_collections
    ]

    if entry_data.get("audience_override"):
        entry_data["audience_override"] = [Audience(a) for a in entry_data["audience_override"]]

    if isinstance(entry_data.get("status"), str):
        entry_data["status"] = PublishStatus(entry_data["status"])
    if entry_data["status"] == PublishStatus.PUBLISHED:
        entry_data["published_at"] = datetime.now(UTC)

    post = Post(**entry_data)
    post = await repository.create(session, post, tag_ids)
    await session.commit()
    return _post_to_dict(post)


async def update_dict(session: AsyncSession, post_id: UUID, data: PostUpdate) -> dict[str, object]:
    post = await repository.get(session, post_id)
    if post is None:
        raise ValueError("post not found")

    update_data = data.model_dump(exclude_unset=True, exclude={"tag_slugs"})

    if update_data.get("platform") and isinstance(update_data["platform"], str):
        update_data["platform"] = PostPlatform(update_data["platform"])

    raw_collections = update_data.get("collections")
    if raw_collections is not None:
        update_data["collections"] = [
            PostCollection(c) if isinstance(c, str) else c for c in raw_collections
        ]

    if update_data.get("audience_override"):
        update_data["audience_override"] = [Audience(a) for a in update_data["audience_override"]]

    if isinstance(update_data.get("status"), str):
        update_data["status"] = PublishStatus(update_data["status"])
    if (
        update_data.get("status") == PublishStatus.PUBLISHED
        and post.status != PublishStatus.PUBLISHED
    ):
        update_data["published_at"] = datetime.now(UTC)

    for key, value in update_data.items():
        setattr(post, key, value)

    post.updated_at = datetime.now(UTC)

    tag_ids = None
    if data.tag_slugs is not None:
        tag_ids = await _resolve_tags(session, data.tag_slugs)

    await repository.update(session, post, tag_ids)
    await session.commit()
    return _post_to_dict(post)


async def delete(session: AsyncSession, post_id: UUID) -> None:
    post = await repository.get(session, post_id)
    if post is None:
        raise ValueError("post not found")
    await repository.delete(session, post)
    await session.commit()
