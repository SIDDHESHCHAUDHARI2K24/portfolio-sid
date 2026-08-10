"""Certifications: full API suite with auth, draft-leak guards, CRUD."""

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
from app.features.certifications.endpoints import router as certs_router
from app.features.certifications.models import Certification, CertKind
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
async def clean_certs_tables(db_engine: AsyncEngine) -> None:
    async with db_engine.begin() as conn:
        await conn.execute(text("DELETE FROM certification_topic_tags"))
        await conn.execute(text("DELETE FROM certifications"))


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


async def test_public_list_excludes_drafts(
    client: httpx.AsyncClient,
    session: AsyncSession,
    clean_certs_tables: None,
    seeded_tags: list[str],
) -> None:
    published = Certification(
        title="AWS Solutions Architect",
        issuer="AWS",
        kind=CertKind.TECHNICAL,
        issued_date=date(2023, 6, 1),
        status=PublishStatus.PUBLISHED,
        published_at=datetime.now(UTC),
    )
    draft = Certification(
        title="PMI-ACP",
        issuer="PMI",
        kind=CertKind.BUSINESS,
        issued_date=date(2022, 1, 1),
        status=PublishStatus.DRAFT,
    )
    session.add_all([published, draft])
    await session.commit()

    response = await client.get("http://test/api/v1/certifications")
    assert response.status_code == 200
    data = response.json()
    titles = [c["title"] for c in data]
    assert "AWS Solutions Architect" in titles
    assert "PMI-ACP" not in titles


async def test_public_list_excludes_future_scheduled(
    client: httpx.AsyncClient,
    session: AsyncSession,
    clean_certs_tables: None,
) -> None:
    now = datetime.now(UTC)
    future = Certification(
        title="Future cert",
        issuer="X",
        kind=CertKind.TECHNICAL,
        issued_date=date(2025, 1, 1),
        status=PublishStatus.SCHEDULED,
        publish_at=now + timedelta(days=30),
    )
    due = Certification(
        title="Past cert",
        issuer="Y",
        kind=CertKind.TECHNICAL,
        issued_date=date(2024, 1, 1),
        status=PublishStatus.SCHEDULED,
        publish_at=now - timedelta(days=1),
    )
    session.add_all([future, due])
    await session.commit()

    response = await client.get("http://test/api/v1/certifications")
    titles = [c["title"] for c in response.json()]
    assert "Past cert" in titles
    assert "Future cert" not in titles


async def test_both_kinds_persist(
    client: httpx.AsyncClient,
    session: AsyncSession,
    clean_certs_tables: None,
    clean_auth_tables: None,
    admin_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await _login(client, monkeypatch)

    for kind, title in [("technical", "AWS"), ("business", "CFA")]:
        resp = await client.post(
            "http://test/api/v1/admin/certifications",
            json={
                "title": title,
                "issuer": "ORG",
                "kind": kind,
                "issued_date": "2023-01-01",
                "status": "published",
            },
        )
        assert resp.status_code == 201


async def test_cert_with_neither_link_nor_file_renders(
    client: httpx.AsyncClient,
    session: AsyncSession,
    clean_certs_tables: None,
) -> None:
    cert = Certification(
        title="Minimal cert",
        issuer="X",
        kind=CertKind.TECHNICAL,
        issued_date=date(2023, 1, 1),
        status=PublishStatus.PUBLISHED,
        published_at=datetime.now(UTC),
    )
    session.add(cert)
    await session.commit()

    response = await client.get("http://test/api/v1/certifications")
    data = response.json()
    assert len(data) == 1
    assert data[0]["credential_url"] is None
    assert data[0]["file_key"] is None


async def test_admin_routes_require_auth(client: httpx.AsyncClient) -> None:
    assert (await client.get("http://test/api/v1/admin/certifications")).status_code == 401


async def test_admin_crud_lifecycle(
    client: httpx.AsyncClient,
    session: AsyncSession,
    clean_certs_tables: None,
    seeded_tags: list[str],
    clean_auth_tables: None,
    admin_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_revalidate(tags: Sequence[str]) -> None:
        pass

    monkeypatch.setattr(certs_router, "revalidate", fake_revalidate)
    await _login(client, monkeypatch)

    create_resp = await client.post(
        "http://test/api/v1/admin/certifications",
        json={
            "title": "AWS Solutions Architect",
            "issuer": "Amazon Web Services",
            "kind": "technical",
            "issued_date": "2023-06-15",
            "tag_slugs": ["engineering"],
            "file_type": "pdf",
            "file_key": "certs/aws-sa.pdf",
        },
    )
    assert create_resp.status_code == 201
    created = create_resp.json()
    assert created["title"] == "AWS Solutions Architect"
    assert created["kind"] == "technical"
    assert created["status"] == "draft"
    assert created["topic_tags"][0]["slug"] == "engineering"
    assert created["file_type"] == "pdf"

    cert_id = created["id"]

    get_resp = await client.get(f"http://test/api/v1/admin/certifications/{cert_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["title"] == "AWS Solutions Architect"

    update_resp = await client.patch(
        f"http://test/api/v1/admin/certifications/{cert_id}",
        json={"title": "AWS SA Pro", "status": "published"},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["title"] == "AWS SA Pro"
    assert update_resp.json()["status"] == "published"

    delete_resp = await client.delete(f"http://test/api/v1/admin/certifications/{cert_id}")
    assert delete_resp.status_code == 204

    assert (
        await client.get(f"http://test/api/v1/admin/certifications/{cert_id}")
    ).status_code == 404


async def test_revalidation_fires_after_create(
    client: httpx.AsyncClient,
    session: AsyncSession,
    clean_certs_tables: None,
    clean_auth_tables: None,
    admin_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[list[str]] = []

    async def fake_revalidate(tags: Sequence[str]) -> None:
        calls.append(list(tags))

    monkeypatch.setattr(certs_router, "revalidate", fake_revalidate)
    await _login(client, monkeypatch)

    response = await client.post(
        "http://test/api/v1/admin/certifications",
        json={
            "title": "Test",
            "issuer": "ORG",
            "kind": "technical",
            "issued_date": "2023-01-01",
        },
    )
    assert response.status_code == 201
    assert calls == [["certifications"]]
