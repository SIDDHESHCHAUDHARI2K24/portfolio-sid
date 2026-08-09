"""Signed admin session cookies.

``itsdangerous.URLSafeTimedSerializer`` — one admin user, no distributed
verification, so a JWT is unwarranted. ``SameSite`` is ``Strict`` in
production and ``Lax`` only in development (conventions invariant 14).
"""

import time
from typing import Any

from fastapi import Response
from itsdangerous import BadSignature, URLSafeTimedSerializer

from app.core.config import get_settings

COOKIE_NAME = "admin_session"
SESSION_MAX_AGE_SECONDS = 8 * 3600


def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(get_settings().session_secret)


def create_session_token() -> str:
    return _serializer().dumps({"sub": "admin", "iat": int(time.time())})


def read_session_token(token: str, max_age: int = SESSION_MAX_AGE_SECONDS) -> dict[str, Any] | None:
    """Payload dict if the signature is valid and fresh, else ``None``."""
    try:
        payload = _serializer().loads(token, max_age=max_age)
    except BadSignature:
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def _cookie_kwargs() -> dict[str, Any]:
    production = get_settings().environment == "production"
    return {
        "max_age": SESSION_MAX_AGE_SECONDS,
        "httponly": True,
        "secure": production,
        "samesite": "strict" if production else "lax",
        "path": "/",
    }


def set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(COOKIE_NAME, token, **_cookie_kwargs())


def clear_session_cookie(response: Response) -> None:
    kwargs = _cookie_kwargs()
    kwargs.pop("max_age")
    response.delete_cookie(COOKIE_NAME, **kwargs)
