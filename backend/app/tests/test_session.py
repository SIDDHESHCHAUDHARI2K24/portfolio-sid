"""Session tokens and cookie security flags."""

import httpx
import pytest
from fastapi import Response

from app.core.config import Settings, get_settings
from app.core.session import (
    COOKIE_NAME,
    SESSION_MAX_AGE_SECONDS,
    create_session_token,
    read_session_token,
    set_session_cookie,
)

ME_URL = "http://test/api/v1/admin/me"


def test_token_roundtrip() -> None:
    payload = read_session_token(create_session_token())
    assert payload is not None
    assert payload["sub"] == "admin"
    assert isinstance(payload["iat"], int)


def test_tampered_token_rejected() -> None:
    token = create_session_token()
    tampered = token[:-2] + ("aa" if not token.endswith("aa") else "bb")
    assert read_session_token(tampered) is None


def test_expired_token_rejected() -> None:
    assert read_session_token(create_session_token(), max_age=-1) is None


def test_production_cookie_flags(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(get_settings(), "environment", "production")
    response = Response()
    set_session_cookie(response, create_session_token())
    header = response.headers["set-cookie"].lower()
    assert "httponly" in header
    assert "secure" in header
    assert "samesite=strict" in header
    assert "path=/" in header
    assert f"max-age={SESSION_MAX_AGE_SECONDS}" in header


def test_dev_cookie_flags(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(get_settings(), "environment", "development")
    response = Response()
    set_session_cookie(response, create_session_token())
    header = response.headers["set-cookie"].lower()
    assert "samesite=lax" in header
    assert "secure" not in header
    assert "httponly" in header


async def test_admin_me_without_cookie_401(
    client: httpx.AsyncClient, admin_settings: Settings
) -> None:
    response = await client.get(ME_URL)
    assert response.status_code == 401


async def test_admin_me_tampered_cookie_401(
    client: httpx.AsyncClient, admin_settings: Settings
) -> None:
    token = create_session_token()
    tampered = token[:-2] + ("aa" if not token.endswith("aa") else "bb")
    client.cookies.set(COOKIE_NAME, tampered)
    response = await client.get(ME_URL)
    assert response.status_code == 401
