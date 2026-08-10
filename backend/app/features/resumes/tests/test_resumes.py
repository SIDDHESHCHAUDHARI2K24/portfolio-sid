"""Resume feature tests."""

import httpx
import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app.core import email
from app.core.config import Settings
from app.features.resumes.models import Resume, ResumeVariant
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
async def clean_resumes(db_engine: AsyncEngine) -> None:
    async with db_engine.begin() as conn:
        await conn.execute(text("DELETE FROM resumes"))


async def test_public_list_returns_active_resumes(
    client: httpx.AsyncClient,
    session: AsyncSession,
    clean_resumes: None,
) -> None:
    tech = Resume(
        variant=ResumeVariant.TECH,
        label="Tech CV",
        file_key="resumes/tech-abc.pdf",
        is_active=True,
    )
    biz = Resume(
        variant=ResumeVariant.BUSINESS,
        label="Business CV",
        file_key="resumes/biz-def.pdf",
        is_active=True,
    )
    inactive = Resume(
        variant=ResumeVariant.TECH,
        label="Old Tech",
        file_key="resumes/old-xyz.pdf",
        is_active=False,
    )
    session.add_all([tech, biz, inactive])
    await session.commit()

    response = await client.get("http://test/api/v1/resumes")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    variants = [r["variant"] for r in data]
    assert "tech" in variants
    assert "business" in variants


async def test_both_variants_persist(
    client: httpx.AsyncClient,
    session: AsyncSession,
    clean_resumes: None,
) -> None:
    tech = Resume(
        variant=ResumeVariant.TECH,
        label="Tech Resume",
        file_key="resumes/t.pdf",
        is_active=True,
    )
    biz = Resume(
        variant=ResumeVariant.BUSINESS,
        label="Biz Resume",
        file_key="resumes/b.pdf",
        is_active=True,
    )
    session.add_all([tech, biz])
    await session.commit()

    response = await client.get("http://test/api/v1/resumes")
    data = response.json()
    variants = {r["variant"] for r in data}
    assert variants == {"tech", "business"}


async def test_admin_crud(
    client: httpx.AsyncClient,
    session: AsyncSession,
    clean_resumes: None,
    clean_auth_tables: None,
    admin_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await _login(client, monkeypatch)

    create_resp = await client.post(
        "http://test/api/v1/admin/resumes",
        json={
            "variant": "tech",
            "label": "Tech CV",
            "file_key": "resumes/tech-abc.pdf",
        },
    )
    assert create_resp.status_code == 201
    created = create_resp.json()
    assert created["variant"] == "tech"
    assert created["label"] == "Tech CV"
    assert created["is_active"] is True

    resume_id = created["id"]

    get_resp = await client.get(f"http://test/api/v1/admin/resumes/{resume_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["label"] == "Tech CV"

    update_resp = await client.patch(
        f"http://test/api/v1/admin/resumes/{resume_id}",
        json={"label": "Updated Tech CV", "is_active": False},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["label"] == "Updated Tech CV"
    assert update_resp.json()["is_active"] is False

    delete_resp = await client.delete(f"http://test/api/v1/admin/resumes/{resume_id}")
    assert delete_resp.status_code == 204

    assert (await client.get(f"http://test/api/v1/admin/resumes/{resume_id}")).status_code == 404


async def test_admin_requires_auth(client: httpx.AsyncClient) -> None:
    assert (await client.get("http://test/api/v1/admin/resumes")).status_code == 401
    assert (
        await client.post(
            "http://test/api/v1/admin/resumes",
            json={"variant": "tech", "label": "X", "file_key": "r/x.pdf"},
        )
    ).status_code == 401
