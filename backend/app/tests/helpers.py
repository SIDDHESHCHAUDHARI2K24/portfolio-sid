"""Reusable test helpers and scratch models.

``TestPublishable`` lives only in the test database: it is registered on
the shared ``Base.metadata`` at import time, so the conftest schema
creation picks it up. ``assert_public_query_excludes_drafts`` is the
Phase 2 leak-guard template (conventions invariant 8): every feature's
public read path gets this assertion applied to its model.
"""

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import PublishStatus
from app.core.models import Base, PublishableMixin, TimestampMixin, UUIDMixin
from app.core.queries import public_filter

TEST_ADMIN_PASSWORD = "correct-horse-battery-staple-test"


class TestPublishable(UUIDMixin, TimestampMixin, PublishableMixin, Base):
    """Scratch publishable model for scheduler and leak-guard tests."""

    __tablename__ = "test_publishables"
    __test__ = False  # keep pytest from collecting this as a test class


async def assert_public_query_excludes_drafts(session: AsyncSession, model: Any) -> None:
    """Assert ``public_filter`` on ``model`` leaks nothing.

    Inserts one row per publishing state, then asserts the public read
    path includes published and due-scheduled rows and excludes drafts
    and future-scheduled rows. Phase 2 features call this per model.
    """
    now = datetime.now(UTC)
    draft = model(status=PublishStatus.DRAFT)
    scheduled_future = model(status=PublishStatus.SCHEDULED, publish_at=now + timedelta(hours=1))
    published = model(status=PublishStatus.PUBLISHED, published_at=now)
    scheduled_due = model(status=PublishStatus.SCHEDULED, publish_at=now - timedelta(hours=1))
    session.add_all([draft, scheduled_future, published, scheduled_due])
    await session.commit()

    visible = set(
        (await session.execute(select(model.id).where(public_filter(model)))).scalars().all()
    )

    assert published.id in visible
    assert scheduled_due.id in visible
    assert draft.id not in visible
    assert scheduled_future.id not in visible
