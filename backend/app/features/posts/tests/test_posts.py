"""Posts: full API suite with auth, draft-leak guards, collection routing, CRUD."""

from collections.abc import AsyncIterator, Sequence
from datetime import UTC, datetime

import httpx
import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app.core import email
from app.core.config import Settings
from app.core.enums import PublishStatus
from app.features.posts.endpoints import router as posts_router
from app.features.posts.models import Post, PostCollection, PostPlatform
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
async def clean_posts_tables(db_engine: AsyncEngine) -> None:
    async with db_engine.begin() as conn:
        await conn.execute(text("DELETE FROM post_topic_tags"))
        await conn.execute(text("DELETE FROM posts"))


@pytest_asyncio.fixture
async def seeded_tags(db_engine: AsyncEngine) -> AsyncIterator[list[str]]:
    slugs = ["engineering", "ai"]
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
    clean_posts_tables: None,
) -> None:
    published = Post(
        title="Published post",
        url="https://example.com/1",
        platform=PostPlatform.OTHER,
        status=PublishStatus.PUBLISHED,
        published_at=datetime.now(UTC),
    )
    draft = Post(
        title="Draft post",
        url="https://example.com/2",
        platform=PostPlatform.OTHER,
        status=PublishStatus.DRAFT,
    )
    session.add_all([published, draft])
    await session.commit()

    response = await client.get("http://test/api/v1/posts")
    assert response.status_code == 200
    data = response.json()
    titles = [p["title"] for p in data]
    assert "Published post" in titles
    assert "Draft post" not in titles


async def test_collection_routing(
    client: httpx.AsyncClient,
    session: AsyncSession,
    clean_posts_tables: None,
) -> None:
    tech = Post(
        title="Tech post",
        url="https://example.com/tech",
        platform=PostPlatform.MEDIUM,
        collections=[PostCollection.TECH_RABBITHOLE],
        status=PublishStatus.PUBLISHED,
        published_at=datetime.now(UTC),
    )
    ai = Post(
        title="AI post",
        url="https://example.com/ai",
        platform=PostPlatform.SUBSTACK,
        collections=[PostCollection.HOW_I_USE_AI],
        status=PublishStatus.PUBLISHED,
        published_at=datetime.now(UTC),
    )
    session.add_all([tech, ai])
    await session.commit()

    tech_resp = await client.get("http://test/api/v1/posts?collection=tech_rabbithole")
    assert tech_resp.status_code == 200
    tech_titles = [p["title"] for p in tech_resp.json()]
    assert "Tech post" in tech_titles
    assert "AI post" not in tech_titles

    ai_resp = await client.get("http://test/api/v1/posts?collection=how_i_use_ai")
    assert ai_resp.status_code == 200
    ai_titles = [p["title"] for p in ai_resp.json()]
    assert "AI post" in ai_titles
    assert "Tech post" not in ai_titles


async def test_post_in_two_collections_appears_on_both(
    client: httpx.AsyncClient,
    session: AsyncSession,
    clean_posts_tables: None,
) -> None:
    cross = Post(
        title="Cross post",
        url="https://example.com/cross",
        platform=PostPlatform.OTHER,
        collections=[PostCollection.TECH_RABBITHOLE, PostCollection.VC_FOR_FOUNDERS],
        status=PublishStatus.PUBLISHED,
        published_at=datetime.now(UTC),
    )
    session.add(cross)
    await session.commit()

    tech_resp = await client.get("http://test/api/v1/posts?collection=tech_rabbithole")
    vc_resp = await client.get("http://test/api/v1/posts?collection=vc_for_founders")
    ai_resp = await client.get("http://test/api/v1/posts?collection=how_i_use_ai")

    assert len(tech_resp.json()) == 1
    assert tech_resp.json()[0]["title"] == "Cross post"
    assert len(vc_resp.json()) == 1
    assert vc_resp.json()[0]["title"] == "Cross post"
    assert len(ai_resp.json()) == 0


