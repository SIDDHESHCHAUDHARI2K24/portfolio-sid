"""Scheduler cron: registry-driven, idempotent, revalidates touched tags."""

from collections.abc import Iterator, Sequence
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core import models_registry
from app.core.enums import PublishStatus
from app.jobs import scheduler
from app.tests.helpers import TestPublishable

TAG = "timeline"


@pytest.fixture
def registered_model(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Isolated registry with TestPublishable registered under TAG."""
    monkeypatch.setattr(models_registry, "_PUBLISHABLES", [])
    models_registry.register_publishable(TestPublishable, TAG)
    yield


@pytest.fixture
def revalidate_calls(
    monkeypatch: pytest.MonkeyPatch,
) -> list[list[str]]:
    calls: list[list[str]] = []

    async def fake_revalidate(tags: Sequence[str]) -> None:
        calls.append(list(tags))

    monkeypatch.setattr(scheduler, "revalidate", fake_revalidate)
    return calls


async def _seed_all_states(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    now = datetime.now(UTC)
    async with session_factory() as session:
        session.add_all(
            [
                TestPublishable(
                    status=PublishStatus.SCHEDULED, publish_at=now - timedelta(hours=1)
                ),
                TestPublishable(
                    status=PublishStatus.SCHEDULED, publish_at=now + timedelta(hours=1)
                ),
                TestPublishable(status=PublishStatus.PUBLISHED, published_at=now),
                TestPublishable(status=PublishStatus.DRAFT),
            ]
        )
        await session.commit()


async def test_scheduler_promotes_due_entries_only(
    session_factory: async_sessionmaker[AsyncSession],
    registered_model: None,
    revalidate_calls: list[list[str]],
) -> None:
    await _seed_all_states(session_factory)

    exit_code = await scheduler.main(session_factory=session_factory)
    assert exit_code == 0

    async with session_factory() as session:
        rows = (await session.execute(select(TestPublishable))).scalars().all()

    by_status: dict[PublishStatus, list[TestPublishable]] = {}
    for row in rows:
        by_status.setdefault(row.status, []).append(row)

    promoted = by_status[PublishStatus.PUBLISHED]
    assert len(promoted) == 2  # seeded published + promoted scheduled
    assert all(row.published_at is not None for row in promoted)
    assert len(by_status[PublishStatus.SCHEDULED]) == 1  # future one untouched
    assert by_status[PublishStatus.SCHEDULED][0].published_at is None
    assert len(by_status[PublishStatus.DRAFT]) == 1

    assert revalidate_calls == [[TAG]]


async def test_scheduler_second_run_is_noop(
    session_factory: async_sessionmaker[AsyncSession],
    registered_model: None,
    revalidate_calls: list[list[str]],
) -> None:
    await _seed_all_states(session_factory)

    await scheduler.main(session_factory=session_factory)
    assert revalidate_calls == [[TAG]]

    await scheduler.main(session_factory=session_factory)
    assert revalidate_calls == [[TAG]]  # no second revalidation


async def test_scheduler_empty_registry_is_noop(
    monkeypatch: pytest.MonkeyPatch,
    session_factory: async_sessionmaker[AsyncSession],
    revalidate_calls: list[list[str]],
) -> None:
    monkeypatch.setattr(models_registry, "_PUBLISHABLES", [])

    exit_code = await scheduler.main(session_factory=session_factory)

    assert exit_code == 0
    assert revalidate_calls == []


async def test_leak_guard_helper_on_test_publishable(
    session: AsyncSession,
) -> None:
    from app.tests.helpers import assert_public_query_excludes_drafts

    await assert_public_query_excludes_drafts(session, TestPublishable)
