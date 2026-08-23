"""Overview feature: CRUD + auth tests."""

from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import email
from app.core.enums import PublishStatus
from app.core.queries import public_filter
from app.features.overview.models import VALID_AUDIENCES, OverviewIntro
from app.tests.helpers import TEST_ADMIN_PASSWORD

SEED_AUDIENCES = VALID_AUDIENCES


async def _seed_overview(session: AsyncSession) -> None:
    """Insert one published row per audience if none exist."""
    existing = {r for r in (await session.execute(select(OverviewIntro.audience))).scalars().all()}
    missing = [a for a in SEED_AUDIENCES if a not in existing]
    if not missing:
        return
    now = datetime.now(UTC)
    for aud in missing:
        session.add(
            OverviewIntro(
                audience=aud,
                headline=f"Siddhesh Chaudhari — {aud.title()}",
                body=f"Welcome! This is the **{aud}** view.",
                status=PublishStatus.PUBLISHED,
                published_at=now,
            )
        )
    await session.commit()


async def _auth(client: AsyncClient, monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    sent: list[tuple[str, str]] = []

    async def fake_send_otp(code: str, to: str) -> None:
        sent.append((code, to))

    monkeypatch.setattr(email, "send_otp", fake_send_otp)
    res = await client.post(
        "http://test/api/v1/auth/login",
        json={"email": "admin@example.com", "password": TEST_ADMIN_PASSWORD},
    )
    assert res.status_code == 200, res.text
    assert len(sent) == 1
    code, _ = sent[0]

    res = await client.post(
        "http://test/api/v1/auth/verify",
        json={"code": code},
    )
    assert res.status_code == 200, res.text
    cookie = res.cookies.get("admin_session")
    assert cookie is not None
    return {"cookie": f"admin_session={cookie}"}


# ── public read ──────────────────────────────────────────────────────


async def test_list_public_seeded_rows(client: AsyncClient, session: AsyncSession) -> None:
    await _seed_overview(session)
    res = await client.get("http://test/api/v1/overview")
    assert res.status_code == 200, res.text
    data = res.json()
    assert isinstance(data, list)
    assert len(data) == 6
    audiences = {r["audience"] for r in data}
    assert audiences == set(SEED_AUDIENCES)
    for row in data:
        assert row["headline"]
        assert "Siddhesh" in row["headline"]


async def test_get_by_audience_public(client: AsyncClient, session: AsyncSession) -> None:
    await _seed_overview(session)
    res = await client.get("http://test/api/v1/overview/default")
    assert res.status_code == 200, res.text
    row = res.json()
    assert row["audience"] == "default"


async def test_public_filter_leak_guard(session: AsyncSession) -> None:
    import uuid as _uuid

    now = datetime.now(UTC)
    draft_aud = f"_leak_draft_{_uuid.uuid4().hex[:8]}"
    future_aud = f"_leak_future_{_uuid.uuid4().hex[:8]}"
    pub_aud = f"_leak_pub_{_uuid.uuid4().hex[:8]}"
    due_aud = f"_leak_due_{_uuid.uuid4().hex[:8]}"

    draft = OverviewIntro(audience=draft_aud, status=PublishStatus.DRAFT)
    scheduled_future = OverviewIntro(
        audience=future_aud,
        status=PublishStatus.SCHEDULED,
        publish_at=now + timedelta(hours=1),
    )
    published = OverviewIntro(
        audience=pub_aud,
        status=PublishStatus.PUBLISHED,
        published_at=now,
    )
    scheduled_due = OverviewIntro(
        audience=due_aud,
        status=PublishStatus.SCHEDULED,
        publish_at=now - timedelta(hours=1),
    )
    session.add_all([draft, scheduled_future, published, scheduled_due])
    await session.commit()

    visible = set(
        (await session.execute(select(OverviewIntro.id).where(public_filter(OverviewIntro))))
        .scalars()
        .all()
    )

    assert published.id in visible
    assert scheduled_due.id in visible
    assert draft.id not in visible
    assert scheduled_future.id not in visible


# ── admin CRUD ───────────────────────────────────────────────────────


async def test_admin_unauthenticated_rejected(client: AsyncClient) -> None:
    res = await client.get("http://test/api/v1/admin/overview")
    assert res.status_code == 401, res.text


async def test_create_and_get_admin(
    client: AsyncClient,
    session: AsyncSession,
    clean_auth_tables: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cookies = await _auth(client, monkeypatch)

    existing = await session.execute(
        select(OverviewIntro).where(OverviewIntro.audience == "founders")
    )
    row = existing.scalar_one_or_none()
    if row:
        await session.delete(row)
        await session.commit()

    payload = {
        "audience": "founders",
        "headline": "Test Headline",
        "body": "**Test** body content.",
        "status": "published",
    }
    res = await client.post("http://test/api/v1/admin/overview", json=payload, headers=cookies)
    assert res.status_code == 201, res.text
    created = res.json()
    assert created["audience"] == "founders"
    assert created["headline"] == "Test Headline"
    assert created["body"] == "**Test** body content."
    assert created["status"] == "published"
    assert created["published_at"] is not None


async def test_update_admin(
    client: AsyncClient,
    session: AsyncSession,
    clean_auth_tables: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cookies = await _auth(client, monkeypatch)
    await _seed_overview(session)

    res = await client.get("http://test/api/v1/admin/overview", headers=cookies)
    entry = res.json()[0]

    res = await client.patch(
        f"http://test/api/v1/admin/overview/{entry['id']}",
        json={"headline": "Updated", "body": "Fresh"},
        headers=cookies,
    )
    assert res.status_code == 200, res.text
    updated = res.json()
    assert updated["headline"] == "Updated"
    assert updated["body"] == "Fresh"


async def test_delete_admin(
    client: AsyncClient,
    session: AsyncSession,
    clean_auth_tables: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cookies = await _auth(client, monkeypatch)
    await _seed_overview(session)

    res = await client.get("http://test/api/v1/admin/overview", headers=cookies)
    assert len(res.json()) >= 1
    entry = res.json()[0]

    res = await client.delete(f"http://test/api/v1/admin/overview/{entry['id']}", headers=cookies)
    assert res.status_code == 204


async def test_duplicate_audience_rejected(
    client: AsyncClient,
    session: AsyncSession,
    clean_auth_tables: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cookies = await _auth(client, monkeypatch)
    await _seed_overview(session)

    payload = {
        "audience": "default",
        "headline": "Duplicate",
        "body": "should fail",
    }
    res = await client.post("http://test/api/v1/admin/overview", json=payload, headers=cookies)
    assert res.status_code == 422, res.text


async def test_invalid_audience_rejected(
    client: AsyncClient,
    clean_auth_tables: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cookies = await _auth(client, monkeypatch)
    payload = {
        "audience": "aliens",
        "headline": "Nope",
    }
    res = await client.post("http://test/api/v1/admin/overview", json=payload, headers=cookies)
    assert res.status_code == 422, res.text
