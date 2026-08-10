"""Thesis: full API suite with auth, draft-leak guards, CRUD."""

from collections.abc import AsyncIterator, Sequence
from datetime import UTC, date, datetime

import httpx
import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app.core import email
from app.core.config import Settings
from app.core.enums import PublishStatus
from app.features.thesis.endpoints import router as thesis_router
from app.features.thesis.models import Thesis
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


@pytest_asyncio.fixture(loop_scope="session")
async def clean_thesis_tables(db_engine: AsyncEngine) -> None:
    async with db_engine.begin() as conn:
        await conn.execute(text("DELETE FROM thesis_topic_tags"))
        await conn.execute(text("DELETE FROM thesis_entries"))


@pytest_asyncio.fixture
async def seeded_tags(db_engine: AsyncEngine) -> AsyncIterator[list[str]]:
    slugs = ["engineering", "investing"]
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


async def test_public_list_excludes_drafts(
    client: httpx.AsyncClient,
    session: AsyncSession,
    clean_thesis_tables: None,
) -> None:
    published = Thesis(
        title="Published thesis",
        drive_url="https://drive.google.com/file/d/abc",
        published_date=date(2024, 6, 1),
        status=PublishStatus.PUBLISHED,
        published_at=datetime.now(UTC),
    )
    draft = Thesis(
        title="Draft thesis",
        drive_url="https://drive.google.com/file/d/xyz",
        published_date=date(2024, 1, 1),
        status=PublishStatus.DRAFT,
    )
    session.add_all([published, draft])
    await session.commit()

    response = await client.get("http://test/api/v1/thesis")
    assert response.status_code == 200
    data = response.json()
    titles = [t["title"] for t in data]
    assert "Published thesis" in titles
    assert "Draft thesis" not in titles


async def test_thesis_entries_render_as_cards(
    client: httpx.AsyncClient,
    session: AsyncSession,
    clean_thesis_tables: None,
) -> None:
    entry = Thesis(
        title="AI Investment Thesis",
        summary="Why AI-native startups will dominate",
        drive_url="https://drive.google.com/file/d/test123",
        published_date=date(2024, 3, 15),
        status=PublishStatus.PUBLISHED,
        published_at=datetime.now(UTC),
    )
    session.add(entry)
    await session.commit()

    response = await client.get("http://test/api/v1/thesis")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "AI Investment Thesis"
    assert data[0]["drive_url"] == "https://drive.google.com/file/d/test123"


async def test_admin_routes_require_auth(client: httpx.AsyncClient) -> None:
    assert (await client.get("http://test/api/v1/admin/thesis")).status_code == 401


async def test_admin_crud_lifecycle(
    client: httpx.AsyncClient,
    session: AsyncSession,
    clean_thesis_tables: None,
    seeded_tags: list[str],
    clean_auth_tables: None,
    admin_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_revalidate(tags: Sequence[str]) -> None:
        pass

    monkeypatch.setattr(thesis_router, "revalidate", fake_revalidate)
    await _login(client, monkeypatch)

    create_resp = await client.post(
        "http://test/api/v1/admin/thesis",
        json={
            "title": "AI Investment Thesis",
            "drive_url": "https://drive.google.com/file/d/abc",
            "published_date": "2024-06-15",
            "tag_slugs": ["investing"],
        },
    )
    assert create_resp.status_code == 201
    created = create_resp.json()
    assert created["title"] == "AI Investment Thesis"
    assert created["status"] == "draft"
    assert created["topic_tags"][0]["slug"] == "investing"

    thesis_id = created["id"]

    get_resp = await client.get(f"http://test/api/v1/admin/thesis/{thesis_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["title"] == "AI Investment Thesis"

    update_resp = await client.patch(
        f"http://test/api/v1/admin/thesis/{thesis_id}",
        json={"title": "Updated Thesis", "status": "published"},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["title"] == "Updated Thesis"
    assert update_resp.json()["status"] == "published"

    delete_resp = await client.delete(f"http://test/api/v1/admin/thesis/{thesis_id}")
    assert delete_resp.status_code == 204

    assert (await client.get(f"http://test/api/v1/admin/thesis/{thesis_id}")).status_code == 404


async def test_revalidation_fires_after_create(
    client: httpx.AsyncClient,
    session: AsyncSession,
    clean_thesis_tables: None,
    clean_auth_tables: None,
    admin_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[list[str]] = []

    async def fake_revalidate(tags: Sequence[str]) -> None:
        calls.append(list(tags))

    monkeypatch.setattr(thesis_router, "revalidate", fake_revalidate)
    await _login(client, monkeypatch)

    response = await client.post(
        "http://test/api/v1/admin/thesis",
        json={
            "title": "Test Thesis",
            "drive_url": "https://drive.google.com/file/d/test",
            "published_date": "2024-01-01",
        },
    )
    assert response.status_code == 201
    assert calls == [["thesis"]]
