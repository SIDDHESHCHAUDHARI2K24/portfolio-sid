"""Auth flow: login, OTP lifecycle, lockout, rate limit, Cloudflare Access."""

import hashlib
import json
import re
import time
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import httpx
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from jwt.algorithms import RSAAlgorithm
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import access, email
from app.core.config import Settings, get_settings
from app.core.session import COOKIE_NAME, create_session_token
from app.features.auth import service
from app.features.auth.models import OTP_MAX_ATTEMPTS, LoginAttempt, OtpChallenge
from app.tests.helpers import TEST_ADMIN_PASSWORD

LOGIN_URL = "http://test/api/v1/auth/login"
VERIFY_URL = "http://test/api/v1/auth/verify"
ME_URL = "http://test/api/v1/admin/me"


def _mock_send(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, str]]:
    """Replace the Resend send; record (code, to). No live email in tests."""
    sent: list[tuple[str, str]] = []

    async def fake_send_otp(code: str, to: str) -> None:
        sent.append((code, to))

    monkeypatch.setattr(email, "send_otp", fake_send_otp)
    return sent


async def test_login_correct_password_sends_code_and_creates_challenge(
    client: httpx.AsyncClient,
    session: AsyncSession,
    clean_auth_tables: None,
    admin_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sent = _mock_send(monkeypatch)
    response = await client.post(LOGIN_URL, json={"password": TEST_ADMIN_PASSWORD})
    assert response.status_code == 200
    assert response.json() == {"detail": "Code sent."}

    assert len(sent) == 1
    code, to = sent[0]
    assert re.fullmatch(r"\d{6}", code)
    assert to == "admin@example.com"
    assert code not in response.text

    challenges = (await session.execute(select(OtpChallenge))).scalars().all()
    assert len(challenges) == 1
    assert challenges[0].code_hash == hashlib.sha256(code.encode()).hexdigest()
    assert challenges[0].consumed_at is None


async def test_login_wrong_password_returns_400_records_failure_sends_nothing(
    client: httpx.AsyncClient,
    session: AsyncSession,
    clean_auth_tables: None,
    admin_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sent = _mock_send(monkeypatch)
    response = await client.post(LOGIN_URL, json={"password": "definitely-wrong"})
    # 400, never 401: the admin apiFetch redirects on 401 and drops the message.
    assert response.status_code == 400
    assert response.json() == {"detail": "Incorrect password."}
    assert sent == []

    # The failure row must be committed before the error is raised.
    attempts = (await session.execute(select(LoginAttempt))).scalars().all()
    assert len(attempts) == 1
    assert attempts[0].outcome == "failure"
    challenges = (await session.execute(select(OtpChallenge))).scalars().all()
    assert challenges == []


async def test_login_correct_password_records_success_and_replaces_old_challenges(
    client: httpx.AsyncClient,
    session: AsyncSession,
    clean_auth_tables: None,
    admin_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sent = _mock_send(monkeypatch)
    old = OtpChallenge(
        code_hash=hashlib.sha256(b"111111").hexdigest(),
        expires_at=datetime.now(UTC) + timedelta(minutes=4),
    )
    session.add(old)
    await session.commit()
    old_id = old.id

    response = await client.post(LOGIN_URL, json={"password": TEST_ADMIN_PASSWORD})
    assert response.status_code == 200
    assert response.json() == {"detail": "Code sent."}
    assert len(sent) == 1

    session.expire_all()
    outcomes = (await session.execute(select(LoginAttempt.outcome))).scalars().all()
    assert list(outcomes) == ["success"]
    challenges = (await session.execute(select(OtpChallenge))).scalars().all()
    assert len(challenges) == 1
    assert challenges[0].id != old_id


async def test_login_delivery_failure_returns_502_and_deletes_challenge(
    client: httpx.AsyncClient,
    session: AsyncSession,
    clean_auth_tables: None,
    admin_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(get_settings(), "environment", "production")
    calls: list[str] = []

    async def failing_send_otp(code: str, to: str) -> None:
        calls.append(code)
        raise email.EmailSendError("boom")

    monkeypatch.setattr(email, "send_otp", failing_send_otp)
    response = await client.post(LOGIN_URL, json={"password": TEST_ADMIN_PASSWORD})
    assert response.status_code == 502
    assert response.json() == {"detail": "Code delivery failed; try again later."}
    assert len(calls) == 1
    challenges = (await session.execute(select(OtpChallenge))).scalars().all()
    assert challenges == []


async def test_login_development_mode_returns_code_sent_and_exposes_dev_code(
    client: httpx.AsyncClient,
    clean_auth_tables: None,
    admin_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(get_settings(), "environment", "development")
    sent = _mock_send(monkeypatch)
    response = await client.post(LOGIN_URL, json={"password": TEST_ADMIN_PASSWORD})
    assert response.status_code == 200
    assert response.json() == {"detail": "Code sent."}

    dev = await client.get("http://test/api/v1/auth/dev/otp")
    assert dev.status_code == 200
    code = dev.json()["code"]
    assert re.fullmatch(r"\d{6}", code)
    assert sent[0][0] == code
    assert code not in response.text


async def test_login_wrong_password_while_locked_out_returns_429_first(
    client: httpx.AsyncClient,
    session: AsyncSession,
    clean_auth_tables: None,
    admin_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sent = _mock_send(monkeypatch)
    ip = "127.0.0.1"
    session.add_all(
        [LoginAttempt(ip=ip, outcome="failure") for _ in range(service.LOCKOUT_FAILURES)]
    )
    await session.commit()

    response = await client.post(LOGIN_URL, json={"password": "wrong-while-locked"})
    assert response.status_code == 429
    assert response.json() == {"detail": "Too many attempts. Try again later."}
    assert sent == []
    # Lockout runs before the password check: no extra failure row is recorded.
    failures = (
        await session.execute(select(func.count()).select_from(LoginAttempt))
    ).scalar_one()
    assert failures == service.LOCKOUT_FAILURES


async def test_login_missing_password_rejected_422_no_side_effects(
    client: httpx.AsyncClient,
    session: AsyncSession,
    clean_auth_tables: None,
    admin_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sent = _mock_send(monkeypatch)
    # Missing field is a schema error; the schema itself is unchanged by W3.
    response = await client.post(LOGIN_URL, json={})
    assert response.status_code == 422
    assert sent == []
    assert (await session.execute(select(LoginAttempt))).scalars().all() == []


async def test_login_empty_string_password_is_just_a_wrong_password(
    client: httpx.AsyncClient,
    session: AsyncSession,
    clean_auth_tables: None,
    admin_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """LoginRequest has no min_length (SPEC assumed a 422; the UI blocks empty
    submits). Empty string therefore takes the wrong-password path: 400, one
    failure row, no email."""
    sent = _mock_send(monkeypatch)
    response = await client.post(LOGIN_URL, json={"password": ""})
    assert response.status_code == 400
    assert response.json() == {"detail": "Incorrect password."}
    assert sent == []
    outcomes = (await session.execute(select(LoginAttempt.outcome))).scalars().all()
    assert list(outcomes) == ["failure"]


async def test_new_login_invalidates_previous_challenge(
    client: httpx.AsyncClient,
    session: AsyncSession,
    clean_auth_tables: None,
    admin_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _mock_send(monkeypatch)
    for _ in range(2):
        response = await client.post(LOGIN_URL, json={"password": TEST_ADMIN_PASSWORD})
        assert response.status_code == 200
    unconsumed = (
        (await session.execute(select(OtpChallenge).where(OtpChallenge.consumed_at.is_(None))))
        .scalars()
        .all()
    )
    assert len(unconsumed) == 1


async def test_full_flow_correct_otp_sets_cookie_and_admin_me_works(
    client: httpx.AsyncClient,
    clean_auth_tables: None,
    admin_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sent = _mock_send(monkeypatch)
    response = await client.post(LOGIN_URL, json={"password": TEST_ADMIN_PASSWORD})
    assert response.status_code == 200
    code = sent[0][0]
    assert code not in response.text

    response = await client.post(VERIFY_URL, json={"code": code})
    assert response.status_code == 200
    assert code not in response.text
    assert COOKIE_NAME in response.cookies

    response = await client.get(ME_URL)
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert code not in response.text


async def test_verify_wrong_code_generic_and_increments_attempts(
    client: httpx.AsyncClient,
    session: AsyncSession,
    clean_auth_tables: None,
    admin_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sent = _mock_send(monkeypatch)
    await client.post(LOGIN_URL, json={"password": TEST_ADMIN_PASSWORD})
    code = sent[0][0]
    wrong = f"{(int(code) + 1) % 1_000_000:06d}"

    response = await client.post(VERIFY_URL, json={"code": wrong})
    assert response.status_code == 400
    assert response.json() == {"detail": service.GENERIC_OTP_DETAIL}
    assert code not in response.text

    challenge = (await session.execute(select(OtpChallenge))).scalars().one()
    assert challenge.attempts == 1


async def test_verify_expired_code_rejected(
    client: httpx.AsyncClient,
    session: AsyncSession,
    clean_auth_tables: None,
    admin_settings: Settings,
) -> None:
    session.add(
        OtpChallenge(
            code_hash=hashlib.sha256(b"123456").hexdigest(),
            expires_at=datetime.now(UTC) - timedelta(seconds=1),
        )
    )
    await session.commit()
    response = await client.post(VERIFY_URL, json={"code": "123456"})
    assert response.status_code == 400
    assert "expired" in response.json()["detail"].lower()


async def test_verify_consumed_code_rejected(
    client: httpx.AsyncClient,
    clean_auth_tables: None,
    admin_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sent = _mock_send(monkeypatch)
    await client.post(LOGIN_URL, json={"password": TEST_ADMIN_PASSWORD})
    code = sent[0][0]
    assert (await client.post(VERIFY_URL, json={"code": code})).status_code == 200

    response = await client.post(VERIFY_URL, json={"code": code})
    assert response.status_code == 400
    assert response.json() == {"detail": service.GENERIC_OTP_DETAIL}


async def test_verify_over_attempt_challenge_rejected(
    client: httpx.AsyncClient,
    session: AsyncSession,
    clean_auth_tables: None,
    admin_settings: Settings,
) -> None:
    session.add(
        OtpChallenge(
            code_hash=hashlib.sha256(b"123456").hexdigest(),
            expires_at=datetime.now(UTC) + timedelta(minutes=4),
            attempts=OTP_MAX_ATTEMPTS,
        )
    )
    await session.commit()
    response = await client.post(VERIFY_URL, json={"code": "123456"})
    assert response.status_code == 429


async def test_lockout_db_backed_rejects_even_correct_password(
    session: AsyncSession,
    admin_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sent = _mock_send(monkeypatch)
    ip = "203.0.113.7"
    for _ in range(service.LOCKOUT_FAILURES):
        # The 10th failure itself still answers 400; lockout bites on the 11th.
        with pytest.raises(service.AuthError) as wrong:
            await service.request_otp(session, "wrong-password", ip)
        assert wrong.value.status_code == 400
        assert wrong.value.detail == "Incorrect password."

    failures = (
        await session.execute(
            select(func.count())
            .select_from(LoginAttempt)
            .where(LoginAttempt.ip == ip, LoginAttempt.outcome == "failure")
        )
    ).scalar_one()
    assert failures == service.LOCKOUT_FAILURES

    with pytest.raises(service.AuthError) as excinfo:
        await service.request_otp(session, TEST_ADMIN_PASSWORD, ip)
    assert excinfo.value.status_code == 429
    assert sent == []

    detail = await service.request_otp(session, TEST_ADMIN_PASSWORD, "203.0.113.8")
    assert detail == "Code sent."


async def test_success_clears_failure_window(
    session: AsyncSession,
    admin_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _mock_send(monkeypatch)
    ip = "203.0.113.9"
    for _ in range(service.LOCKOUT_FAILURES):
        with pytest.raises(service.AuthError):
            await service.request_otp(session, "wrong-password", ip)
    session.add(LoginAttempt(ip=ip, outcome="success"))
    await session.commit()

    detail = await service.request_otp(session, TEST_ADMIN_PASSWORD, ip)
    assert detail == "Code sent."


async def test_login_rate_limit_returns_429_json(
    client: httpx.AsyncClient,
    clean_auth_tables: None,
    admin_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _mock_send(monkeypatch)
    for _ in range(5):
        response = await client.post(LOGIN_URL, json={"password": "wrong"})
        assert response.status_code == 400
    response = await client.post(LOGIN_URL, json={"password": "wrong"})
    assert response.status_code == 429
    assert "detail" in response.json()
    assert response.json()["detail"] != "Incorrect password."


@pytest.fixture(scope="module")
def rsa_private_key() -> rsa.RSAPrivateKey:
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.fixture
def cf_enabled(admin_settings: Settings) -> Iterator[Settings]:
    settings = get_settings()
    settings.cf_access_enabled = True
    settings.cf_access_team_domain = "test-team.cloudflareaccess.com"
    settings.cf_access_aud = "test-aud-tag"
    yield settings
    settings.cf_access_enabled = False
    settings.cf_access_team_domain = None
    settings.cf_access_aud = None


@pytest.fixture
def injected_jwks(rsa_private_key: rsa.RSAPrivateKey) -> Iterator[None]:
    jwk = json.loads(RSAAlgorithm.to_jwk(rsa_private_key.public_key()))
    jwk["kid"] = "test-kid"
    saved = dict(access._jwks_cache)
    access._jwks_cache["jwks"] = jwt.PyJWKSet([jwk])
    access._jwks_cache["fetched_at"] = time.monotonic()
    yield
    access._jwks_cache.clear()
    access._jwks_cache.update(saved)


async def test_cf_disabled_requires_only_session_cookie(
    client: httpx.AsyncClient, clean_auth_tables: None, admin_settings: Settings
) -> None:
    assert get_settings().cf_access_enabled is False
    client.cookies.set(COOKIE_NAME, create_session_token())
    response = await client.get(ME_URL)
    assert response.status_code == 200


async def test_cf_enabled_missing_assertion_403(
    client: httpx.AsyncClient,
    clean_auth_tables: None,
    admin_settings: Settings,
    cf_enabled: Settings,
) -> None:
    client.cookies.set(COOKIE_NAME, create_session_token())
    response = await client.get(ME_URL)
    assert response.status_code == 403


async def test_cf_enabled_invalid_assertion_403(
    client: httpx.AsyncClient,
    clean_auth_tables: None,
    admin_settings: Settings,
    cf_enabled: Settings,
    injected_jwks: None,
) -> None:
    client.cookies.set(COOKIE_NAME, create_session_token())
    response = await client.get(
        ME_URL,
        headers={"Cf-Access-Jwt-Assertion": "not-a-jwt"},
    )
    assert response.status_code == 403


async def test_cf_enabled_valid_assertion_allowed(
    client: httpx.AsyncClient,
    clean_auth_tables: None,
    admin_settings: Settings,
    cf_enabled: Settings,
    injected_jwks: None,
    rsa_private_key: rsa.RSAPrivateKey,
) -> None:
    now = int(time.time())
    assertion = jwt.encode(
        {
            "aud": "test-aud-tag",
            "iss": "https://test-team.cloudflareaccess.com",
            "sub": "admin@example.com",
            "iat": now,
            "exp": now + 300,
        },
        rsa_private_key,
        algorithm="RS256",
        headers={"kid": "test-kid"},
    )
    client.cookies.set(COOKIE_NAME, create_session_token())
    response = await client.get(
        ME_URL,
        headers={"Cf-Access-Jwt-Assertion": assertion},
    )
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
