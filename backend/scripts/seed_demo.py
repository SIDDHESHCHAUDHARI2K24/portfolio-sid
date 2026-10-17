"""Local-only demo seed: realistic sample content for every public category.

Idempotent: each row is upserted by natural key (certifications/collections/
thesis/posts by title, prose by slug). All sample titles start with ``Sample —``
so they are easy to spot and remove (``--remove``).

Refuses to run unless ENVIRONMENT is development/local AND the database host
is localhost/127.0.0.1.

Usage:
    uv run python scripts/seed_demo.py            # seed / refresh
    uv run python scripts/seed_demo.py --remove   # delete only the samples
"""

import asyncio
import datetime as dt
import sys
from pathlib import Path
from typing import Any

_backend_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_backend_root))

from sqlalchemy import select  # noqa: E402
from sqlalchemy.engine import make_url  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.core.database import async_session_factory  # noqa: E402
from app.core.enums import Audience, PublishStatus  # noqa: E402
from app.core.models import TopicTag  # noqa: E402
from app.features.certifications.models import Certification, CertKind  # noqa: E402
from app.features.collections.models import (  # noqa: E402
    CollectionItem,
    CollectionKind,
    CollectionStatus,
    ExternalSource,
)
from app.features.posts.models import Post, PostCollection, PostPlatform  # noqa: E402
from app.features.prose.models import ProseGroup, ProsePage  # noqa: E402
from app.features.thesis.models import Thesis  # noqa: E402

PREFIX = "Sample — "
NOW = dt.datetime.now(dt.UTC)
A = Audience


def _guard() -> None:
    settings = get_settings()
    host = make_url(settings.database_url).host
    if settings.environment not in {"development", "local"} or host not in {
        "localhost",
        "127.0.0.1",
    }:
        sys.exit(
            f"refusing to seed: environment={settings.environment!r} db host={host!r} "
            "(need development/local + localhost)"
        )


async def _tags(session: AsyncSession, slugs: list[str]) -> list[TopicTag]:
    if not slugs:
        return []
    rows = (await session.scalars(select(TopicTag).where(TopicTag.slug.in_(slugs)))).all()
    missing = set(slugs) - {t.slug for t in rows}
    if missing:
        print(f"  warn: unknown topic tags skipped: {sorted(missing)}")
    return list(rows)


async def _upsert(
    session: AsyncSession, model: Any, key: str, value: str, data: dict[str, Any]
) -> None:
    row = await session.scalar(select(model).where(getattr(model, key) == value))
    if row is None:
        row = model(**{key: value})
        session.add(row)
    for k, v in data.items():
        setattr(row, k, v)
    row.status = PublishStatus.PUBLISHED
    row.published_at = row.published_at or NOW


def _d(y: int, m: int, d: int) -> dt.date:
    return dt.date(y, m, d)


# (title, issuer, kind, issued, expires, tags, audiences)
CERTS: list[tuple[str, str, str, dt.date, dt.date | None, list[str], list[A] | None]] = [
    (
        "Google Cloud Professional Architect",
        "Google Cloud",
        "technical",
        _d(2024, 3, 12),
        _d(2026, 3, 12),
        ["gcp", "engineering"],
        [A.TECHIES, A.RECRUITERS],
    ),
    (
        "Agentic AI Engineering",
        "DeepLearning.AI",
        "technical",
        _d(2025, 6, 1),
        None,
        ["agentic-ai", "ai"],
        [A.TECHIES],
    ),
    (
        "Platform Engineering Fundamentals",
        "Linux Foundation",
        "technical",
        _d(2023, 9, 20),
        None,
        ["platform-engineering"],
        None,
    ),
    (
        "Data Platform Specialist",
        "Databricks",
        "technical",
        _d(2024, 11, 5),
        _d(2026, 11, 5),
        ["data-platform"],
        [A.TECHIES],
    ),
    (
        "Venture Capital Fundamentals",
        "Kauffman Fellows",
        "business",
        _d(2024, 5, 2),
        None,
        ["venture-capital", "fundraising"],
        [A.INVESTORS, A.FOUNDERS],
    ),
    (
        "Product Management Certificate",
        "Product School",
        "business",
        _d(2022, 8, 15),
        None,
        ["product-management"],
        [A.RECRUITERS],
    ),
    (
        "Startup Finance and Fundraising",
        "Y Combinator Startup School",
        "business",
        _d(2023, 2, 10),
        None,
        ["startup", "fundraising"],
        [A.FOUNDERS, A.INVESTORS],
    ),
]

