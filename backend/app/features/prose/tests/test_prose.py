"""ProsePages: API tests covering CRUD, by-slug lookup, draft exclusion."""

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
async def clean_prose(db_engine: AsyncEngine) -> None:
    async with db_engine.begin() as conn:
        await conn.execute(text("DELETE FROM prose_pages"))


@pytest.mark.asyncio
async def test_public_list_excludes_drafts(
    client: httpx.AsyncClient,
    session: AsyncSession,
    clean_prose: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await _login(client, monkeypatch)

    draft = {
        "slug": "draft-page",
        "title": "Draft Page",
        "body": "Draft content.",
        "group": "hobbies",
        "status": "draft",
    }
    resp = await client.post("http://test/api/v1/admin/prose", json=draft)
    assert resp.status_code == 201

    published = {
        "slug": "published-page",
        "title": "Published Page",
        "body": "Published content.",
        "group": "hobbies",
        "status": "published",
    }
    resp = await client.post("http://test/api/v1/admin/prose", json=published)
    assert resp.status_code == 201

    resp = await client.get("http://test/api/v1/prose")
    assert resp.status_code == 200
    data = resp.json()
    titles = {item["title"] for item in data}
    assert "Draft Page" not in titles
    assert "Published Page" in titles


@pytest.mark.asyncio
async def test_all_three_groups(
    client: httpx.AsyncClient,
    session: AsyncSession,
    clean_prose: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await _login(client, monkeypatch)

    for group in ["hobbies", "work_views", "investor_intro"]:
        payload = {
            "slug": f"test-{group}",
            "title": f"Test {group}",
            "body": f"Content for {group}",
            "group": group,
            "status": "published",
        }
        resp = await client.post("http://test/api/v1/admin/prose", json=payload)
        assert resp.status_code == 201

    resp = await client.get("http://test/api/v1/prose")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 3

    groups = {item["group"] for item in data}
    assert groups == {"hobbies", "work_views", "investor_intro"}


@pytest.mark.asyncio
async def test_by_slug(
    client: httpx.AsyncClient,
    clean_prose: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await _login(client, monkeypatch)

    payload = {
        "slug": "my-hobbies",
        "title": "My Hobbies",
        "body": "I like things.",
        "group": "hobbies",
        "status": "published",
    }
    resp = await client.post("http://test/api/v1/admin/prose", json=payload)
    assert resp.status_code == 201

    resp = await client.get("http://test/api/v1/prose/slug/my-hobbies")
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "My Hobbies"
    assert data["body"] == "I like things."
    assert data["slug"] == "my-hobbies"


@pytest.mark.asyncio
async def test_slug_not_found(
    client: httpx.AsyncClient,
) -> None:
    resp = await client.get("http://test/api/v1/prose/slug/nonexistent")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_cta_appears_when_set(
    client: httpx.AsyncClient,
    clean_prose: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await _login(client, monkeypatch)

    payload = {
        "slug": "investor-intro",
        "title": "Investor Intro",
        "body": "Hello investors.",
        "group": "investor_intro",
        "cta_label": "Get in touch",
        "cta_url": "https://forms.gle/test",
        "status": "published",
    }
    resp = await client.post("http://test/api/v1/admin/prose", json=payload)
    assert resp.status_code == 201

    resp = await client.get("http://test/api/v1/prose/slug/investor-intro")
    assert resp.status_code == 200
    data = resp.json()
    assert data["cta_label"] == "Get in touch"
    assert data["cta_url"] == "https://forms.gle/test"


@pytest.mark.asyncio
async def test_admin_crud(
    client: httpx.AsyncClient,
    clean_prose: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await _login(client, monkeypatch)

    payload = {
        "slug": "crud-test",
        "title": "CRUD Test",
        "body": "Body text.",
        "group": "hobbies",
        "status": "published",
    }
    resp = await client.post("http://test/api/v1/admin/prose", json=payload)
    assert resp.status_code == 201
    page = resp.json()
    page_id = page["id"]

    resp = await client.patch(
        f"http://test/api/v1/admin/prose/{page_id}",
        json={"title": "Updated Title", "body": "Updated body."},
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "Updated Title"
    assert resp.json()["body"] == "Updated body."

    resp = await client.delete(f"http://test/api/v1/admin/prose/{page_id}")
    assert resp.status_code == 204

    resp = await client.get(f"http://test/api/v1/admin/prose/{page_id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_audience_override(
    client: httpx.AsyncClient,
    clean_prose: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await _login(client, monkeypatch)

    payload = {
        "slug": "targeted-page",
        "title": "Targeted Page",
        "body": "For specific audiences.",
        "group": "work_views",
        "audience_override": ["recruiters", "techies"],
        "status": "published",
    }
    resp = await client.post("http://test/api/v1/admin/prose", json=payload)
    assert resp.status_code == 201

    resp = await client.get("http://test/api/v1/admin/prose")
    items = resp.json()
    page = next(p for p in items if p["slug"] == "targeted-page")
    assert set(page["audience_override"]) == {"recruiters", "techies"}


@pytest.mark.asyncio
async def test_public_unauthorized(
    client: httpx.AsyncClient,
) -> None:
    resp = await client.post(
        "http://test/api/v1/admin/prose",
        json={"slug": "x", "title": "X", "body": "X", "group": "hobbies"},
    )
    assert resp.status_code == 401


async def _create_published(
    client: httpx.AsyncClient, slug: str, group: str, sort_order: int = 0
) -> None:
    payload = {
        "slug": slug,
        "title": f"Title {slug}",
        "body": f"Body {slug}",
        "group": group,
        "sort_order": sort_order,
        "status": "published",
    }
    resp = await client.post("http://test/api/v1/admin/prose", json=payload)
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_group_filter_returns_only_that_group(
    client: httpx.AsyncClient,
    clean_prose: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await _login(client, monkeypatch)
    await _create_published(client, "h-1", "hobbies")
    await _create_published(client, "h-2", "hobbies", sort_order=1)
    await _create_published(client, "w-1", "work_views")
    await _create_published(client, "i-1", "investor_intro")

    resp = await client.get("http://test/api/v1/prose?group=hobbies")
    assert resp.status_code == 200
    assert {p["slug"] for p in resp.json()} == {"h-1", "h-2"}
    assert all(p["group"] == "hobbies" for p in resp.json())

    resp = await client.get("http://test/api/v1/prose?group=work_views")
    assert resp.status_code == 200
    assert [p["slug"] for p in resp.json()] == ["w-1"]

    resp = await client.get("http://test/api/v1/prose?group=investor_intro")
    assert resp.status_code == 200
    assert [p["slug"] for p in resp.json()] == ["i-1"]


@pytest.mark.asyncio
async def test_group_filter_excludes_drafts(
    client: httpx.AsyncClient,
    clean_prose: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await _login(client, monkeypatch)
    await _create_published(client, "h-live", "hobbies")
    draft = {
        "slug": "h-draft",
        "title": "Draft",
        "body": "Draft body",
        "group": "hobbies",
        "status": "draft",
    }
    resp = await client.post("http://test/api/v1/admin/prose", json=draft)
    assert resp.status_code == 201

    resp = await client.get("http://test/api/v1/prose?group=hobbies")
    assert resp.status_code == 200
    assert [p["slug"] for p in resp.json()] == ["h-live"]


@pytest.mark.asyncio
async def test_group_filter_unknown_group_is_422(
    client: httpx.AsyncClient,
    clean_prose: None,
) -> None:
    resp = await client.get("http://test/api/v1/prose?group=nope")
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_group_filter_empty_group_returns_empty_list(
    client: httpx.AsyncClient,
    clean_prose: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await _login(client, monkeypatch)
    await _create_published(client, "w-only", "work_views")

    resp = await client.get("http://test/api/v1/prose?group=hobbies")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_no_group_param_returns_all_published(
    client: httpx.AsyncClient,
    clean_prose: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await _login(client, monkeypatch)
    await _create_published(client, "h-x", "hobbies")
    await _create_published(client, "w-x", "work_views")
    await _create_published(client, "i-x", "investor_intro")

    resp = await client.get("http://test/api/v1/prose")
    assert resp.status_code == 200
    assert {p["slug"] for p in resp.json()} == {"h-x", "w-x", "i-x"}
