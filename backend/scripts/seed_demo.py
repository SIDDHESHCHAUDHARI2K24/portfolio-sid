"""Local-only demo seed: realistic sample content for every public category.

Idempotent: each row is upserted by natural key (certifications/thesis/external
posts by title, collections by real title, prose and native posts by slug).
Collection samples keep their real titles (so cover lookups match) and are
marked by ``[sample-demo]`` in the note; the other samples start with
``Sample —`` or use a ``sample-`` slug. ``--remove`` deletes only those rows.

Refuses to run unless ENVIRONMENT is development/local AND the database host
is localhost/127.0.0.1 AND the database name starts with ``portfolio`` (never
``railway``) -- checked on the URL up front and again at runtime with
``SELECT current_database()``, so a production DB tunnelled to localhost
(``railway connect Postgres --tunnel-only``) is refused.

Collection rows are only ever updated when they carry the ``[sample-demo]``
marker; a real (unmarked) row with the same title is left alone and reported.

Usage:
    uv run python scripts/seed_demo.py                   # seed / refresh, with covers
    uv run python scripts/seed_demo.py --no-covers       # skip cover network lookups
    uv run python scripts/seed_demo.py --remove          # delete only the samples
    uv run python scripts/seed_demo.py --revalidate-url http://localhost:24735
        # then POSTs /api/revalidate (needs REVALIDATION_SECRET in the env)
"""

import argparse
import asyncio
import datetime as dt
import os
import sys
from pathlib import Path
from typing import Any

_backend_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_backend_root))

import httpx  # noqa: E402
from sqlalchemy import or_, select, text  # noqa: E402
from sqlalchemy.engine import make_url  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.core.database import async_session_factory  # noqa: E402
from app.core.enums import Audience, PublishStatus  # noqa: E402
from app.core.models import TopicTag  # noqa: E402
from app.core.storage import get_storage  # noqa: E402
from app.features.certifications.models import Certification, CertKind  # noqa: E402
from app.features.collections.covers import fetch_and_store_cover  # noqa: E402
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
MARKER = "[sample-demo]"
TOUCHED_TAGS = ["certifications", "collections", "posts", "prose", "thesis"]
NOW = dt.datetime.now(dt.UTC)
A = Audience


DB_NAME_PREFIX = "portfolio"
FORBIDDEN_DB_NAMES = {"railway"}


def _db_name_problem(name: str | None) -> str | None:
    if not name or name.lower() in FORBIDDEN_DB_NAMES or not name.startswith(DB_NAME_PREFIX):
        return f"database name {name!r} must start with {DB_NAME_PREFIX!r} (and not be 'railway')"
    return None


def guard_problem(environment: str, database_url: str) -> str | None:
    """Return why seeding must be refused for this config, or None if it is allowed."""
    url = make_url(database_url)
    if environment not in {"development", "local"}:
        return f"environment={environment!r} (need development/local)"
    if url.host not in {"localhost", "127.0.0.1"}:
        return f"db host={url.host!r} (need localhost/127.0.0.1)"
    return _db_name_problem(url.database)


def _guard() -> None:
    settings = get_settings()
    problem = guard_problem(settings.environment, settings.database_url)
    if problem:
        sys.exit(f"refusing to seed: {problem}")


async def _guard_runtime(session: AsyncSession) -> None:
    """Ask the server which database we are really connected to (tunnels, aliases)."""
    actual = await session.scalar(text("SELECT current_database()"))
    problem = _db_name_problem(actual)
    if problem:
        await session.rollback()
        sys.exit(f"refusing to seed: connected {problem}")


async def _tags(session: AsyncSession, slugs: list[str]) -> list[TopicTag]:
    if not slugs:
        return []
    rows = (await session.scalars(select(TopicTag).where(TopicTag.slug.in_(slugs)))).all()
    missing = set(slugs) - {t.slug for t in rows}
    if missing:
        print(f"  warn: unknown topic tags skipped: {sorted(missing)}")
    return list(rows)


def _apply(row: Any, data: dict[str, Any]) -> None:
    for k, v in data.items():
        setattr(row, k, v)
    row.status = PublishStatus.PUBLISHED
    row.published_at = row.published_at or NOW


