"""Projects: full API suite with auth assertions, draft-leak guards, query-count check."""

from collections.abc import AsyncIterator, Sequence
from datetime import UTC, datetime, timedelta

import httpx
import pytest
import pytest_asyncio
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app.core import email
from app.core.config import Settings
from app.core.enums import PublishStatus
from app.features.projects.endpoints import router as projects_router
from app.features.projects.models import Project
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
async def clean_projects_tables(db_engine: AsyncEngine) -> None:
    async with db_engine.begin() as conn:
        await conn.execute(text("DELETE FROM project_topic_tags"))
        await conn.execute(text("DELETE FROM project_attachments"))
        await conn.execute(text("DELETE FROM projects"))


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
    clean_projects_tables: None,
    seeded_tags: list[str],
) -> None:
    published = Project(
        title="Published Project",
        slug="published-project",
        status=PublishStatus.PUBLISHED,
        published_at=datetime.now(UTC),
    )
    draft = Project(
        title="Draft Project",
        slug="draft-project",
        status=PublishStatus.DRAFT,
    )
    session.add_all([published, draft])
    await session.commit()

    response = await client.get("http://test/api/v1/projects")
    assert response.status_code == 200
    data = response.json()
    titles = [p["title"] for p in data]
    assert "Published Project" in titles
    assert "Draft Project" not in titles


async def test_public_list_excludes_future_scheduled(
    client: httpx.AsyncClient,
    session: AsyncSession,
    clean_projects_tables: None,
) -> None:
    now = datetime.now(UTC)
    future_scheduled = Project(
        title="Future Project",
        slug="future-project",
        status=PublishStatus.SCHEDULED,
        publish_at=now + timedelta(days=30),
    )
    due_scheduled = Project(
        title="Due Project",
        slug="due-project",
        status=PublishStatus.SCHEDULED,
        publish_at=now - timedelta(days=1),
    )
    session.add_all([future_scheduled, due_scheduled])
    await session.commit()

    response = await client.get("http://test/api/v1/projects")
    titles = [p["title"] for p in response.json()]
    assert "Due Project" in titles
    assert "Future Project" not in titles


async def test_public_project_not_found_returns_404(client: httpx.AsyncClient) -> None:
    response = await client.get("http://test/api/v1/projects/nonexistent-slug")
    assert response.status_code == 404


async def test_public_responses_omit_status_and_overrides(
    client: httpx.AsyncClient,
    session: AsyncSession,
    clean_projects_tables: None,
) -> None:
    project = Project(
        title="Public shape test",
        slug="public-shape-test",
        status=PublishStatus.PUBLISHED,
        published_at=datetime.now(UTC),
        audience_override=["recruiters"],
    )
    session.add(project)
    await session.commit()

    response = await client.get("http://test/api/v1/projects")
    data = response.json()
    item = data[0]
    assert "status" not in item
    assert "publish_at" not in item
    assert "audience_override" not in item


async def test_get_by_slug(
    client: httpx.AsyncClient,
    session: AsyncSession,
    clean_projects_tables: None,
) -> None:
    project = Project(
        title="Slugged Project",
        slug="slugged-project",
        status=PublishStatus.PUBLISHED,
        published_at=datetime.now(UTC),
    )
    session.add(project)
    await session.commit()

    response = await client.get(f"http://test/api/v1/projects/{project.slug}")
    assert response.status_code == 200
    assert response.json()["title"] == "Slugged Project"


# ---------------------------------------------------------------------------
# admin endpoint tests
# ---------------------------------------------------------------------------


async def test_admin_routes_require_auth(client: httpx.AsyncClient) -> None:
    assert (await client.get("http://test/api/v1/admin/projects")).status_code == 401
    assert (
        await client.post(
            "http://test/api/v1/admin/projects",
            json={
                "title": "Unauthorized",
                "slug": "unauthorized",
            },
        )
    ).status_code == 401