async def test_collection_does_not_affect_relevance(
    client: httpx.AsyncClient,
    session: AsyncSession,
    clean_posts_tables: None,
    seeded_tags: list[str],
) -> None:
    post = Post(
        title="Tagged post",
        url="https://example.com/tagged",
        platform=PostPlatform.OTHER,
        collections=[PostCollection.HOW_I_USE_AI],
        status=PublishStatus.PUBLISHED,
        published_at=datetime.now(UTC),
    )
    session.add(post)
    await session.flush()

    slug = seeded_tags[0]
    tag_result = await session.execute(
        text("SELECT id FROM topic_tags WHERE slug = :slug"), {"slug": slug}
    )
    tag_id = tag_result.scalar_one()
    await session.execute(
        text("INSERT INTO post_topic_tags (post_id, topic_tag_id) VALUES (:post_id, :tag_id)"),
        {"post_id": post.id, "tag_id": tag_id},
    )
    await session.commit()

    response = await client.get("http://test/api/v1/posts?collection=how_i_use_ai")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert len(data[0]["topic_tags"]) == 1
    assert data[0]["topic_tags"][0]["slug"] == slug
    assert data[0]["collections"] == ["how_i_use_ai"]


async def test_admin_routes_require_auth(client: httpx.AsyncClient) -> None:
    assert (await client.get("http://test/api/v1/admin/posts")).status_code == 401


async def test_admin_crud_lifecycle(
    client: httpx.AsyncClient,
    session: AsyncSession,
    clean_posts_tables: None,
    seeded_tags: list[str],
    clean_auth_tables: None,
    admin_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_revalidate(tags: Sequence[str]) -> None:
        pass

    monkeypatch.setattr(posts_router, "revalidate", fake_revalidate)
    await _login(client, monkeypatch)

    create_resp = await client.post(
        "http://test/api/v1/admin/posts",
        json={
            "title": "My Substack Post",
            "url": "https://substack.com/my-post",
            "platform": "substack",
            "published_date": "2024-06-15",
            "collections": ["tech_rabbithole"],
            "tag_slugs": ["engineering"],
            "status": "draft",
        },
    )
    assert create_resp.status_code == 201
    created = create_resp.json()
    assert created["title"] == "My Substack Post"
    assert created["platform"] == "substack"
    assert created["status"] == "draft"
    assert created["topic_tags"][0]["slug"] == "engineering"
    assert created["collections"] == ["tech_rabbithole"]

    post_id = created["id"]

    get_resp = await client.get(f"http://test/api/v1/admin/posts/{post_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["title"] == "My Substack Post"

    update_resp = await client.patch(
        f"http://test/api/v1/admin/posts/{post_id}",
        json={
            "title": "Updated Post",
            "status": "published",
            "collections": ["tech_rabbithole", "how_i_use_ai"],
        },
    )
    assert update_resp.status_code == 200
    updated = update_resp.json()
    assert updated["title"] == "Updated Post"
    assert updated["status"] == "published"
    assert set(updated["collections"]) == {"tech_rabbithole", "how_i_use_ai"}

    delete_resp = await client.delete(f"http://test/api/v1/admin/posts/{post_id}")
    assert delete_resp.status_code == 204

    assert (await client.get(f"http://test/api/v1/admin/posts/{post_id}")).status_code == 404


async def test_revalidation_fires_after_create(
    client: httpx.AsyncClient,
    session: AsyncSession,
    clean_posts_tables: None,
    clean_auth_tables: None,
    admin_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[list[str]] = []

    async def fake_revalidate(tags: Sequence[str]) -> None:
        calls.append(list(tags))

    monkeypatch.setattr(posts_router, "revalidate", fake_revalidate)
    await _login(client, monkeypatch)

    response = await client.post(
        "http://test/api/v1/admin/posts",
        json={
            "title": "Test",
            "url": "https://example.com/test",
            "platform": "other",
            "collections": ["tech_rabbithole"],
        },
    )
    assert response.status_code == 201
    assert calls == [["posts"]]