async def _upsert(
    session: AsyncSession, model: Any, key: str, value: str, data: dict[str, Any]
) -> None:
    row = await session.scalar(select(model).where(getattr(model, key) == value))
    if row is None:
        row = model(**{key: value})
        session.add(row)
    _apply(row, data)


def _is_marked(item: CollectionItem) -> bool:
    return MARKER in (item.note or "")


async def _upsert_collection(session: AsyncSession, title: str, data: dict[str, Any]) -> bool:
    """Upsert a sample collection row by title AND marker.

    Returns False (and touches nothing) when an unmarked row with this title exists:
    that is real content and must never be modified by the demo seed.
    """
    rows = (
        await session.scalars(select(CollectionItem).where(CollectionItem.title == title))
    ).all()
    marked = [r for r in rows if _is_marked(r)]
    if marked:
        _apply(marked[0], data)
        return True
    if rows:
        return False
    row = CollectionItem(title=title)
    session.add(row)
    _apply(row, data)
    return True


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

# (title, creator, kind, section, status, note). Real titles so cover lookups match.
COLLECTION: list[tuple[str, str, str, str, str, str]] = [
    ("Zero to One", "Peter Thiel", "book", "Startups", "completed", "Contrarian company building."),
    (
        "The Mom Test",
        "Rob Fitzpatrick",
        "book",
        "Startups",
        "completed",
        "Customer talks done right.",
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
        "The Pragmatic Programmer",
        "Andrew Hunt",
        "book",
        "Engineering",
        "completed",
        "Craft over cleverness.",
    ),
    ("Shape Up", "Ryan Singer", "book", "Product", "want_to_read", "Six-week cycles, no backlog."),
    (
        "Frieren: Beyond Journey's End",
        "Madhouse",
        "anime",
        "Fantasy",
        "completed",
        "Quiet and beautiful.",
    ),
    ("Steins;Gate", "White Fox", "anime", "Sci-Fi", "completed", "Time travel done properly."),
    ("Haikyuu!!", "Production I.G", "anime", "Sports", "completed", "Pure team energy."),
    (
        "Vinland Saga",
        "Wit Studio",
        "anime",
        "Historical",
        "reading",
        "A saga about unlearning war.",
    ),
    ("Solo Leveling", "Chugong", "manhwa", "Action", "completed", "The one that started it."),
    (
        "Omniscient Reader's Viewpoint",
        "Sing Shong",
        "manhwa",
        "Action",
        "reading",
        "Story-within-a-story.",
    ),
    ("Tower of God", "SIU", "manhwa", "Fantasy", "reading", "Sprawling world-building."),
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

_CODE_AI = """```python
def review(diff: str) -> str:
    prompt = f"Review this diff for bugs, not style:\\n{diff}"
    return agent.run(prompt)
```"""

# (slug, title, summary, collection, tags, audiences, body)
NATIVE_POSTS: list[tuple[str, str, str, PostCollection, list[str], list[A] | None, str]] = [
    (
        "sample-how-i-pair-with-agents",
        "How I pair with coding agents",
        "A small, repeatable loop for shipping with an AI pair.",
        PostCollection.HOW_I_USE_AI,
        ["ai", "agentic-ai"],
        [A.TECHIES, A.RECRUITERS],
        """I treat an agent like a fast junior who never gets tired but needs a clear brief. \
The loop below is boring on purpose, and that is why it works.

## The loop

Every task goes through the same four steps:

- Write the goal and the acceptance check in two sentences.
- Let the agent propose a plan, and edit the plan before any code exists.
- Run the change in small slices, with tests after each slice.
- Read the whole diff myself before it merges.

## Keep prompts small and testable

A review prompt is a function, not a conversation. Pass in the diff, ask one \
question, and demand a structured answer:

"""
        + _CODE_AI
        + """

## What goes wrong

Agents drift when the brief is vague, so I spend most of my effort on the first \
paragraph of the task. They also happily over-build, so I state the stop \
condition up front: "done means the failing test passes and nothing else changes."

When something surprises me, I do not argue with the agent. I rewrite the brief \
and rerun it. That keeps every attempt comparable, and it makes the lesson stick \
in the written task rather than in my head.

## Further reading

The best short guide I have found on structuring agent work is the \
[Anthropic agents guide](https://www.anthropic.com/engineering/building-effective-agents). \
It matches my experience: start simple, add structure only when a measurement says so.

Treat this as a sample article. Swap in your own words from the admin editor.
""",
    ),
    (
        "sample-postgres-rabbit-hole",
        "Down the Postgres rabbit hole",
        "Query planners, vacuum and the one setting that fixed a slow page.",
        PostCollection.TECH_RABBITHOLE,
        ["engineering", "data-platform"],
        [A.TECHIES],
        """A slow list page sent me into the planner for a weekend. Here is the short version \
of what I found, because the detour paid for itself.

## Start with the plan

Never guess. Ask the database what it is doing:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM posts
WHERE status = 'PUBLISHED'
ORDER BY published_date DESC
LIMIT 20;
```

The output showed a sequential scan and a sort, even though an index existed.

## Three things I checked

- **Statistics:** stale stats made the planner underestimate row counts.
- **Index shape:** the index did not match the `ORDER BY`, so it could not be used.
- **Bloat:** heavy updates left dead tuples that vacuum had not reclaimed.

## The fix

A composite index on `(status, published_date DESC)` plus a manual `ANALYZE` \
turned a 180 ms query into a 2 ms one. Nothing exotic, just reading the plan \
carefully instead of adding hardware.

## Lessons

1. Read the plan before changing the schema.
2. Match indexes to the exact query, including sort order.
3. Autovacuum is a feature, but watch it on write-heavy tables.

The official [EXPLAIN documentation](https://www.postgresql.org/docs/current/using-explain.html) \
is dense but worth an hour. This is a sample article for local review; edit or \
delete it freely from the admin.
""",
    ),
    (
        "sample-fundraising-mistakes",
        "Five fundraising mistakes I keep seeing",
        "Patterns from the investor side of the table.",
        PostCollection.VC_FOR_FOUNDERS,
        ["fundraising", "venture-capital"],
        [A.FOUNDERS, A.INVESTORS],
        """After reading a lot of decks, the same mistakes show up. None of them are about the \
idea. They are about how the story is told.

## The mistakes

1. **Burying the ask.** Say how much you raise and what it buys in the first minute.
2. **Vague market claims.** "A billion-dollar market" says nothing. Name the buyer and the budget.
3. **No proof of pull.** One paying customer beats ten slides about vision.
4. **Hiding the risks.** Investors find them anyway. Naming them builds trust.
5. **Going wide on process.** Run a tight two-week window, not a six-month drift.

## A simple checklist

Before you send a deck, check that it answers these:

- Who is the customer and why do they pay now?
- What is true today that was not true a year ago?
- What does the next round of money unlock?

## Show the numbers

Keep a one-line snapshot you can paste into any email:

```text
MRR $18k | growth 14% m/m | runway 11 months | raising $1.5M seed
```

If the line is awkward to write, the business is probably not ready to pitch.

## Where to learn more

[Y Combinator's fundraising guide](https://www.ycombinator.com/library) is a solid \
starting point and free. This is a sample article for local review, so feel free \
to replace it with your own writing.
""",
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
        await _guard_runtime(session)
        n = 0
        for model, cond in [
            (Certification, Certification.title.like(f"{PREFIX}%")),
            (CollectionItem, CollectionItem.note.like(f"%{MARKER}%")),
            (Thesis, Thesis.title.like(f"{PREFIX}%")),
            (Post, or_(Post.title.like(f"{PREFIX}%"), Post.slug.like("sample-%"))),
            (ProsePage, ProsePage.slug.like("sample-%")),
        ]:
            for row in (await session.scalars(select(model).where(cond))).all():
                await session.delete(row)
                n += 1
        await session.commit()
        print(f"removed {n} sample rows")


async def _drop_stale_collection_samples(session: AsyncSession) -> int:
    """Delete marked collection rows whose title is no longer in COLLECTION (old fake titles)."""
    keep = {c[0] for c in COLLECTION}
    rows = (
        await session.scalars(select(CollectionItem).where(CollectionItem.note.like(f"%{MARKER}%")))
    ).all()
    stale = [r for r in rows if r.title not in keep]
    for r in stale:
        await session.delete(r)
    return len(stale)


async def _fill_covers(session: AsyncSession) -> tuple[int, list[str]]:
    """Fetch covers for marked items lacking one. Returns (found, failed titles)."""
    items = (
        await session.scalars(
            select(CollectionItem).where(
                CollectionItem.note.like(f"%{MARKER}%"), CollectionItem.cover_key.is_(None)
            )
        )
    ).all()
    found, failed = 0, []
    adapter = get_storage()
    async with httpx.AsyncClient(
        timeout=15, headers={"User-Agent": "portfolio-seed-demo/1.0"}
    ) as client:
        for item in items:
            kind = item.kind.value if hasattr(item.kind, "value") else str(item.kind)
            try:
                result = await fetch_and_store_cover(item.title, kind, adapter, client)
            except Exception as exc:  # network is best effort
                print(f"  cover error for {item.title!r}: {exc}")
                result = None
            if result is not None and result.status == "found":
                item.cover_key = result.cover_key
                found += 1
            else:
                failed.append(item.title)
            await asyncio.sleep(0.5)  # stay under Jikan's rate limit
    return found, failed


async def seed(*, covers: bool = True) -> list[str]:
    async with async_session_factory() as session:
        await _guard_runtime(session)
        stale = await _drop_stale_collection_samples(session)
        skipped: list[str] = []
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
            written = await _upsert_collection(
                session,
                t,
                {
                    "creator": creator,
                    "kind": CollectionKind(kind),
                    "section": section,
                    "status_": CollectionStatus(st),
                    "note": f"{note} {MARKER}",
                    "external_source": ExternalSource.MANUAL,
                    "sort_order": i,
                },
            )
            if not written:
                skipped.append(t)
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
        for i, (slug, title, summ, coll, tags, aud, body) in enumerate(NATIVE_POSTS):
            await _upsert(
                session,
                Post,
                "slug",
                slug,
                {
                    "title": title,
                    "summary": summ,
                    "body": body,
                    "url": None,
                    "platform": PostPlatform.INTERNAL,
                    "published_date": _d(2026, 9, 1 + i),
                    "collections": [coll],
                    "audience_override": aud,
                    "sort_order": 100 + i,
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
        await session.flush()
        failed: list[str] = []
        found = 0
        if covers:
            found, failed = await _fill_covers(session)
        await session.commit()
        print(
            f"seeded: {len(CERTS)} certs, {len(COLLECTION)} collection items, "
            f"{len(THESIS)} thesis, {len(POSTS)} external posts, "
            f"{len(NATIVE_POSTS)} native posts, {len(PROSE)} prose pages "
            f"(dropped {stale} stale old collection samples)"
        )
        if skipped:
            print(
                f"skipped {len(skipped)} collection samples: a real (unmarked) row with the "
                f"same title exists and was left untouched: {skipped}"
            )
        if covers:
            print(f"covers: {found} fetched this run")
            print(f"cover lookups failed: {failed or 'none'}")
        else:
            print("covers: skipped (--no-covers)")
        return failed


def revalidate(url: str | None) -> None:
    """POST the frontend revalidate route, or print the curl to run."""
    secret = os.environ.get("REVALIDATION_SECRET")
    body = '{"tags": ' + str(TOUCHED_TAGS).replace("'", '"') + "}"
    if not url or not secret:
        target = url or "<frontend-url>"
        print(
            "revalidate manually:\n  curl -X POST "
            f"{target}/api/revalidate -H 'content-type: application/json' "
            f"-H 'x-revalidation-secret: $REVALIDATION_SECRET' -d '{body}'"
        )
        return
    try:
        resp = httpx.post(
            f"{url.rstrip('/')}/api/revalidate",
            json={"tags": TOUCHED_TAGS},
            headers={"x-revalidation-secret": secret},
            timeout=15,
        )
        print(f"revalidate {resp.status_code}: {resp.text.strip()[:120]}")
    except httpx.HTTPError as exc:
        print(f"revalidate failed: {exc}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    parser.add_argument("--remove", action="store_true", help="delete only the samples")
    parser.add_argument("--no-covers", action="store_true", help="skip cover network lookups")
    parser.add_argument("--revalidate-url", help="frontend base URL to POST /api/revalidate")
    args = parser.parse_args()
    _guard()
    if args.remove:
        asyncio.run(remove())
    else:
        asyncio.run(seed(covers=not args.no_covers))
    revalidate(args.revalidate_url)


if __name__ == "__main__":
    main()
