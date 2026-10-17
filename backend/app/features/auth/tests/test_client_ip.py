"""Lockout and slowapi limits key on the resolved client IP, not the proxy."""

from collections.abc import Iterator

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import email
from app.core.config import Settings, get_settings
from app.features.auth import service
from app.features.auth.models import LoginAttempt
from app.tests.helpers import TEST_ADMIN_PASSWORD

LOGIN_URL = "http://test/api/v1/auth/login"
IP_A = "203.0.113.10"
IP_B = "203.0.113.11"


def _mock_send(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, str]]:
    sent: list[tuple[str, str]] = []

    async def fake_send_otp(code: str, to: str) -> None:
        sent.append((code, to))

    monkeypatch.setattr(email, "send_otp", fake_send_otp)
    return sent


@pytest.fixture
def trusted_test_peer(admin_settings: Settings) -> Iterator[None]:
    """The ASGI test transport's peer is 127.0.0.1; trust it as the proxy."""
    settings = get_settings()
    old = settings.trusted_proxy_cidrs
    settings.trusted_proxy_cidrs = ["127.0.0.0/8"]
    yield
    settings.trusted_proxy_cidrs = old


async def test_lockout_is_per_real_ip_behind_trusted_proxy(
    client: httpx.AsyncClient,
    session: AsyncSession,
    clean_auth_tables: None,
    trusted_test_peer: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sent = _mock_send(monkeypatch)
    session.add_all(
        [LoginAttempt(ip=IP_A, outcome="failure") for _ in range(service.LOCKOUT_FAILURES)]
    )
    await session.commit()

    locked = await client.post(
        LOGIN_URL, json={"password": TEST_ADMIN_PASSWORD}, headers={"X-Real-IP": IP_A}
    )
    assert locked.status_code == 429
    assert sent == []

    other = await client.post(
        LOGIN_URL, json={"password": TEST_ADMIN_PASSWORD}, headers={"X-Real-IP": IP_B}
    )
    assert other.status_code == 200
    assert len(sent) == 1


async def test_failures_are_recorded_against_real_ip(
    client: httpx.AsyncClient,
    session: AsyncSession,
    clean_auth_tables: None,
    trusted_test_peer: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _mock_send(monkeypatch)
    await client.post(LOGIN_URL, json={"password": "wrong"}, headers={"X-Real-IP": IP_A})
    ips = (await session.execute(select(LoginAttempt.ip))).scalars().all()
    assert list(ips) == [IP_A]


async def test_rate_limit_counts_per_real_ip_behind_trusted_proxy(
    client: httpx.AsyncClient,
    clean_auth_tables: None,
    trusted_test_peer: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _mock_send(monkeypatch)
    for _ in range(5):
        response = await client.post(
            LOGIN_URL, json={"password": "wrong"}, headers={"X-Real-IP": IP_A}
        )
        assert response.status_code == 400
    blocked = await client.post(LOGIN_URL, json={"password": "wrong"}, headers={"X-Real-IP": IP_A})
    assert blocked.status_code == 429

    other = await client.post(LOGIN_URL, json={"password": "wrong"}, headers={"X-Real-IP": IP_B})
    assert other.status_code == 400


async def test_forged_header_ignored_when_peer_untrusted(
    client: httpx.AsyncClient,
    clean_auth_tables: None,
    admin_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No trusted CIDRs: rotating X-Real-IP cannot dodge the per-peer limit."""
    _mock_send(monkeypatch)
    assert get_settings().trusted_proxy_cidrs == []
    for i in range(5):
        response = await client.post(
            LOGIN_URL, json={"password": "wrong"}, headers={"X-Real-IP": f"203.0.113.{i}"}
        )
        assert response.status_code == 400
    blocked = await client.post(
        LOGIN_URL, json={"password": "wrong"}, headers={"X-Real-IP": "203.0.113.200"}
    )
    assert blocked.status_code == 429
