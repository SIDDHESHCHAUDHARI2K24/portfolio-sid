"""Collections: API tests covering CRUD, draft exclusion, kind/section handling."""

import httpx
import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app.core import email
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
async def clean_collections(db_engine: AsyncEngine) -> None:
    async with db_engine.begin() as conn:
        await conn.execute(text("DELETE FROM collection_items"))


@pytest.mark.asyncio
async def test_public_list_excludes_drafts(
    client: httpx.AsyncClient,
    session: AsyncSession,
    clean_collections: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await _login(client, monkeypatch)

    draft = {
        "title": "Draft Book",
        "kind": "book",
        "publish_status": "draft",
    }
    resp = await client.post("http://test/api/v1/admin/collections", json=draft)
    assert resp.status_code == 201

    published = {
        "title": "Published Book",
        "kind": "book",
        "publish_status": "published",
    }
    resp = await client.post("http://test/api/v1/admin/collections", json=published)
    assert resp.status_code == 201

    resp = await client.get("http://test/api/v1/collections")
    assert resp.status_code == 200
    data = resp.json()
    titles = {item["title"] for item in data}
    assert "Draft Book" not in titles
    assert "Published Book" in titles


@pytest.mark.asyncio
async def test_all_three_kinds_persist(
    client: httpx.AsyncClient,
    session: AsyncSession,
    clean_collections: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await _login(client, monkeypatch)

    book = {
        "title": "Test Book",
        "creator": "Test Author",
        "kind": "book",
        "section": "Tech",
        "status": "completed",
        "sort_order": 0,
        "publish_status": "published",
    }
    resp = await client.post("http://test/api/v1/admin/collections", json=book)
    assert resp.status_code == 201

    anime = {
        "title": "Test Anime",
        "creator": "Test Studio",
        "kind": "anime",
        "status": "reading",
        "publish_status": "published",
    }
    resp = await client.post("http://test/api/v1/admin/collections", json=anime)
    assert resp.status_code == 201

    manhwa = {
        "title": "Test Manhwa",
        "creator": "Test Artist",
        "kind": "manhwa",
        "status": "want_to_read",
        "publish_status": "published",
    }
    resp = await client.post("http://test/api/v1/admin/collections", json=manhwa)
    assert resp.status_code == 201

    resp = await client.get("http://test/api/v1/collections")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 3

    kinds = {item["kind"] for item in data}
    assert kinds == {"book", "anime", "manhwa"}

    book_item = next(i for i in data if i["kind"] == "book")
    assert book_item["section"] == "Tech"
    assert book_item["creator"] == "Test Author"
    assert book_item["status"] == "completed"

    anime_item = next(i for i in data if i["kind"] == "anime")
    assert anime_item["section"] is None

    manhwa_item = next(i for i in data if i["kind"] == "manhwa")
    assert manhwa_item["section"] is None


@pytest.mark.asyncio
async def test_admin_crud(
    client: httpx.AsyncClient,
    clean_collections: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await _login(client, monkeypatch)

    payload = {
        "title": "CRUD Test",
        "kind": "book",
        "section": "Business",
        "publish_status": "published",
    }
    resp = await client.post("http://test/api/v1/admin/collections", json=payload)
    assert resp.status_code == 201
    item = resp.json()
    assert item["title"] == "CRUD Test"
    item_id = item["id"]

    resp = await client.patch(
        f"http://test/api/v1/admin/collections/{item_id}",
        json={"title": "Updated Title", "section": "Tech"},
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "Updated Title"
    assert resp.json()["section"] == "Tech"

    resp = await client.delete(f"http://test/api/v1/admin/collections/{item_id}")
    assert resp.status_code == 204

    resp = await client.get(f"http://test/api/v1/admin/collections/{item_id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_public_unauthorized(
    client: httpx.AsyncClient,
) -> None:
    resp = await client.post(
        "http://test/api/v1/admin/collections", json={"title": "Hack", "kind": "book"}
    )
    assert resp.status_code == 401
