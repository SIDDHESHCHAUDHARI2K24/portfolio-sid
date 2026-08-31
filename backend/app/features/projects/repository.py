"""Projects repository: queries only, never imports FastAPI."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.models import TopicTag
from app.core.queries import public_filter
from app.features.projects.models import Project


async def list_public(session: AsyncSession) -> list[Project]:
    stmt = (
        select(Project)
        .where(public_filter(Project))
        .options(selectinload(Project.topic_tags), selectinload(Project.attachments))
        .order_by(Project.sort_order.asc(), Project.created_at.desc())
    )
    return list((await session.scalars(stmt)).unique().all())


async def list_admin(session: AsyncSession) -> list[Project]:
    stmt = (
        select(Project)
        .options(selectinload(Project.topic_tags), selectinload(Project.attachments))
        .order_by(Project.sort_order.asc(), Project.created_at.desc())
    )
    return list((await session.scalars(stmt)).unique().all())


async def get(session: AsyncSession, project_id: UUID) -> Project | None:
    return await session.get(
        Project,
        project_id,
        options=[selectinload(Project.topic_tags), selectinload(Project.attachments)],
    )


async def get_by_slug(session: AsyncSession, slug: str) -> Project | None:
    stmt = (
        select(Project)
        .where(Project.slug == slug)
        .options(selectinload(Project.topic_tags), selectinload(Project.attachments))
    )
    return (await session.scalars(stmt)).unique().one_or_none()


async def list_public_by_timeline(
    session: AsyncSession, entry_id: UUID
) -> list[Project]:
    stmt = (
        select(Project)
        .where(Project.timeline_entry_id == entry_id)
        .where(public_filter(Project))
        .options(selectinload(Project.topic_tags), selectinload(Project.attachments))
        .order_by(Project.sort_order.asc(), Project.created_at.desc())
    )
    return list((await session.scalars(stmt)).unique().all())


async def create(
    session: AsyncSession,
    project: Project,
    tag_ids: list[UUID] | None = None,
) -> Project:
    tags: list[TopicTag] = []
    if tag_ids:
        tags = list((await session.scalars(select(TopicTag).where(TopicTag.id.in_(tag_ids)))).all())
    project.topic_tags = tags
    project.attachments = []
    session.add(project)
    await session.flush()
    return project


async def update(
    session: AsyncSession,
    project: Project,
    tag_ids: list[UUID] | None = None,
) -> Project:
    if tag_ids is not None:
        tags = list((await session.scalars(select(TopicTag).where(TopicTag.id.in_(tag_ids)))).all())
        project.topic_tags = tags
    else:
        _ = project.topic_tags
    await session.flush()
    return project


async def delete(session: AsyncSession, project: Project) -> None:
    await session.delete(project)
    await session.flush()
