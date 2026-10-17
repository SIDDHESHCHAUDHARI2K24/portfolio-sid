"""Production auth config validation (no DB required)."""

import logging
from typing import Any

import pytest

from app.core.config import Settings
from app.core.security import hash_password
from app.core.startup_checks import validate_production_auth

SECRET = "s" * 40
API_KEY = "re_abcdefghijklmnop"
EMAIL = "owner@example.com"
SENDER = "portfolio@example.com"
CIDRS = ["10.0.0.0/8"]


def make(**overrides: Any) -> Settings:
    values: dict[str, Any] = {
        "environment": "production",
        "admin_password_hash": hash_password("correct horse battery staple"),
        "session_secret": SECRET,
        "resend_api_key": API_KEY,
        "admin_email": EMAIL,
        "resend_from": SENDER,
        "trusted_proxy_cidrs": CIDRS,
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


def fail_message(**overrides: Any) -> str:
    with pytest.raises(RuntimeError) as exc:
        validate_production_auth(make(**overrides))
    return str(exc.value)


def test_valid_config_passes(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.WARNING):
        validate_production_auth(make())
    assert caplog.records == []


def test_non_production_skips() -> None:
    for env in ("development", "test"):
        validate_production_auth(
            Settings(_env_file=None, environment=env, session_secret="dev-only-secret")
        )


@pytest.mark.parametrize(
    ("var", "field", "bad"),
    [
        ("ADMIN_PASSWORD_HASH", "admin_password_hash", None),
        ("ADMIN_PASSWORD_HASH", "admin_password_hash", ""),
        ("ADMIN_PASSWORD_HASH", "admin_password_hash", "plaintext-password-xyz"),
        ("ADMIN_PASSWORD_HASH", "admin_password_hash", "$argon2id$not-a-real-hash"),
        ("SESSION_SECRET", "session_secret", "dev-only-secret"),
        ("SESSION_SECRET", "session_secret", "short-secret-value"),
        ("SESSION_SECRET", "session_secret", ""),
        ("RESEND_API_KEY", "resend_api_key", None),
        ("RESEND_API_KEY", "resend_api_key", "sk_wrongprefix123"),
        ("ADMIN_EMAIL", "admin_email", None),
        ("ADMIN_EMAIL", "admin_email", "not-an-email"),
        ("ADMIN_EMAIL", "admin_email", "a@b.com, c@d.com"),
        ("ADMIN_EMAIL", "admin_email", "a@localhost"),
        ("RESEND_FROM", "resend_from", ""),
    ],
)
def test_rule_fails_without_leaking_value(var: str, field: str, bad: str | None) -> None:
    message = fail_message(**{field: bad})
    assert var in message
    if bad:
        assert bad not in message
        assert bad[:6] not in message


def test_hash_with_wrong_variant_fails() -> None:
    from argon2 import PasswordHasher, Type

    h = PasswordHasher(type=Type.I).hash("pw")
    message = fail_message(admin_password_hash=h)
    assert "ADMIN_PASSWORD_HASH" in message
    assert h[:12] not in message


def test_multiple_failures_all_reported() -> None:
    message = fail_message(
        admin_password_hash=None,
        session_secret="dev-only-secret",
        resend_api_key="bad",
        admin_email="bad",
        resend_from="",
    )
    for var in (
        "ADMIN_PASSWORD_HASH",
        "SESSION_SECRET",
        "RESEND_API_KEY",
        "ADMIN_EMAIL",
        "RESEND_FROM",
    ):
        assert var in message


def test_default_session_secret_fails() -> None:
    with pytest.raises(RuntimeError, match="SESSION_SECRET"):
        validate_production_auth(
            Settings(_env_file=None, environment="production", trusted_proxy_cidrs=CIDRS)
        )


@pytest.mark.parametrize("wrap", ['"{}"', "'{}'", " {}", "{} ", "{}\n", "`{}`"])
@pytest.mark.parametrize(
    ("var", "field", "good"),
    [
        ("SESSION_SECRET", "session_secret", SECRET),
        ("RESEND_API_KEY", "resend_api_key", API_KEY),
        ("ADMIN_EMAIL", "admin_email", EMAIL),
        ("RESEND_FROM", "resend_from", SENDER),
    ],
)
def test_quoted_or_padded_values_fail(wrap: str, var: str, field: str, good: str) -> None:
    bad = wrap.format(good)
    message = fail_message(**{field: bad})
    assert var in message
    assert good not in message


@pytest.mark.parametrize("wrap", ['"{}"', "'{}'", " {}", "{} "])
def test_quoted_or_padded_hash_fails(wrap: str) -> None:
    good = hash_password("pw")
    message = fail_message(admin_password_hash=wrap.format(good))
    assert "ADMIN_PASSWORD_HASH" in message
    assert good[:12] not in message


def test_error_logged_with_names_only(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.ERROR), pytest.raises(RuntimeError):
        validate_production_auth(make(resend_api_key="bad-key-value"))
    assert "RESEND_API_KEY" in caplog.text
    assert "bad-key-value" not in caplog.text


def test_sandbox_sender_warns_but_passes(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.WARNING):
        validate_production_auth(make(resend_from="onboarding@resend.dev"))
    assert "RESEND_FROM" in caplog.text


def test_empty_trusted_proxy_cidrs_warns_but_passes(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.WARNING):
        validate_production_auth(make(trusted_proxy_cidrs=[]))
    assert "TRUSTED_PROXY_CIDRS" in caplog.text


def test_invalid_cidr_rejected_by_settings() -> None:
    with pytest.raises(ValueError, match="TRUSTED_PROXY_CIDRS"):
        make(trusted_proxy_cidrs=["not-a-cidr"])