# (title, creator, kind, section, status, note)
COLLECTION: list[tuple[str, str, str, str, str, str]] = [
    (
        "Zero to One",
        "Peter Thiel",
        "book",
        "Startups",
        "completed",
        "Contrarian thinking on building companies.",
    ),
    (
        "The Hard Thing About Hard Things",
        "Ben Horowitz",
        "book",
        "Startups",
        "completed",
        "Honest founder lessons.",
    ),
    (
        "Designing Data-Intensive Applications",
        "Martin Kleppmann",
        "book",
        "Engineering",
        "reading",
        "The systems bible.",
    ),
    (
        "The Mom Test",
        "Rob Fitzpatrick",
        "book",
        "Startups",
        "want_to_read",
        "Customer conversations done right.",
    ),
    ("Atomic Habits", "James Clear", "book", "Self", "completed", "Small habits compound."),
    (
        "Sample Anime — Steins;Gate",
        "White Fox",
        "anime",
        "Sci-Fi",
        "completed",
        "Time travel done properly.",
    ),
    (
        "Sample Anime — Frieren: Beyond Journey's End",
        "Madhouse",
        "anime",
        "Fantasy",
        "completed",
        "Quiet and beautiful.",
    ),
    (
        "Sample Anime — Monster",
        "Madhouse",
        "anime",
        "Thriller",
        "reading",
        "Slow-burn masterpiece.",
    ),
    (
        "Sample Anime — Cyberpunk: Edgerunners",
        "Trigger",
        "anime",
        "Sci-Fi",
        "want_to_read",
        "Neon and heartbreak.",
    ),
    (
        "Sample Manhwa — Solo Leveling",
        "Chugong",
        "manhwa",
        "Action",
        "completed",
        "The one that started it.",
    ),
    (
        "Sample Manhwa — Omniscient Reader",
        "Sing Shong",
        "manhwa",
        "Action",
        "reading",
        "Story-within-a-story.",
    ),
    (
        "Sample Manhwa — Tower of God",
        "SIU",
        "manhwa",
        "Fantasy",
        "reading",
        "Sprawling world-building.",
    ),
]

THESIS: list[tuple[str, str, dt.date, list[str], list[A] | None]] = [
    (
        "Agentic AI will eat vertical SaaS workflows",
        "Why task-completing agents change what software is worth paying for.",
        _d(2025, 9, 1),
        ["agentic-ai", "ai", "enterprise-saas"],
        [A.INVESTORS, A.TECHIES],
    ),
    (
        "Data platforms are the new picks and shovels",
        "Infrastructure under every AI product compounds in value.",
        _d(2025, 4, 14),
        ["data-platform", "venture-capital"],
        [A.INVESTORS],
    ),
    (
        "Ad-tech is being rebuilt around first-party data",
        "Privacy shifts reopen a mature market to new entrants.",
        _d(2024, 12, 3),
        ["adtech", "startup"],
        [A.INVESTORS, A.FOUNDERS],
    ),
    (
        "CRM automation: from system of record to system of action",
        "Where the next wave of workflow tooling lands.",
        _d(2024, 7, 21),
        ["crm-automation", "enterprise-saas"],
        None,
    ),
]

