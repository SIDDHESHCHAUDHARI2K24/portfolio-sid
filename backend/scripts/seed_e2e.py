"""Deterministic seed for e2e / local verification runs.

Idempotent: removes rows it owns (title prefix ``E2E Seed``) and re-inserts
a minimal, relevance-contrastive dataset so journey assertions (dim vs bright
timeline entries) hold against any fresh database.

Usage: uv run python scripts/seed_e2e.py
"""

import asyncio
import datetime as dt
import sys
from pathlib import Path

_backend_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_backend_root))

from sqlalchemy import select  # noqa: E402

from app.core.database import async_session_factory  # noqa: E402
from app.core.enums import Audience, PublishStatus  # noqa: E402
from app.features.posts.models import Post, PostCollection, PostPlatform  # noqa: E402
from app.features.projects.models import Project  # noqa: E402
from app.features.timeline.models import TimelineEntry, TimelineKind  # noqa: E402

PREFIX = "E2E Seed"
NATIVE_POST_SLUG = "e2e-native-article"


async def seed() -> None:
    async with async_session_factory() as session:
        stale = await session.scalars(
            select(TimelineEntry).where(TimelineEntry.title.like(f"{PREFIX}%"))
        )
        for row in stale:
            await session.delete(row)

        now = dt.datetime.now(dt.UTC)
        session.add_all(
            [
                TimelineEntry(
                    kind=TimelineKind.EXPERIENCE,
                    title=f"{PREFIX}: Recruiters-relevant role",
                    organisation="ACME",
                    start_date=dt.date(2023, 1, 1),
                    summary="Seeded for e2e; bright under the recruiters lens.",
                    status=PublishStatus.PUBLISHED,
                    published_at=now,
                    audience_override=[Audience.RECRUITERS],
                ),
                TimelineEntry(
                    kind=TimelineKind.EDUCATION,
                    title=f"{PREFIX}: Unbiased degree",
                    organisation="MIT",
                    start_date=dt.date(2020, 1, 1),
                    summary="Seeded for e2e; dimmed under any lens.",
                    status=PublishStatus.PUBLISHED,
                    published_at=now,
                ),
            ]
        )
        await session.commit()
        print(f"seeded {2} timeline entries ({PREFIX}*)")

        # A published project cross-linked to a seeded timeline entry, so the
        # TD-36.S5 project -> timeline cross-link journey has something to click.
        linked_entry = await session.scalars(
            select(TimelineEntry)
            .where(TimelineEntry.title.like(f"{PREFIX}: Recruiters-relevant role"))
            .limit(1)
        )
        linked_entry = linked_entry.first()
        if linked_entry is not None:
            existing = await session.scalars(
                select(Project).where(Project.slug == "e2e-seed-project")
            )
            existing = existing.first()
            if existing is not None:
                await session.delete(existing)
                await session.commit()
            session.add(
                Project(
                    title=f"{PREFIX}: Cross-linked project",
                    slug="e2e-seed-project",
                    summary="Seeded for e2e; links back to a timeline entry.",
                    status=PublishStatus.PUBLISHED,
                    published_at=now,
                    timeline_entry_id=linked_entry.id,
                )
            )
            await session.commit()
            print("seeded 1 project (e2e-seed-project) cross-linked to a timeline entry")

        # A published internal (native) post in how_i_use_ai so the writing
        # journey (themed page -> /writing/<slug> -> back) runs instead of skipping.
        stale_post = await session.scalars(select(Post).where(Post.slug == NATIVE_POST_SLUG))
        for row in stale_post:
            await session.delete(row)
        await session.commit()
        session.add(
            Post(
                title=f"{PREFIX}: Native article",
                slug=NATIVE_POST_SLUG,
                summary="Seeded for e2e; a native article in how_i_use_ai.",
                body="## Seeded article\n\nBody text for the writing journey.",
                platform=PostPlatform.INTERNAL,
                collections=[PostCollection.HOW_I_USE_AI],
                status=PublishStatus.PUBLISHED,
                published_at=now,
                published_date=now.date(),
            )
        )
        await session.commit()
        print(f"seeded 1 internal post ({NATIVE_POST_SLUG}) in how_i_use_ai")


if __name__ == "__main__":
    asyncio.run(seed())