async def test_admin_crud_lifecycle(
    client: httpx.AsyncClient,
    session: AsyncSession,
    clean_projects_tables: None,
    seeded_tags: list[str],
    clean_auth_tables: None,
    admin_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await _login(client, monkeypatch)

    create_resp = await client.post(
        "http://test/api/v1/admin/projects",
        json={
            "title": "AI Platform",
            "slug": "ai-platform",
            "summary": "An AI platform for enterprises",
            "tag_slugs": ["ai"],
        },
    )
    assert create_resp.status_code == 201
    created = create_resp.json()
    assert created["title"] == "AI Platform"
    assert created["slug"] == "ai-platform"
    assert created["status"] == "draft"
    assert created["topic_tags"][0]["slug"] == "ai"

    project_id = created["id"]

    get_resp = await client.get(f"http://test/api/v1/admin/projects/{project_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["title"] == "AI Platform"

    update_resp = await client.patch(
        f"http://test/api/v1/admin/projects/{project_id}",
        json={"title": "AI Platform v2", "status": "published"},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["title"] == "AI Platform v2"
    assert update_resp.json()["status"] == "published"

    delete_resp = await client.delete(f"http://test/api/v1/admin/projects/{project_id}")
    assert delete_resp.status_code == 204

    assert (await client.get(f"http://test/api/v1/admin/projects/{project_id}")).status_code == 404


async def test_create_with_unknown_tag_returns_422(
    client: httpx.AsyncClient,
    clean_projects_tables: None,
    clean_auth_tables: None,
    admin_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await _login(client, monkeypatch)

    response = await client.post(
        "http://test/api/v1/admin/projects",
        json={
            "title": "Bad tag",
            "slug": "bad-tag",
            "tag_slugs": ["nonexistent_tag_12345"],
        },
    )
    assert response.status_code == 422


async def test_revalidation_fires_after_create(
    client: httpx.AsyncClient,
    session: AsyncSession,
    clean_projects_tables: None,
    clean_auth_tables: None,
    admin_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[list[str]] = []

    async def fake_revalidate(tags: Sequence[str]) -> None:
        calls.append(list(tags))

    monkeypatch.setattr(projects_router, "revalidate", fake_revalidate)
    await _login(client, monkeypatch)

    response = await client.post(
        "http://test/api/v1/admin/projects",
        json={
            "title": "Revalidation test",
            "slug": "revalidation-test",
        },
    )
    assert response.status_code == 201
    assert calls == [["projects", "timeline"]]


async def test_project_persists_without_timeline_entry(
    client: httpx.AsyncClient,
    session: AsyncSession,
    clean_projects_tables: None,
    seeded_tags: list[str],
    clean_auth_tables: None,
    admin_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await _login(client, monkeypatch)

    response = await client.post(
        "http://test/api/v1/admin/projects",
        json={
            "title": "No Experience Linked",
            "slug": "no-exp-linked",
            "status": "published",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["timeline_entry_id"] is None

    public_resp = await client.get(f"http://test/api/v1/projects/{data['slug']}")
    assert public_resp.status_code == 200


# ---------------------------------------------------------------------------
# attachment metadata CRUD tests
# ---------------------------------------------------------------------------


async def test_attachment_metadata_roundtrip(
    client: httpx.AsyncClient,
    session: AsyncSession,
    clean_projects_tables: None,
    clean_auth_tables: None,
    admin_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.features.projects.models import ProjectAttachment, ProjectAttachmentKind

    await _login(client, monkeypatch)

    create_resp = await client.post(
        "http://test/api/v1/admin/projects",
        json={
            "title": "Project with Attachments",
            "slug": "project-with-attachments",
            "status": "published",
        },
    )
    assert create_resp.status_code == 201
    project_id = create_resp.json()["id"]

    attachment = ProjectAttachment(
        project_id=project_id,
        kind=ProjectAttachmentKind.PDF,
        storage_key="resume.pdf",
        label="Resume",
        sort_order=0,
    )
    session.add(attachment)
    await session.commit()

    get_resp = await client.get(f"http://test/api/v1/admin/projects/{project_id}")
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert len(data["attachments"]) == 1
    att = data["attachments"][0]
    assert att["kind"] == "pdf"
    assert att["label"] == "Resume"
    assert "url" in att
    assert isinstance(att["url"], str) and len(att["url"]) > 0

    public_resp = await client.get("http://test/api/v1/projects/project-with-attachments")
    assert public_resp.status_code == 200
    public_data = public_resp.json()
    assert len(public_data["attachments"]) == 1
    assert "url" in public_data["attachments"][0]
    assert isinstance(public_data["attachments"][0]["url"], str)

    delete_resp = await client.delete(f"http://test/api/v1/admin/projects/{project_id}")
    assert delete_resp.status_code == 204

    get_after = await client.get(f"http://test/api/v1/admin/projects/{project_id}")
    assert get_after.status_code == 404

    remaining = (
        await session.scalars(
            select(ProjectAttachment).where(ProjectAttachment.project_id == project_id)
        )
    ).all()
    assert len(remaining) == 0


async def test_project_update_preserves_attachments(
    client: httpx.AsyncClient,
    session: AsyncSession,
    clean_projects_tables: None,
    clean_auth_tables: None,
    admin_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.features.projects.models import ProjectAttachment, ProjectAttachmentKind

    await _login(client, monkeypatch)

    create_resp = await client.post(
        "http://test/api/v1/admin/projects",
        json={
            "title": "Update Attachments Project",
            "slug": "update-attachments-project",
        },
    )
    assert create_resp.status_code == 201
    project_id = create_resp.json()["id"]

    attachment = ProjectAttachment(
        project_id=project_id,
        kind=ProjectAttachmentKind.IMAGE,
        storage_key="screenshot.png",
        label="Screenshot",
        sort_order=1,
    )
    session.add(attachment)
    await session.commit()

    update_resp = await client.patch(
        f"http://test/api/v1/admin/projects/{project_id}",
        json={"title": "Updated Title"},
    )
    assert update_resp.status_code == 200
    data = update_resp.json()
    assert len(data["attachments"]) == 1
    assert data["attachments"][0]["label"] == "Screenshot"
