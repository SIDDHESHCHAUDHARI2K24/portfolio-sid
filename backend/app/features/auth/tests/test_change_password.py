"""Change-password: DB override + authenticated rotation."""

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.core.session import COOKIE_NAME, create_session_token
from app.features.auth import service
from app.features.auth.models import AdminCredential
from app.tests.helpers import TEST_ADMIN_PASSWORD

CHANGE_URL = "http://test/api/v1/admin/change-password"
LOGIN_URL = "http://test/api/v1/auth/login"
ME_URL = "http://test/api/v1/admin/me"


@pytest.mark.asyncio
async def test_get_effective_hash_falls_back_to_env_when_db_empty(
    session: AsyncSession, admin_settings
) -> None:
    # Ensure no row
    from sqlalchemy import text
    await session.execute(text("DELETE FROM admin_credentials"))
    await session.commit()
    h = await service.get_effective_password_hash(session)
    assert h == admin_settings.admin_password_hash
    assert verify_password(h, TEST_ADMIN_PASSWORD)


@pytest.mark.asyncio
async def test_get_effective_hash_uses_db_when_present(
    session: AsyncSession, admin_settings
) -> None:
    from sqlalchemy import text

    await session.execute(text("DELETE FROM admin_credentials"))
    await session.commit()
    db_hash = hash_password("db-only-password-123")
    session.add(AdminCredential(password_hash=db_hash))
    await session.commit()

    h = await service.get_effective_password_hash(session)
    assert h == db_hash
    assert verify_password(h, "db-only-password-123")
    assert not verify_password(h, TEST_ADMIN_PASSWORD)

    # cleanup
    await session.execute(text("DELETE FROM admin_credentials"))
    await session.commit()


@pytest.mark.asyncio
async def test_change_password_happy_path_rotates_and_login_uses_new(
    client: httpx.AsyncClient,
    session: AsyncSession,
    clean_auth_tables,
    admin_settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.core import email

    async def fake_send_otp(code: str, to: str) -> None:
        pass

    monkeypatch.setattr(email, "send_otp", fake_send_otp)
    # Cleanup admin_credentials
    from sqlalchemy import text

    await session.execute(text("DELETE FROM admin_credentials"))
    await session.commit()

    # 1. login with env password works
    resp = await client.post(LOGIN_URL, json={"password": TEST_ADMIN_PASSWORD})
    assert resp.status_code == 200

    # 2. authenticate via session cookie and change
    client.cookies.set(COOKIE_NAME, create_session_token())
    new_pw = "new-secure-password-123"
    resp = await client.post(
        CHANGE_URL, json={"current_password": TEST_ADMIN_PASSWORD, "new_password": new_pw}
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"

    # 3. verify DB row holds new hash
    cred = (await session.execute(select(AdminCredential))).scalars().first()
    assert cred is not None
    assert verify_password(cred.password_hash, new_pw)

    # 4. new password logs in (need fresh client without session)
    # Clear session cookie first
    client.cookies.clear()
    resp = await client.post(LOGIN_URL, json={"password": new_pw})
    assert resp.status_code == 200

    # 5. old password still returns generic but does not send OTP (same UX)
    # It should now be treated as wrong password
    # We check that OTP not sent and failure recorded
    # Login with old now is failure path — cannot create challenge
    from sqlalchemy import func

    # Count challenges before
    from app.features.auth.models import OtpChallenge

    before = (await session.execute(select(func.count()).select_from(OtpChallenge))).scalar_one()
    resp = await client.post(LOGIN_URL, json={"password": TEST_ADMIN_PASSWORD})
    assert resp.status_code == 200
    after = (await session.execute(select(func.count()).select_from(OtpChallenge))).scalar_one()
    # No new challenge for wrong password (old)
    # new_login_invalidates_previous ensures old would have created one if correct
    # So after should == before (or before after change, the old password fails)
    # We issued one with new_pw above, so there is 1 unconsumed; old should not add
    assert after == before

    # cleanup
    await session.execute(text("DELETE FROM admin_credentials"))
    await session.commit()
    client.cookies.clear()


@pytest.mark.asyncio
async def test_change_password_wrong_current_rejected(
    client: httpx.AsyncClient,
    clean_auth_tables,
    admin_settings,
) -> None:
    client.cookies.set(COOKIE_NAME, create_session_token())
    resp = await client.post(
        CHANGE_URL,
        json={
            "current_password": "wrong-current-pass",
            "new_password": "new-secure-password-123",
        },
    )
    assert resp.status_code == 403
    assert "incorrect" in resp.json()["detail"].lower()
    client.cookies.clear()


@pytest.mark.asyncio
async def test_change_password_validation_short_rejected(
    client: httpx.AsyncClient,
    clean_auth_tables,
    admin_settings,
) -> None:
    client.cookies.set(COOKIE_NAME, create_session_token())
    resp = await client.post(
        CHANGE_URL, json={"current_password": TEST_ADMIN_PASSWORD, "new_password": "short"}
    )
    # Pydantic validation gives 422, service also 400; either is acceptable but we expect 422
    assert resp.status_code in (400, 422)
    client.cookies.clear()


@pytest.mark.asyncio
async def test_change_password_same_as_current_rejected(
    client: httpx.AsyncClient,
    clean_auth_tables,
    admin_settings,
) -> None:
    client.cookies.set(COOKIE_NAME, create_session_token())
    resp = await client.post(
        CHANGE_URL,
        json={
            "current_password": TEST_ADMIN_PASSWORD,
            "new_password": TEST_ADMIN_PASSWORD,
        },
    )
    assert resp.status_code == 400
    assert "differ" in resp.json()["detail"].lower()
    client.cookies.clear()


@pytest.mark.asyncio
async def test_change_password_requires_auth(
    client: httpx.AsyncClient,
    clean_auth_tables,
    admin_settings,
) -> None:
    client.cookies.clear()
    resp = await client.post(
        CHANGE_URL,
        json={
            "current_password": TEST_ADMIN_PASSWORD,
            "new_password": "new-secure-password-123",
        },
    )
    assert resp.status_code == 401
