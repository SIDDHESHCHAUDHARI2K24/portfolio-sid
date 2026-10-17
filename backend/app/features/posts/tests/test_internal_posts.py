"""Internal (native) posts: DB rules, schema validation, API, slug endpoint."""

from collections.abc import Sequence
from datetime import UTC, datetime, timedelta

import httpx
import pytest
import pytest_asyncio
from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app.core import email
from app.core.config import Settings
from app.core.enums import PublishStatus
from app.features.posts.endpoints import router as posts_router
from app.features.posts.models import Post, PostPlatform
from app.features.posts.schemas import PostCreate, PostUpdate
from app.tests.helpers import TEST_ADMIN_PASSWORD

MAX_BODY = 100 * 1024


@pytest_asyncio.fixture(loop_scope="session")
async def clean_posts_tables(db_engine: AsyncEngine) -> None:
    async with db_engine.begin() as conn:
        await conn.execute(text("DELETE FROM post_topic_tags"))
        await conn.execute(text("DELETE FROM posts"))


# --- Task 1: DB-level rules -------------------------------------------------


async def test_check_rejects_internal_without_slug_or_body(
    session: AsyncSession, clean_posts_tables: None
) -> None:
    session.add(Post(title="x", platform=PostPlatform.INTERNAL, slug="a"))
    with pytest.raises(IntegrityError):
        await session.commit()
    await session.rollback()
    session.add(Post(title="x", platform=PostPlatform.INTERNAL, body="b"))
    with pytest.raises(IntegrityError):
        await session.commit()


async def test_check_rejects_external_without_url(
    session: AsyncSession, clean_posts_tables: None
) -> None:
    session.add(Post(title="x", platform=PostPlatform.MEDIUM))
    with pytest.raises(IntegrityError):
        await session.commit()


async def test_check_allows_internal_without_url(
    session: AsyncSession, clean_posts_tables: None
) -> None:
    session.add(Post(title="x", platform=PostPlatform.INTERNAL, slug="ok", body="# hi"))
    await session.commit()


async def test_slug_unique_in_db(session: AsyncSession, clean_posts_tables: None) -> None:
    session.add(Post(title="a", platform=PostPlatform.INTERNAL, slug="dup", body="b"))
    await session.commit()
    session.add(Post(title="b", platform=PostPlatform.INTERNAL, slug="dup", body="b"))
    with pytest.raises(IntegrityError):
        await session.commit()


# --- Task 2: schema validation ---------------------------------------------


def _create(**kw: object) -> PostCreate:
    base: dict[str, object] = {"title": "t", "platform": "internal"}
    base.update(kw)
    return PostCreate(**base)


def test_slug_normalized_lowercase() -> None:
    assert _create(slug="  My-Post ", body="b").slug == "my-post"
    assert PostUpdate(slug="ABC").slug == "abc"


@pytest.mark.parametrize("bad", ["Hello World!", "-a", "a-", "a_b", "a--b", "x" * 201, "é"])
def test_slug_rejects_invalid(bad: str) -> None:
    with pytest.raises(ValidationError):
        _create(slug=bad, body="b")


def test_body_100kb_ok_plus_one_rejected() -> None:
    assert _create(slug="a", body="x" * MAX_BODY).body is not None
    with pytest.raises(ValidationError):
        _create(slug="a", body="x" * (MAX_BODY + 1))


