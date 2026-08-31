"""Resume feature tests."""

import httpx
import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app.core import email
from app.core.config import Settings
from app.features.resumes.models import ALLOWED_VARIANTS, Resume
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
    business = Resume(
        variant="business",
        label="Business CV",
        file_key="resumes/biz-abc.pdf",
        is_active=True,
    )
    generic = Resume(
        variant="generic",
        label="Generic CV",
        file_key="resumes/generic-def.pdf",
        is_active=True,
    )
    inactive = Resume(
        variant="business",
        label="Old Business",
        file_key="resumes/old-xyz.pdf",
        is_active=False,
    )
    session.add_all([business, generic, inactive])
    await session.commit()

    response = await client.get("http://test/api/v1/resumes")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    variants = [r["variant"] for r in data]
    assert "business" in variants
    assert "generic" in variants


async def test_both_variants_persist(
    client: httpx.AsyncClient,
    session: AsyncSession,
    clean_resumes: None,
) -> None:
    business = Resume(
        variant="business",
        label="Biz Resume",
        file_key="resumes/b.pdf",
        is_active=True,
    )
    generic = Resume(
        variant="generic",
        label="Generic Resume",
        file_key="resumes/t.pdf",
        is_active=True,
    )
    session.add_all([business, generic])
    await session.commit()

    response = await client.get("http://test/api/v1/resumes")
    data = response.json()
    variants = {r["variant"] for r in data}
    assert variants == {"business", "generic"}


async def test_all_six_variants_persist(
    client: httpx.AsyncClient,
    session: AsyncSession,
    clean_resumes: None,
) -> None:
    for variant in sorted(ALLOWED_VARIANTS):
        session.add(
            Resume(
                variant=variant,
                label=f"{variant} CV",
                file_key=f"resumes/{variant}.pdf",
                is_active=True,
            )
        )
    await session.commit()

    response = await client.get("http://test/api/v1/resumes")
    assert response.status_code == 200
    data = response.json()
    variants = {r["variant"] for r in data}
    assert variants == ALLOWED_VARIANTS


async def test_variant_validation_rejects_invalid_and_case_sensitive(
    client: httpx.AsyncClient,
    session: AsyncSession,
    clean_resumes: None,
    clean_auth_tables: None,
    admin_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await _login(client, monkeypatch)
    # invalid variant
    resp = await client.post(
        "http://test/api/v1/admin/resumes",
        json={"variant": "invalid_variant", "label": "X", "file_key": "r/x.pdf"},
    )
    assert resp.status_code == 422
    # case-sensitive: Business vs business
    resp2 = await client.post(
        "http://test/api/v1/admin/resumes",
        json={"variant": "Business", "label": "X", "file_key": "r/x.pdf"},
    )
    assert resp2.status_code == 422
    # legacy tech should also be rejected now
    resp3 = await client.post(
        "http://test/api/v1/admin/resumes",
        json={"variant": "tech", "label": "X", "file_key": "r/x.pdf"},
    )
    assert resp3.status_code == 422


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
            "variant": "business",
            "label": "Business CV",
            "file_key": "resumes/business-abc.pdf",
        },
    )
    assert create_resp.status_code == 201
    created = create_resp.json()
    assert created["variant"] == "business"
    assert created["label"] == "Business CV"
    assert created["is_active"] is True

    resume_id = created["id"]

    get_resp = await client.get(f"http://test/api/v1/admin/resumes/{resume_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["label"] == "Business CV"

    update_resp = await client.patch(
        f"http://test/api/v1/admin/resumes/{resume_id}",
        json={"label": "Updated Business CV", "is_active": False},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["label"] == "Updated Business CV"
    assert update_resp.json()["is_active"] is False

    # variant update across allowlist works
    variant_update = await client.patch(
        f"http://test/api/v1/admin/resumes/{resume_id}",
        json={"variant": "ai_consultant"},
    )
    assert variant_update.status_code == 200
    assert variant_update.json()["variant"] == "ai_consultant"

    delete_resp = await client.delete(f"http://test/api/v1/admin/resumes/{resume_id}")
    assert delete_resp.status_code == 204

    assert (await client.get(f"http://test/api/v1/admin/resumes/{resume_id}")).status_code == 404


async def test_admin_requires_auth(client: httpx.AsyncClient) -> None:
    assert (await client.get("http://test/api/v1/admin/resumes")).status_code == 401
    assert (
        await client.post(
            "http://test/api/v1/admin/resumes",
            json={"variant": "business", "label": "X", "file_key": "r/x.pdf"},
        )
    ).status_code == 401
