"""ContactProfile: public read + admin update with revalidation."""

from typing import Sequence

import httpx
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import email
from app.features.contact.endpoints import router as contact_router
from app.features.contact.models import ContactProfile
from app.tests.helpers import TEST_ADMIN_PASSWORD

DEFAULT_PROFILE = {
    "email": "siddhesh@example.com",
    "linkedin_url": "https://www.linkedin.com/in/siddheshchaudhari/",
    "linkedin_label": "linkedin.com/in/siddheshchaudhari",
    "cal_url": "https://cal.com/siddhesh",
    "cal_label": "https://cal.com/siddhesh",
    "github_url": "https://github.com/siddhesh",
    "consent_text": "I consent to having my data stored for the purpose of this contact submission.",
}


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


async def _seed_profile(session: AsyncSession) -> ContactProfile:
    profile = ContactProfile(**DEFAULT_PROFILE)
    session.add(profile)
    await session.commit()
    await session.refresh(profile)
    return profile


async def _clear(session: AsyncSession) -> None:
    await session.execute(text("DELETE FROM contact_profiles"))
    await session.commit()


@pytest.mark.asyncio
async def test_public_get_returns_profile(client: httpx.AsyncClient, session: AsyncSession) -> None:
    await _clear(session)
    await _seed_profile(session)

    resp = await client.get("http://test/api/v1/contact")
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == DEFAULT_PROFILE["email"]
    assert body["linkedin_url"] == DEFAULT_PROFILE["linkedin_url"]
    assert body["consent_text"] == DEFAULT_PROFILE["consent_text"]


@pytest.mark.asyncio
async def test_public_get_404_when_missing(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    await _clear(session)
    resp = await client.get("http://test/api/v1/contact")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_admin_update_requires_auth(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    await _clear(session)
    await _seed_profile(session)

    resp = await client.put("http://test/api/v1/admin/contact", json={"email": "x@y.com"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_admin_update_persists_and_revalidates(
    client: httpx.AsyncClient,
    session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await _clear(session)
    await _seed_profile(session)
    await _login(client, monkeypatch)

    revalidated: list[Sequence[str]] = []

    async def fake_revalidate(tags: Sequence[str]) -> None:
        revalidated.append(tags)

    monkeypatch.setattr(contact_router, "revalidate", fake_revalidate)

    resp = await client.put(
        "http://test/api/v1/admin/contact",
        json={"email": "new@example.com", "cal_label": "Book time with me"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == "new@example.com"
    assert body["cal_label"] == "Book time with me"
    # untouched fields preserved
    assert body["linkedin_url"] == DEFAULT_PROFILE["linkedin_url"]
    assert revalidated == [["contact"]]

    public = await client.get("http://test/api/v1/contact")
    assert public.json()["email"] == "new@example.com"


@pytest.mark.asyncio
async def test_admin_update_404_when_missing(
    client: httpx.AsyncClient,
    session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await _clear(session)
    await _login(client, monkeypatch)

    resp = await client.put("http://test/api/v1/admin/contact", json={"email": "x@y.com"})
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_singleton_guard_constraint(session: AsyncSession) -> None:
    """Two rows must be impossible — the singleton_guard unique constraint."""
    await _clear(session)
    await _seed_profile(session)
    with pytest.raises(Exception):
        duplicate = ContactProfile(**DEFAULT_PROFILE)
        session.add(duplicate)
        await session.commit()
    await session.rollback()
