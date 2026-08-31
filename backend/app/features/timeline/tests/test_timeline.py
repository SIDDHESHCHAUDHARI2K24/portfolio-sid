"""Timeline: full API suite with auth assertions, draft-leak guards, query-count check."""

from collections.abc import AsyncIterator, Sequence
from datetime import UTC, date, datetime, timedelta

import httpx
import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app.core import email
from app.core.config import Settings
from app.core.enums import PublishStatus
from app.features.timeline.endpoints import router as timeline_router
from app.features.timeline.models import TimelineEntry, TimelineKind
from app.tests.helpers import TEST_ADMIN_PASSWORD


async def _login(client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
    sent: list[str] = []

    async def fake_send_otp(code: str, to: str) -> None:
        sent.append(code)

    monkeypatch.setattr(email, "send_otp", fake_send_otp)
    resp = await client.post(
        "http://test/api/v1/auth/login", json={"password": TEST_ADMIN_PASSWORD}
    )
    assert resp.status_code == 200
    resp = await client.post("http://test/api/v1/auth/verify", json={"code": sent[0]})
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(loop_scope="session")
async def clean_timeline_tables(db_engine: AsyncEngine) -> None:
    async with db_engine.begin() as conn:
        await conn.execute(text("DELETE FROM timeline_topic_tags"))
        await conn.execute(text("DELETE FROM timeline_entries"))


@pytest_asyncio.fixture
async def seeded_tags(db_engine: AsyncEngine) -> AsyncIterator[list[str]]:
    slugs = ["engineering", "ai", "consulting"]
    async with db_engine.begin() as conn:
        for slug in slugs:
            await conn.execute(
                text(
                    "INSERT INTO topic_tags (id, slug, label) "
                    "VALUES (gen_random_uuid(), :slug, :label) "
                    "ON CONFLICT (slug) DO NOTHING"
                ),
                {"slug": slug, "label": slug.capitalize()},
            )
    yield slugs
    async with db_engine.begin() as conn:
        for slug in slugs:
            await conn.execute(
                text("DELETE FROM topic_tags WHERE slug = :slug"),
                {"slug": slug},
            )


# ---------------------------------------------------------------------------
# public endpoint tests
# ---------------------------------------------------------------------------


async def test_public_list_excludes_drafts(
    client: httpx.AsyncClient,
    session: AsyncSession,
    clean_timeline_tables: None,
    seeded_tags: list[str],
) -> None:
    published = TimelineEntry(
        kind=TimelineKind.EXPERIENCE,
        title="Published role",
        organisation="ACME",
        start_date=date(2023, 1, 1),
        status=PublishStatus.PUBLISHED,
        published_at=datetime.now(UTC),
    )
    draft = TimelineEntry(
        kind=TimelineKind.EDUCATION,
        title="Draft degree",
        organisation="MIT",
        start_date=date(2020, 1, 1),
        status=PublishStatus.DRAFT,
    )
    session.add_all([published, draft])
    await session.commit()

    response = await client.get("http://test/api/v1/timeline")
    assert response.status_code == 200
    data = response.json()
    titles = [e["title"] for e in data]
    assert "Published role" in titles
    assert "Draft degree" not in titles


async def test_public_list_excludes_future_scheduled(
    client: httpx.AsyncClient,
    session: AsyncSession,
    clean_timeline_tables: None,
) -> None:
    now = datetime.now(UTC)
    future_scheduled = TimelineEntry(
        kind=TimelineKind.EXPERIENCE,
        title="Future job",
        organisation="NEXT",
        start_date=date(2025, 6, 1),
        status=PublishStatus.SCHEDULED,
        publish_at=now + timedelta(days=30),
    )
    due_scheduled = TimelineEntry(
        kind=TimelineKind.EXPERIENCE,
        title="Past job",
        organisation="PAST",
        start_date=date(2022, 1, 1),
        status=PublishStatus.SCHEDULED,
        publish_at=now - timedelta(days=1),
    )
    session.add_all([future_scheduled, due_scheduled])
    await session.commit()

    response = await client.get("http://test/api/v1/timeline")
    titles = [e["title"] for e in response.json()]
    assert "Past job" in titles
    assert "Future job" not in titles


async def test_public_entry_not_found_returns_404(client: httpx.AsyncClient) -> None:
    response = await client.get("http://test/api/v1/timeline/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


async def test_public_detail_excludes_draft(
    client: httpx.AsyncClient,
    session: AsyncSession,
    clean_timeline_tables: None,
) -> None:
    draft = TimelineEntry(
        kind=TimelineKind.EXPERIENCE,
        title="Draft hidden",
        organisation="HIDDEN",
        start_date=date(2023, 1, 1),
        status=PublishStatus.DRAFT,
    )
    session.add(draft)
    await session.commit()

    response = await client.get(f"http://test/api/v1/timeline/{draft.id}")
    assert response.status_code == 404


async def test_public_detail_excludes_future_scheduled(
    client: httpx.AsyncClient,
    session: AsyncSession,
    clean_timeline_tables: None,
) -> None:
    future = TimelineEntry(
        kind=TimelineKind.EXPERIENCE,
        title="Future scheduled hidden",
        organisation="FUTURE",
        start_date=date(2025, 1, 1),
        status=PublishStatus.SCHEDULED,
        publish_at=datetime.now(UTC) + timedelta(days=30),
    )
    session.add(future)
    await session.commit()

    response = await client.get(f"http://test/api/v1/timeline/{future.id}")
    assert response.status_code == 404


async def test_public_detail_returns_published(
    client: httpx.AsyncClient,
    session: AsyncSession,
    clean_timeline_tables: None,
) -> None:
    published = TimelineEntry(
        kind=TimelineKind.EXPERIENCE,
        title="Public detail visible",
        organisation="VISIBLE",
        start_date=date(2022, 1, 1),
        status=PublishStatus.PUBLISHED,
        published_at=datetime.now(UTC),
    )
    session.add(published)
    await session.commit()

    response = await client.get(f"http://test/api/v1/timeline/{published.id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Public detail visible"


async def test_admin_detail_returns_draft(
    client: httpx.AsyncClient,
    session: AsyncSession,
    clean_timeline_tables: None,
    clean_auth_tables: None,
    admin_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await _login(client, monkeypatch)
    draft = TimelineEntry(
        kind=TimelineKind.EXPERIENCE,
        title="Admin draft visible",
        organisation="ADMIN",
        start_date=date(2023, 6, 1),
        status=PublishStatus.DRAFT,
    )
    session.add(draft)
    await session.commit()

    response = await client.get(f"http://test/api/v1/admin/timeline/{draft.id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Admin draft visible"


async def test_public_timeline_projects_filters(
    client: httpx.AsyncClient,
    session: AsyncSession,
    clean_timeline_tables: None,
) -> None:
    from app.features.projects.models import Project

    # Need to clean projects tables as well for isolation
    await session.execute(text("DELETE FROM project_topic_tags"))
    await session.execute(text("DELETE FROM project_attachments"))
    await session.execute(text("DELETE FROM projects"))
    await session.commit()

    timeline_entry = TimelineEntry(
        kind=TimelineKind.EXPERIENCE,
        title="Timeline with projects",
        organisation="ORG",
        start_date=date(2022, 1, 1),
        status=PublishStatus.PUBLISHED,
        published_at=datetime.now(UTC),
    )
    session.add(timeline_entry)
    await session.flush()

    published_proj = Project(
        title="Published proj",
        slug="published-proj-timeline",
        status=PublishStatus.PUBLISHED,
        published_at=datetime.now(UTC),
        timeline_entry_id=timeline_entry.id,
    )
    draft_proj = Project(
        title="Draft proj",
        slug="draft-proj-timeline",
        status=PublishStatus.DRAFT,
        timeline_entry_id=timeline_entry.id,
    )
    other_timeline_proj = Project(
        title="Other timeline proj",
        slug="other-timeline-proj",
        status=PublishStatus.PUBLISHED,
        published_at=datetime.now(UTC),
        timeline_entry_id=None,
    )
    session.add_all([published_proj, draft_proj, other_timeline_proj])
    await session.commit()

    response = await client.get(f"http://test/api/v1/timeline/{timeline_entry.id}/projects")
    assert response.status_code == 200
    titles = [p["title"] for p in response.json()]
    assert "Published proj" in titles
    assert "Draft proj" not in titles
    assert "Other timeline proj" not in titles

    # Draft timeline entry should 404 even if projects exist
    draft_entry = TimelineEntry(
        kind=TimelineKind.EXPERIENCE,
        title="Draft entry",
        organisation="DRAFTORG",
        start_date=date(2023, 1, 1),
        status=PublishStatus.DRAFT,
    )
    session.add(draft_entry)
    await session.commit()
    response2 = await client.get(f"http://test/api/v1/timeline/{draft_entry.id}/projects")
    assert response2.status_code == 404


async def test_public_responses_omit_status_and_overrides(
    client: httpx.AsyncClient,
    session: AsyncSession,
    clean_timeline_tables: None,
) -> None:
    entry = TimelineEntry(
        kind=TimelineKind.EXPERIENCE,
        title="Public shape test",
        organisation="TEST",
        start_date=date(2021, 1, 1),
        status=PublishStatus.PUBLISHED,
        published_at=datetime.now(UTC),
        audience_override=["recruiters"],
    )
    session.add(entry)
    await session.commit()

    response = await client.get("http://test/api/v1/timeline")
    data = response.json()
    item = data[0]
    assert "status" not in item
    assert "publish_at" not in item
    assert "audience_override" not in item


# ---------------------------------------------------------------------------
# admin endpoint tests
# ---------------------------------------------------------------------------


async def test_admin_routes_require_auth(client: httpx.AsyncClient) -> None:
    assert (await client.get("http://test/api/v1/admin/timeline")).status_code == 401
    assert (
        await client.post(
            "http://test/api/v1/admin/timeline",
            json={
                "kind": "experience",
                "title": "Unauthorized",
                "organisation": "HACK",
                "start_date": "2023-01-01",
            },
        )
    ).status_code == 401


async def test_admin_crud_lifecycle(
    client: httpx.AsyncClient,
    session: AsyncSession,
    clean_timeline_tables: None,
    seeded_tags: list[str],
    clean_auth_tables: None,
    admin_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await _login(client, monkeypatch)

    create_resp = await client.post(
        "http://test/api/v1/admin/timeline",
        json={
            "kind": "experience",
            "title": "Software Engineer",
            "organisation": "ACME Corp",
            "start_date": "2023-01-15",
            "tag_slugs": ["engineering"],
        },
    )
    assert create_resp.status_code == 201
    created = create_resp.json()
    assert created["title"] == "Software Engineer"
    assert created["kind"] == "experience"
    assert created["status"] == "draft"
    assert created["topic_tags"][0]["slug"] == "engineering"

    entry_id = created["id"]

    get_resp = await client.get(f"http://test/api/v1/admin/timeline/{entry_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["title"] == "Software Engineer"

    update_resp = await client.patch(
        f"http://test/api/v1/admin/timeline/{entry_id}",
        json={"title": "Senior Software Engineer", "status": "published"},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["title"] == "Senior Software Engineer"
    assert update_resp.json()["status"] == "published"

    delete_resp = await client.delete(f"http://test/api/v1/admin/timeline/{entry_id}")
    assert delete_resp.status_code == 204

    assert (await client.get(f"http://test/api/v1/admin/timeline/{entry_id}")).status_code == 404


async def test_create_with_invalid_dates_returns_422(
    client: httpx.AsyncClient,
    clean_auth_tables: None,
    admin_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await _login(client, monkeypatch)

    response = await client.post(
        "http://test/api/v1/admin/timeline",
        json={
            "kind": "education",
            "title": "Bad dates",
            "organisation": "UNI",
            "start_date": "2025-01-01",
            "end_date": "2024-01-01",
        },
    )
    assert response.status_code == 422


async def test_create_with_unknown_tag_returns_422(
    client: httpx.AsyncClient,
    clean_timeline_tables: None,
    clean_auth_tables: None,
    admin_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await _login(client, monkeypatch)

    response = await client.post(
        "http://test/api/v1/admin/timeline",
        json={
            "kind": "experience",
            "title": "Bad tag",
            "organisation": "X",
            "start_date": "2023-01-01",
            "tag_slugs": ["nonexistent_tag_12345"],
        },
    )
    assert response.status_code == 422


async def test_revalidation_fires_after_create(
    client: httpx.AsyncClient,
    session: AsyncSession,
    clean_timeline_tables: None,
    clean_auth_tables: None,
    admin_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[list[str]] = []

    async def fake_revalidate(tags: Sequence[str]) -> None:
        calls.append(list(tags))

    monkeypatch.setattr(timeline_router, "revalidate", fake_revalidate)
    await _login(client, monkeypatch)

    response = await client.post(
        "http://test/api/v1/admin/timeline",
        json={
            "kind": "experience",
            "title": "Revalidation test",
            "organisation": "T",
            "start_date": "2023-01-01",
        },
    )
    assert response.status_code == 201
    assert calls == [["timeline", "projects"]]


async def test_null_end_date_means_current(
    client: httpx.AsyncClient,
    session: AsyncSession,
    clean_timeline_tables: None,
    clean_auth_tables: None,
    admin_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await _login(client, monkeypatch)

    response = await client.post(
        "http://test/api/v1/admin/timeline",
        json={
            "kind": "experience",
            "title": "Current role",
            "organisation": "ACME",
            "start_date": "2023-01-01",
            "status": "published",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["end_date"] is None
    assert data["status"] == "published"
    assert data["published_at"] is not None
