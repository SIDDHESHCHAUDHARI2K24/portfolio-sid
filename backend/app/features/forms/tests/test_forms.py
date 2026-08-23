"""Form submission feature tests."""

from unittest.mock import AsyncMock

import httpx
import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app.core import email
from app.core.config import Settings
from app.features.forms.models import FormSubmission, FormType
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
async def clean_forms(db_engine: AsyncEngine) -> None:
    async with db_engine.begin() as conn:
        await conn.execute(text("DELETE FROM form_submissions"))


async def test_contact_submission_persists(
    client: httpx.AsyncClient,
    session: AsyncSession,
    clean_forms: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_verify(token: str, remoteip: str | None = None) -> bool:
        return True

    monkeypatch.setattr("app.features.forms.endpoints.router.verify_turnstile", fake_verify)
    monkeypatch.setattr(email, "send_email", AsyncMock())

    response = await client.post(
        "http://test/api/v1/forms/contact",
        json={
            "name": "Test User",
            "email": "test@example.com",
            "message": "Hello",
            "consent_given": True,
            "consent_text": "I agree.",
            "turnstile_token": "valid-token",
            "_hpt": "",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Thank you for your submission."

    result = await session.execute(text("SELECT * FROM form_submissions"))
    rows = result.all()
    assert len(rows) == 1
    row = rows[0]._mapping
    assert row["form_type"] == "CONTACT"
    assert row["consent_given"] is True
    assert row["consent_text"] == "I agree."
    assert row["submitter_email"] == "test@example.com"


async def test_dealflow_submission_requires_consent(
    client: httpx.AsyncClient,
    session: AsyncSession,
    clean_forms: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_verify(token: str, remoteip: str | None = None) -> bool:
        return True

    monkeypatch.setattr("app.features.forms.endpoints.router.verify_turnstile", fake_verify)
    monkeypatch.setattr(email, "send_email", AsyncMock())

    response = await client.post(
        "http://test/api/v1/forms/dealflow",
        json={
            "name": "Investor",
            "email": "vc@example.com",
            "firm": "VC Firm",
            "focus_area": "Pre-seed",
            "consent_given": True,
            "consent_text": "I consent.",
            "turnstile_token": "valid-token",
            "_hpt": "",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Thank you for your submission."


async def test_honeypot_returns_generic_success(
    client: httpx.AsyncClient,
    session: AsyncSession,
    clean_forms: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_verify(token: str, remoteip: str | None = None) -> bool:
        return True

    monkeypatch.setattr("app.features.forms.endpoints.router.verify_turnstile", fake_verify)

    response = await client.post(
        "http://test/api/v1/forms/contact",
        json={
            "name": "Bot",
            "email": "bot@example.com",
            "message": "spam",
            "consent_given": True,
            "consent_text": "X",
            "turnstile_token": "xxx",
            "_hpt": "gotcha",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Thank you for your submission."

    result = await session.execute(text("SELECT COUNT(*) FROM form_submissions"))
    count = result.scalar_one()
    assert count == 0


async def test_invalid_form_type_returns_404(client: httpx.AsyncClient) -> None:
    response = await client.post("http://test/api/v1/forms/invalid", json={})
    assert response.status_code == 404


async def test_email_failure_does_not_fail_request(
    client: httpx.AsyncClient,
    session: AsyncSession,
    clean_forms: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_verify(token: str, remoteip: str | None = None) -> bool:
        return True

    async def fake_send_email(*args: object, **kwargs: object) -> None:
        raise Exception("Email down")

    monkeypatch.setattr("app.features.forms.endpoints.router.verify_turnstile", fake_verify)
    monkeypatch.setattr(email, "send_email", fake_send_email)

    from app.core.config import get_settings

    settings = get_settings()
    monkeypatch.setattr(settings, "resend_api_key", "fake-key")

    response = await client.post(
        "http://test/api/v1/forms/contact",
        json={
            "name": "User",
            "email": "u@test.com",
            "message": "Hi",
            "consent_given": True,
            "consent_text": "ok",
            "turnstile_token": "valid-token",
            "_hpt": "",
        },
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Thank you for your submission."

    result = await session.execute(text("SELECT COUNT(*) FROM form_submissions"))
    count = result.scalar_one()
    assert count == 1


async def test_admin_can_list_and_filter(
    client: httpx.AsyncClient,
    session: AsyncSession,
    clean_forms: None,
    clean_auth_tables: None,
    admin_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sub1 = FormSubmission(
        form_type=FormType.CONTACT,
        payload={"name": "A"},
        consent_given=True,
        consent_text="Y",
        submitter_email="a@test.com",
    )
    sub2 = FormSubmission(
        form_type=FormType.DEALFLOW,
        payload={"name": "B"},
        consent_given=True,
        consent_text="Y",
        submitter_email="b@test.com",
        is_read=True,
    )
    session.add_all([sub1, sub2])
    await session.commit()

    await _login(client, monkeypatch)

    resp = await client.get("http://test/api/v1/admin/forms")
    assert resp.status_code == 200
    assert len(resp.json()) == 2

    resp = await client.get("http://test/api/v1/admin/forms?form_type=contact")
    assert len(resp.json()) == 1

    resp = await client.get("http://test/api/v1/admin/forms?is_read=true")
    assert len(resp.json()) == 1
    assert resp.json()[0]["form_type"] == "dealflow"


async def test_admin_can_mark_read(
    client: httpx.AsyncClient,
    session: AsyncSession,
    clean_forms: None,
    clean_auth_tables: None,
    admin_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sub = FormSubmission(
        form_type=FormType.CONTACT,
        payload={"name": "X"},
        consent_given=True,
        consent_text="ok",
        submitter_email="x@test.com",
    )
    session.add(sub)
    await session.commit()

    await _login(client, monkeypatch)

    resp = await client.patch(
        f"http://test/api/v1/admin/forms/{sub.id}",
        json={"is_read": True},
    )
    assert resp.status_code == 200
    assert resp.json()["is_read"] is True


async def test_csv_export(
    client: httpx.AsyncClient,
    session: AsyncSession,
    clean_forms: None,
    clean_auth_tables: None,
    admin_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sub = FormSubmission(
        form_type=FormType.CONTACT,
        payload={"name": "Export Test"},
        consent_given=True,
        consent_text="Export consent",
        submitter_email="export@test.com",
    )
    session.add(sub)
    await session.commit()

    await _login(client, monkeypatch)

    resp = await client.get("http://test/api/v1/admin/forms/export/csv")
    assert resp.status_code == 200
    content = resp.text
    assert "Export Test" in content
    assert "export@test.com" in content
    assert "Export consent" in content