# (title, summary, platform, collection, tags, audiences)
POSTS: list[tuple[str, str, PostPlatform, PostCollection, list[str], list[A] | None]] = [
    (
        "My daily AI workflow for shipping faster",
        "How I pair with coding agents day to day.",
        PostPlatform.SUBSTACK,
        PostCollection.HOW_I_USE_AI,
        ["ai", "engineering"],
        [A.TECHIES],
    ),
    (
        "Prompting patterns that actually hold up",
        "Patterns I reuse across projects.",
        PostPlatform.MEDIUM,
        PostCollection.HOW_I_USE_AI,
        ["ai"],
        [A.TECHIES, A.RECRUITERS],
    ),
    (
        "Building an agent eval loop (video)",
        "Walkthrough of an eval harness.",
        PostPlatform.YOUTUBE,
        PostCollection.HOW_I_USE_AI,
        ["agentic-ai"],
        [A.TECHIES],
    ),
    (
        "Using AI for research and writing",
        "Notes outside the usual dev loop.",
        PostPlatform.OTHER,
        PostCollection.HOW_I_USE_AI,
        ["ai"],
        None,
    ),
    (
        "Why I went down the Postgres rabbit hole",
        "Query planners, vacuum, and surprises.",
        PostPlatform.SUBSTACK,
        PostCollection.TECH_RABBITHOLE,
        ["engineering", "data-platform"],
        [A.TECHIES],
    ),
    (
        "Platform engineering without the cargo cult",
        "What a small platform team really needs.",
        PostPlatform.MEDIUM,
        PostCollection.TECH_RABBITHOLE,
        ["platform-engineering"],
        [A.TECHIES, A.RECRUITERS],
    ),
    (
        "GCP networking deep dive (video)",
        "VPCs, peering, and the odd corner cases.",
        PostPlatform.YOUTUBE,
        PostCollection.TECH_RABBITHOLE,
        ["gcp"],
        [A.TECHIES],
    ),
    (
        "Weekend hacks and tiny tools",
        "A collection of small experiments.",
        PostPlatform.OTHER,
        PostCollection.TECH_RABBITHOLE,
        ["engineering"],
        None,
    ),
    (
        "What founders get wrong about fundraising",
        "Common mistakes seen from the investor side.",
        PostPlatform.SUBSTACK,
        PostCollection.VC_FOR_FOUNDERS,
        ["fundraising", "venture-capital"],
        [A.FOUNDERS, A.INVESTORS],
    ),
    (
        "How VCs actually read a deck",
        "A reader's-eye view of the first five minutes.",
        PostPlatform.MEDIUM,
        PostCollection.VC_FOR_FOUNDERS,
        ["venture-capital", "startup"],
        [A.FOUNDERS],
    ),
    (
        "Seed round mechanics explained (video)",
        "SAFEs, notes and priced rounds.",
        PostPlatform.YOUTUBE,
        PostCollection.VC_FOR_FOUNDERS,
        ["fundraising"],
        [A.FOUNDERS],
    ),
    (
        "Investor update template",
        "The format that keeps investors informed.",
        PostPlatform.OTHER,
        PostCollection.VC_FOR_FOUNDERS,
        ["startup"],
        [A.FOUNDERS, A.INVESTORS],
    ),
]

LOREM = (
    "This is **sample content** seeded for local development.\n\n"
    "It exists so you can see how this page renders and how it is managed in the admin. "
    "Edit or delete it freely.\n\n"
    "## A heading\n\n- First point\n- Second point\n- Third point\n\n"
    "> A short quote to check blockquote styling.\n"
)

# (slug, title, group, audiences, cta)
PROSE: list[tuple[str, str, ProseGroup, list[A] | None, tuple[str, str] | None]] = [
    (
        "sample-hobbies-running",
        "Sample — Running and fitness",
        ProseGroup.HOBBIES,
        [A.PERSONAL],
        None,
    ),
    ("sample-hobbies-anime", "Sample — Why I watch anime", ProseGroup.HOBBIES, [A.PERSONAL], None),
    ("sample-hobbies-reading", "Sample — My reading habit", ProseGroup.HOBBIES, [A.PERSONAL], None),
    (
        "sample-work-views-ownership",
        "Sample — How I think about ownership",
        ProseGroup.WORK_VIEWS,
        [A.RECRUITERS, A.FOUNDERS],
        None,
    ),
    (
        "sample-work-views-shipping",
        "Sample — Shipping over polishing",
        ProseGroup.WORK_VIEWS,
        [A.RECRUITERS, A.TECHIES],
        None,
    ),
    (
        "sample-work-views-teams",
        "Sample — What good teams look like",
        ProseGroup.WORK_VIEWS,
        [A.RECRUITERS],
        None,
    ),
    (
        "sample-investor-intro",
        "Sample — Investor introduction",
        ProseGroup.INVESTOR_INTRO,
        [A.INVESTORS],
        ("Request an intro", "https://example.com/intro"),
    ),
    (
        "sample-investor-focus",
        "Sample — Investment focus areas",
        ProseGroup.INVESTOR_INTRO,
        [A.INVESTORS, A.FOUNDERS],
        ("Share your deck", "https://example.com/deck"),
    ),
    (
        "sample-investor-track-record",
        "Sample — Track record",
        ProseGroup.INVESTOR_INTRO,
        [A.INVESTORS],
        None,
    ),
]


