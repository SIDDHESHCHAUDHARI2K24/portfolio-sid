"""Core data foundations: mixins, timestamps, public_filter, TopicTag, enums."""

import asyncio
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import Audience, PublishStatus
from app.core.models import (
    AUDIENCE_ENUM,
    Base,
    PublishableMixin,
    SortableMixin,
    TimestampMixin,
    TopicTag,
    UUIDMixin,
)
from app.core.queries import public_filter


class TestEntry(UUIDMixin, TimestampMixin, SortableMixin, PublishableMixin, Base):
    """Scratch model exercising every mixin; lives only in the test DB."""

    __tablename__ = "test_entries"
    __test__ = False  # keep pytest from collecting this as a test class

    audience: Mapped[Audience] = mapped_column(
        AUDIENCE_ENUM, nullable=False, default=Audience.PERSONAL
    )


async def test_timestamps_auto_populate(session: AsyncSession) -> None:
    entry = TestEntry()
    session.add(entry)
    await session.commit()
    await session.refresh(entry)

    assert entry.created_at is not None
    assert entry.updated_at is not None
    assert entry.created_at.tzinfo is not None
    assert entry.updated_at.tzinfo is not None
    assert entry.status is PublishStatus.DRAFT
    assert entry.sort_order == 0
    assert isinstance(entry.id, uuid.UUID)


async def test_update_changes_updated_at_not_created_at(session: AsyncSession) -> None:
    entry = TestEntry()
    session.add(entry)
    await session.commit()
    await session.refresh(entry)

    created_at = entry.created_at
    updated_at = entry.updated_at
    await asyncio.sleep(0.05)

    entry.sort_order = 5
    await session.commit()
    await session.refresh(entry)

    assert entry.created_at == created_at
    assert entry.updated_at > updated_at


async def test_public_filter(session: AsyncSession) -> None:
    now = datetime.now(UTC)
    draft = TestEntry(status=PublishStatus.DRAFT)
    published = TestEntry(status=PublishStatus.PUBLISHED, published_at=now)
    scheduled_past = TestEntry(status=PublishStatus.SCHEDULED, publish_at=now - timedelta(hours=1))
    scheduled_future = TestEntry(
        status=PublishStatus.SCHEDULED, publish_at=now + timedelta(hours=1)
    )
    session.add_all([draft, published, scheduled_past, scheduled_future])
    await session.commit()

    visible = (
        (await session.execute(select(TestEntry.id).where(public_filter(TestEntry))))
        .scalars()
        .all()
    )
    visible_ids = set(visible)

    assert published.id in visible_ids
    assert scheduled_past.id in visible_ids
    assert draft.id not in visible_ids
    assert scheduled_future.id not in visible_ids

    # Admin-style query bypasses the filter explicitly and sees everything.
    all_ids = set((await session.execute(select(TestEntry.id))).scalars().all())
    assert {draft.id, published.id, scheduled_past.id, scheduled_future.id} <= all_ids


async def test_topic_tag_round_trip(session: AsyncSession) -> None:
    tag = TopicTag(slug="ai", label="AI", description="Machine intelligence work")
    session.add(tag)
    await session.commit()
    await session.refresh(tag)

    assert isinstance(tag.id, uuid.UUID)
    assert tag.created_at is not None
    assert tag.slug == "ai"


async def test_topic_tag_duplicate_slug_rejected(session: AsyncSession) -> None:
    session.add(TopicTag(slug="dup-slug", label="First"))
    await session.commit()

    session.add(TopicTag(slug="dup-slug", label="Second"))
    with pytest.raises(IntegrityError):
        await session.commit()
    await session.rollback()


async def test_topic_tag_uppercase_slug_rejected(session: AsyncSession) -> None:
    session.add(TopicTag(slug="BadSlug", label="Uppercase"))
    with pytest.raises(IntegrityError):
        await session.commit()
    await session.rollback()


async def test_audience_enum_round_trip(session: AsyncSession) -> None:
    entry = TestEntry(audience=Audience.RECRUITERS)
    session.add(entry)
    await session.commit()

    fetched = (
        await session.execute(select(TestEntry).where(TestEntry.id == entry.id))
    ).scalar_one()
    assert fetched.audience is Audience.RECRUITERS
