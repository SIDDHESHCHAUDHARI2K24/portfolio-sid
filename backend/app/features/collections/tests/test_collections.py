"""Collections: API tests covering CRUD, draft exclusion, kind/section handling."""

import httpx
import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app.core import email
from app.features.collections import service
from app.features.collections.covers import CoverResult
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


class _CoverSpy:
    """Replaces service.fetch_and_store_cover; never touches the network."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []
        self.result: CoverResult | Exception = CoverResult(status="no_match")

    async def __call__(self, title: str, kind: str, adapter: object, client: object) -> CoverResult:
        self.calls.append((title, kind))
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


@pytest.fixture(autouse=True)
def cover_spy(monkeypatch: pytest.MonkeyPatch) -> _CoverSpy:
    spy = _CoverSpy()
    monkeypatch.setattr(service, "fetch_and_store_cover", spy)
    return spy


_URL = "http://test/api/v1/admin/collections"


async def _create(client: httpx.AsyncClient, **extra: object) -> dict[str, object]:
    body = {"title": "Dune", "kind": "book", "publish_status": "published", **extra}
    resp = await client.post(_URL, json=body)
    assert resp.status_code == 201, resp.text
    data: dict[str, object] = resp.json()
    return data


@pytest.mark.asyncio
async def test_cover_url_present_when_key_set(
    client: httpx.AsyncClient, clean_collections: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    await _login(client, monkeypatch)
    created = await _create(client, cover_key="book-abc.jpg")
    assert str(created["cover_url"]).endswith("book-abc.jpg")
    pub = (await client.get("http://test/api/v1/collections")).json()
    assert str(pub[0]["cover_url"]).endswith("book-abc.jpg")
    assert pub[0]["cover_key"] == "book-abc.jpg"


@pytest.mark.asyncio
async def test_cover_url_null_without_key(
    client: httpx.AsyncClient, clean_collections: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    await _login(client, monkeypatch)
    created = await _create(client)
    assert created["cover_key"] is None
    assert created["cover_url"] is None


@pytest.mark.asyncio
async def test_create_triggers_one_lookup_and_sets_cover(
    client: httpx.AsyncClient,
    clean_collections: None,
    monkeypatch: pytest.MonkeyPatch,
    cover_spy: _CoverSpy,
) -> None:
    await _login(client, monkeypatch)
    cover_spy.result = CoverResult(status="found", cover_key="book-123.jpg")
    created = await _create(client)
    assert cover_spy.calls == [("Dune", "book")]
    assert created["cover_key"] == "book-123.jpg"
    assert str(created["cover_url"]).endswith("book-123.jpg")


@pytest.mark.asyncio
async def test_create_with_explicit_cover_skips_lookup(
    client: httpx.AsyncClient,
    clean_collections: None,
    monkeypatch: pytest.MonkeyPatch,
    cover_spy: _CoverSpy,
) -> None:
    await _login(client, monkeypatch)
    await _create(client, cover_key="mine.jpg")
    assert cover_spy.calls == []


@pytest.mark.asyncio
async def test_update_with_existing_cover_does_not_lookup(
    client: httpx.AsyncClient,
    clean_collections: None,
    monkeypatch: pytest.MonkeyPatch,
    cover_spy: _CoverSpy,
) -> None:
    await _login(client, monkeypatch)
    created = await _create(client, cover_key="mine.jpg")
    resp = await client.patch(f"{_URL}/{created['id']}", json={"title": "Dune Messiah"})
    assert resp.status_code == 200
    assert resp.json()["cover_key"] == "mine.jpg"
    assert cover_spy.calls == []


@pytest.mark.asyncio
async def test_update_without_cover_triggers_lookup(
    client: httpx.AsyncClient,
    clean_collections: None,
    monkeypatch: pytest.MonkeyPatch,
    cover_spy: _CoverSpy,
) -> None:
    await _login(client, monkeypatch)
    created = await _create(client)
    assert len(cover_spy.calls) == 1
    cover_spy.result = CoverResult(status="found", cover_key="book-9.jpg")
    resp = await client.patch(f"{_URL}/{created['id']}", json={"title": "Dune 2"})
    assert resp.status_code == 200
    assert cover_spy.calls[-1] == ("Dune 2", "book")
    assert resp.json()["cover_key"] == "book-9.jpg"


@pytest.mark.asyncio
@pytest.mark.parametrize("status", ["failed", "no_match"])
async def test_lookup_failed_or_no_match_saves_without_cover(
    status: str,
    client: httpx.AsyncClient,
    clean_collections: None,
    monkeypatch: pytest.MonkeyPatch,
    cover_spy: _CoverSpy,
) -> None:
    await _login(client, monkeypatch)
    cover_spy.result = CoverResult(status=status)
    created = await _create(client)
    assert created["cover_key"] is None
    assert created["cover_url"] is None


@pytest.mark.asyncio
async def test_lookup_exception_saves_without_5xx(
    client: httpx.AsyncClient,
    clean_collections: None,
    monkeypatch: pytest.MonkeyPatch,
    cover_spy: _CoverSpy,
) -> None:
    await _login(client, monkeypatch)
    cover_spy.result = httpx.ConnectTimeout("boom")
    created = await _create(client)
    assert created["cover_key"] is None
    resp = await client.patch(f"{_URL}/{created['id']}", json={"note": "x"})
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_explicit_null_cover_clears_without_refetch(
    client: httpx.AsyncClient,
    clean_collections: None,
    monkeypatch: pytest.MonkeyPatch,
    cover_spy: _CoverSpy,
) -> None:
    await _login(client, monkeypatch)
    created = await _create(client, cover_key="mine.jpg")
    cover_spy.result = CoverResult(status="found", cover_key="book-new.jpg")
    resp = await client.patch(f"{_URL}/{created['id']}", json={"cover_key": None})
    assert resp.status_code == 200
    assert resp.json()["cover_key"] is None
    assert resp.json()["cover_url"] is None
    assert cover_spy.calls == []