async def remove() -> None:
    async with async_session_factory() as session:
        n = 0
        for model, col, pat in [
            (Certification, Certification.title, f"{PREFIX}%"),
            (CollectionItem, CollectionItem.note, "%sample-demo%"),
            (Thesis, Thesis.title, f"{PREFIX}%"),
            (Post, Post.title, f"{PREFIX}%"),
            (ProsePage, ProsePage.slug, "sample-%"),
        ]:
            for row in (await session.scalars(select(model).where(col.like(pat)))).all():
                await session.delete(row)
                n += 1
        await session.commit()
        print(f"removed {n} sample rows")


async def seed() -> None:
    async with async_session_factory() as session:
        for i, (t, issuer, kind, issued, exp, tags, aud) in enumerate(CERTS):
            title = PREFIX + t
            await _upsert(
                session,
                Certification,
                "title",
                title,
                {
                    "issuer": issuer,
                    "kind": CertKind(kind),
                    "issued_date": issued,
                    "expires_date": exp,
                    "credential_url": "https://example.com/credential",
                    "audience_override": aud,
                    "sort_order": i,
                    "topic_tags": await _tags(session, tags),
                },
            )
        for i, (t, creator, kind, section, st, note) in enumerate(COLLECTION):
            title = t if t.startswith("Sample") else PREFIX + t
            await _upsert(
                session,
                CollectionItem,
                "title",
                title,
                {
                    "creator": creator,
                    "kind": CollectionKind(kind),
                    "section": section,
                    "status_": CollectionStatus(st),
                    "note": f"{note} [sample-demo]",
                    "external_source": ExternalSource.MANUAL,
                    "sort_order": i,
                },
            )
        for i, (t, summ, d, tags, aud) in enumerate(THESIS):
            await _upsert(
                session,
                Thesis,
                "title",
                PREFIX + t,
                {
                    "summary": summ,
                    "drive_url": "https://docs.google.com/document/d/sample",
                    "published_date": d,
                    "audience_override": aud,
                    "sort_order": i,
                    "topic_tags": await _tags(session, tags),
                },
            )
        for i, (t, summ, plat, coll, tags, aud) in enumerate(POSTS):
            await _upsert(
                session,
                Post,
                "title",
                PREFIX + t,
                {
                    "summary": summ,
                    "url": "https://example.com/post",
                    "platform": plat,
                    "published_date": _d(2025, 1 + i % 12, 10),
                    "collections": [coll],
                    "audience_override": aud,
                    "sort_order": i,
                    "topic_tags": await _tags(session, tags),
                },
            )
        for i, (slug, title, group, aud, cta) in enumerate(PROSE):
            await _upsert(
                session,
                ProsePage,
                "slug",
                slug,
                {
                    "title": title,
                    "body": LOREM,
                    "group": group,
                    "audience_override": aud,
                    "cta_label": cta[0] if cta else None,
                    "cta_url": cta[1] if cta else None,
                    "sort_order": i,
                },
            )
        await session.commit()
        print(
            f"seeded: {len(CERTS)} certs, {len(COLLECTION)} collection items, "
            f"{len(THESIS)} thesis, {len(POSTS)} posts, {len(PROSE)} prose pages"
        )


if __name__ == "__main__":
    _guard()
    asyncio.run(remove() if "--remove" in sys.argv else seed())
