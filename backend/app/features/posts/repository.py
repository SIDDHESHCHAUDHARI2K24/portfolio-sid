"""Posts repository: queries only, never imports FastAPI.

``list_public`` applies ``public_filter``; admin bypasses it.
``list_by_collection`` filters by a single collection slug.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.models import TopicTag
from app.core.queries import public_filter
from app.features.posts.models import Post, PostCollection, PostPlatform


async def list_public(session: AsyncSession) -> list[Post]:
    stmt = (
        select(Post)
        .where(public_filter(Post))
        .options(selectinload(Post.topic_tags))
        .order_by(Post.published_date.desc().nullslast(), Post.sort_order.asc())
    )
    return list((await session.scalars(stmt)).unique().all())


async def list_by_collection(session: AsyncSession, collection: PostCollection) -> list[Post]:
    stmt = (
        select(Post)
        .where(public_filter(Post), Post.collections.contains([collection]))
        .options(selectinload(Post.topic_tags))
        .order_by(Post.published_date.desc().nullslast(), Post.sort_order.asc())
    )
    return list((await session.scalars(stmt)).unique().all())


async def list_admin(session: AsyncSession) -> list[Post]:
    stmt = (
        select(Post)
        .options(selectinload(Post.topic_tags))
        .order_by(Post.published_date.desc().nullslast(), Post.sort_order.asc())
    )
    return list((await session.scalars(stmt)).unique().all())


async def get_internal_by_slug(session: AsyncSession, slug: str) -> Post | None:
    """Public read: published internal post by slug (``public_filter`` applies)."""
    stmt = (
        select(Post)
        .where(public_filter(Post), Post.platform == PostPlatform.INTERNAL, Post.slug == slug)
        .options(selectinload(Post.topic_tags))
    )
    return (await session.scalars(stmt)).unique().one_or_none()


async def slug_taken(session: AsyncSession, slug: str, exclude_id: UUID | None = None) -> bool:
    stmt = select(Post.id).where(Post.slug == slug)
    if exclude_id is not None:
        stmt = stmt.where(Post.id != exclude_id)
    return (await session.scalars(stmt)).first() is not None


async def get(session: AsyncSession, post_id: UUID) -> Post | None:
    return await session.get(Post, post_id, options=[selectinload(Post.topic_tags)])


async def create(
    session: AsyncSession,
    post: Post,
    tag_ids: list[UUID] | None = None,
) -> Post:
    tags: list[TopicTag] = []
    if tag_ids:
        tags = list((await session.scalars(select(TopicTag).where(TopicTag.id.in_(tag_ids)))).all())
    post.topic_tags = tags
    session.add(post)
    await session.flush()
    return post


async def update(
    session: AsyncSession,
    post: Post,
    tag_ids: list[UUID] | None = None,
) -> Post:
    if tag_ids is not None:
        tags = list((await session.scalars(select(TopicTag).where(TopicTag.id.in_(tag_ids)))).all())
        post.topic_tags = tags
    else:
        _ = post.topic_tags
    await session.flush()
    return post


async def delete(session: AsyncSession, post: Post) -> None:
    await session.delete(post)
    await session.flush()