def test_body_multibyte_counts_bytes() -> None:
    # 2-byte char: 51201 chars = 102402 bytes > limit although chars < limit
    with pytest.raises(ValidationError):
        _create(slug="a", body="é" * (MAX_BODY // 2 + 1))


# --- Task 3/4: API ---------------------------------------------------------


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


@pytest_asyncio.fixture
async def admin(
    client: httpx.AsyncClient,
    clean_posts_tables: None,
    clean_auth_tables: None,
    admin_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> httpx.AsyncClient:
    async def fake_revalidate(tags: Sequence[str]) -> None:
        pass

    monkeypatch.setattr(posts_router, "revalidate", fake_revalidate)
    await _login(client, monkeypatch)
    return client


A = "http://test/api/v1/admin/posts"
P = "http://test/api/v1/posts"


def _internal(**kw: object) -> dict[str, object]:
    d: dict[str, object] = {
        "title": "Hello",
        "platform": "internal",
        "slug": "hello",
        "body": "# Hello\n\nworld",
    }
    d.update(kw)
    return d


def _fields(resp: httpx.Response) -> set[str]:
    return {e["loc"][-1] for e in resp.json()["detail"]}


async def test_create_internal_requires_slug_and_body(admin: httpx.AsyncClient) -> None:
    r = await admin.post(A, json={"title": "t", "platform": "internal"})
    assert r.status_code == 422
    assert {"slug", "body"} <= _fields(r)
    r = await admin.post(A, json=_internal(body="   "))
    assert r.status_code == 422 and "body" in _fields(r)


async def test_create_external_requires_url(admin: httpx.AsyncClient) -> None:
    r = await admin.post(A, json={"title": "t", "platform": "medium"})
    assert r.status_code == 422 and "url" in _fields(r)
    r = await admin.post(A, json={"title": "t", "platform": "medium", "url": "  "})
    assert r.status_code == 422 and "url" in _fields(r)


async def test_create_internal_ok_without_url(admin: httpx.AsyncClient) -> None:
    r = await admin.post(A, json=_internal())
    assert r.status_code == 201
    j = r.json()
    assert j["url"] is None and j["slug"] == "hello" and j["body"].startswith("# Hello")


async def test_create_normalizes_slug(admin: httpx.AsyncClient) -> None:
    r = await admin.post(A, json=_internal(slug="My-Post"))
    assert r.status_code == 201 and r.json()["slug"] == "my-post"


async def test_invalid_slug_422(admin: httpx.AsyncClient) -> None:
    r = await admin.post(A, json=_internal(slug="Hello World!"))
    assert r.status_code == 422 and "slug" in _fields(r)


async def test_slug_collision_422(admin: httpx.AsyncClient) -> None:
    assert (await admin.post(A, json=_internal())).status_code == 201
    r = await admin.post(A, json=_internal(title="Other"))
    assert r.status_code == 422
    assert "slug already exists" in str(r.json()["detail"])
    assert "slug" in _fields(r)


async def test_slug_collision_case_insensitive(admin: httpx.AsyncClient) -> None:
    assert (await admin.post(A, json=_internal())).status_code == 201
    r = await admin.post(A, json=_internal(slug="HELLO"))
    assert r.status_code == 422 and "slug already exists" in str(r.json()["detail"])


async def test_oversize_body_422(admin: httpx.AsyncClient) -> None:
    r = await admin.post(A, json=_internal(body="x" * (MAX_BODY + 1)))
    assert r.status_code == 422 and "body" in _fields(r)
    r = await admin.post(A, json=_internal(body="x" * MAX_BODY))
    assert r.status_code == 201


async def test_patch_to_internal_without_slug_body_422(admin: httpx.AsyncClient) -> None:
    created = await admin.post(
        A, json={"title": "t", "platform": "medium", "url": "https://x.com/a"}
    )
    pid = created.json()["id"]
    r = await admin.patch(f"{A}/{pid}", json={"platform": "internal"})
    assert r.status_code == 422 and {"slug", "body"} <= _fields(r)
    r = await admin.patch(f"{A}/{pid}", json={"platform": "internal", "slug": "s", "body": "b"})
    assert r.status_code == 200 and r.json()["platform"] == "internal"


async def test_patch_internal_to_external_requires_url(admin: httpx.AsyncClient) -> None:
    pid = (await admin.post(A, json=_internal())).json()["id"]
    r = await admin.patch(f"{A}/{pid}", json={"platform": "medium"})
    assert r.status_code == 422 and "url" in _fields(r)
    r = await admin.patch(f"{A}/{pid}", json={"platform": "medium", "url": "https://m.com/x"})
    assert r.status_code == 200
    assert r.json()["body"] is not None  # body stays stored


async def test_patch_own_slug_is_not_a_collision(admin: httpx.AsyncClient) -> None:
    pid = (await admin.post(A, json=_internal())).json()["id"]
    r = await admin.patch(f"{A}/{pid}", json={"slug": "hello", "title": "New"})
    assert r.status_code == 200


async def test_patch_slug_collision_with_other_post(admin: httpx.AsyncClient) -> None:
    await admin.post(A, json=_internal())
    pid = (await admin.post(A, json=_internal(slug="second"))).json()["id"]
    r = await admin.patch(f"{A}/{pid}", json={"slug": "hello"})
    assert r.status_code == 422 and "slug already exists" in str(r.json()["detail"])


async def test_external_posts_unchanged(admin: httpx.AsyncClient) -> None:
    r = await admin.post(A, json={"title": "t", "platform": "substack", "url": "https://s.com/p"})
    assert r.status_code == 201
    j = r.json()
    assert j["url"] == "https://s.com/p" and j["slug"] is None and j["body"] is None


# --- Task 4: public endpoints ----------------------------------------------


async def _publish(admin: httpx.AsyncClient, **kw: object) -> dict[str, object]:
    r = await admin.post(A, json=_internal(status="published", **kw))
    assert r.status_code == 201, r.text
    out: dict[str, object] = r.json()
    return out


async def test_slug_endpoint_returns_body_for_published_internal(
    admin: httpx.AsyncClient,
) -> None:
    await _publish(admin)
    r = await admin.get(f"{P}/slug/hello")
    assert r.status_code == 200
    j = r.json()
    assert j["body"].startswith("# Hello") and j["slug"] == "hello" and j["url"] is None


async def test_slug_endpoint_404_draft(admin: httpx.AsyncClient) -> None:
    await admin.post(A, json=_internal())
    assert (await admin.get(f"{P}/slug/hello")).status_code == 404


async def test_slug_endpoint_scheduled_future_404_past_ok(admin: httpx.AsyncClient) -> None:
    future = (datetime.now(UTC) + timedelta(days=1)).isoformat()
    await admin.post(A, json=_internal(status="scheduled", publish_at=future))
    assert (await admin.get(f"{P}/slug/hello")).status_code == 404
    past = (datetime.now(UTC) - timedelta(days=1)).isoformat()
    await admin.post(A, json=_internal(slug="past", status="scheduled", publish_at=past))
    assert (await admin.get(f"{P}/slug/past")).status_code == 200


async def test_slug_endpoint_404_external_even_with_slug(
    admin: httpx.AsyncClient, session: AsyncSession
) -> None:
    session.add(
        Post(
            title="ext",
            platform=PostPlatform.MEDIUM,
            url="https://m.com/x",
            slug="ext",
            body="secret",
            status=PublishStatus.PUBLISHED,
            published_at=datetime.now(UTC),
        )
    )
    await session.commit()
    assert (await admin.get(f"{P}/slug/ext")).status_code == 404


async def test_slug_endpoint_404_missing_and_case_insensitive(
    admin: httpx.AsyncClient,
) -> None:
    assert (await admin.get(f"{P}/slug/nope")).status_code == 404
    await _publish(admin)
    assert (await admin.get(f"{P}/slug/HELLO")).status_code == 200


async def test_public_list_has_slug_and_no_body(admin: httpx.AsyncClient) -> None:
    await _publish(admin, collections=["how_i_use_ai"])
    r = await admin.get(P)
    assert r.status_code == 200
    item = r.json()[0]
    assert item["slug"] == "hello" and item["platform"] == "internal"
    assert "body" not in item
    r = await admin.get(f"{P}?collection=how_i_use_ai")
    assert "body" not in r.json()[0]
    pid = item["id"]
    assert "body" not in (await admin.get(f"{P}/{pid}")).json()


async def test_internal_post_in_multiple_collections_on_each_page(
    admin: httpx.AsyncClient,
) -> None:
    await _publish(admin, collections=["tech_rabbithole", "vc_for_founders"])
    for col, n in (("tech_rabbithole", 1), ("vc_for_founders", 1), ("how_i_use_ai", 0)):
        assert len((await admin.get(f"{P}?collection={col}")).json()) == n


async def test_internal_post_tags_and_audience_override(
    admin: httpx.AsyncClient, db_engine: AsyncEngine
) -> None:
    async with db_engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO topic_tags (id, slug, label) VALUES "
                "(gen_random_uuid(), 'w2-tag', 'W2') ON CONFLICT (slug) DO NOTHING"
            )
        )
    try:
        await _publish(admin, tag_slugs=["w2-tag"], audience_override=["founders"])
        item = (await admin.get(P)).json()[0]
        assert [t["slug"] for t in item["topic_tags"]] == ["w2-tag"]
        assert item["audience_override"] == ["founders"]
    finally:
        async with db_engine.begin() as conn:
            await conn.execute(text("DELETE FROM post_topic_tags"))
            await conn.execute(text("DELETE FROM topic_tags WHERE slug = 'w2-tag'"))


async def test_admin_response_includes_body(admin: httpx.AsyncClient) -> None:
    pid = (await admin.post(A, json=_internal())).json()["id"]
    assert (await admin.get(f"{A}/{pid}")).json()["body"].startswith("# Hello")
    assert (await admin.get(A)).json()[0]["body"].startswith("# Hello")


async def test_revalidate_fires_for_internal_create(
    admin: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[list[str]] = []

    async def rec(tags: Sequence[str]) -> None:
        calls.append(list(tags))

    monkeypatch.setattr(posts_router, "revalidate", rec)
    assert (await admin.post(A, json=_internal())).status_code == 201
    assert calls == [["posts"]]
