"""Contact: public read + admin full-replace update with revalidation."""

from collections.abc import Sequence

import httpx
import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import email
from app.features.contact.endpoints import router as contact_router
from app.features.contact.models import ContactItem, ContactProfile
from app.tests.helpers import TEST_ADMIN_PASSWORD

DEFAULT_ITEMS = [
    {
        "kind": "email",
        "label": "s.chaudhari2k24@gmail.com",
        "url": "mailto:s.chaudhari2k24@gmail.com",
    },
    {
        "kind": "linkedin",
        "label": "linkedin.com/in/siddheshchaudhari",
        "url": "https://www.linkedin.com/in/siddheshchaudhari/",
    },
    {"kind": "cal", "label": "https://cal.com/siddhesh", "url": "https://cal.com/siddhesh"},
]

DEFAULT_CONSENT = (
    "I consent to having my data stored for the purpose of this contact submission."
)


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


async def _seed(session: AsyncSession) -> None:
    profile = ContactProfile(consent_text=DEFAULT_CONSENT)
    session.add(profile)
    for index, entry in enumerate(DEFAULT_ITEMS):
        session.add(ContactItem(**entry, sort_order=index))
    await session.commit()


async def _clear(session: AsyncSession) -> None:
    await session.execute(text("DELETE FROM contact_items"))
    await session.execute(text("DELETE FROM contact_profiles"))
    await session.commit()


@pytest.mark.asyncio
async def test_public_get_returns_profile_and_ordered_items(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    await _clear(session)
    await _seed(session)

    resp = await client.get("http://test/api/v1/contact")
    assert resp.status_code == 200
    body = resp.json()
    assert body["consent_text"] == DEFAULT_CONSENT
    assert [i["kind"] for i in body["items"]] == ["email", "linkedin", "cal"]
    assert [i["sort_order"] for i in body["items"]] == [0, 1, 2]
    assert body["items"][0]["url"] == "mailto:s.chaudhari2k24@gmail.com"


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
    await _seed(session)

    resp = await client.put("http://test/api/v1/admin/contact", json={"consent_text": "x"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_admin_update_replaces_items_in_order(
    client: httpx.AsyncClient,
    session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await _clear(session)
    await _seed(session)
    await _login(client, monkeypatch)

    revalidated: list[Sequence[str]] = []

    async def fake_revalidate(tags: Sequence[str]) -> None:
        revalidated.append(tags)

    monkeypatch.setattr(contact_router, "revalidate", fake_revalidate)

    resp = await client.put(
        "http://test/api/v1/admin/contact",
        json={
            "consent_text": "Updated consent",
            "items": [
                {
                    "kind": "instagram",
                    "label": "@siddhesh",
                    "url": "https://instagram.com/siddhesh",
                },
                {"kind": "generic", "label": "My site", "url": "https://example.com"},
            ],
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["consent_text"] == "Updated consent"
    assert [(i["kind"], i["sort_order"]) for i in body["items"]] == [
        ("instagram", 0),
        ("generic", 1),
    ]
    assert revalidated == [["contact"]]

    public = await client.get("http://test/api/v1/contact")
    assert public.json()["items"][0]["label"] == "@siddhesh"


@pytest.mark.asyncio
async def test_admin_update_rejects_unknown_kind(
    client: httpx.AsyncClient,
    session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await _clear(session)
    await _seed(session)
    await _login(client, monkeypatch)

    resp = await client.put(
        "http://test/api/v1/admin/contact",
        json={"items": [{"kind": "myspace", "label": "x", "url": "https://x.com"}]},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_admin_update_can_clear_items(
    client: httpx.AsyncClient,
    session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await _clear(session)
    await _seed(session)
    await _login(client, monkeypatch)

    resp = await client.put(
        "http://test/api/v1/admin/contact", json={"consent_text": "Only text", "items": []}
    )
    assert resp.status_code == 200
    assert resp.json()["items"] == []
    assert resp.json()["consent_text"] == "Only text"


@pytest.mark.asyncio
async def test_singleton_guard_constraint(session: AsyncSession) -> None:
    """Two profile rows must be impossible — the singleton_guard unique constraint."""
    await _clear(session)
    await _seed(session)
    with pytest.raises(IntegrityError):
        duplicate = ContactProfile(consent_text="dupe")
        session.add(duplicate)
        await session.commit()
    await session.rollback()
