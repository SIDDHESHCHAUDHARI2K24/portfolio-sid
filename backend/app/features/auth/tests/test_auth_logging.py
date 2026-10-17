"""Auth and email observability: one outcome line per path, no secrets (E01-W4)."""

import hashlib
import logging
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
import resend
from resend.exceptions import ResendError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import email
from app.core.config import Settings, get_settings
from app.features.auth import service
from app.features.auth.models import OTP_MAX_ATTEMPTS, OtpChallenge
from app.tests.helpers import TEST_ADMIN_PASSWORD

IP = "203.0.113.9"
KNOWN_CODE = "482913"
ADMIN = "admin@example.com"


def _auth_lines(caplog: pytest.LogCaptureFixture) -> list[str]:
    return [r.getMessage() for r in caplog.records if r.name == "app.auth"]


def _mock_send(monkeypatch: pytest.MonkeyPatch, fail: bool = False) -> list[str]:
    sent: list[str] = []

    async def fake(code: str, to: str) -> None:
        sent.append(code)
        if fail:
            raise email.EmailSendError("boom")

    monkeypatch.setattr(email, "send_otp", fake)
    return sent


async def _challenge(
    session: AsyncSession, *, expired: bool = False, attempts: int = 0
) -> None:
    delta = timedelta(seconds=-1) if expired else timedelta(minutes=4)
    session.add(
        OtpChallenge(
            code_hash=hashlib.sha256(KNOWN_CODE.encode()).hexdigest(),
            expires_at=datetime.now(UTC) + delta,
            attempts=attempts,
        )
    )
    await session.commit()


@pytest.fixture(autouse=True)
def _production(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(get_settings(), "environment", "production")


async def test_login_bad_password_line(
    session: AsyncSession,
    clean_auth_tables: None,
    admin_settings: Settings,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO, logger="app.auth")
    with pytest.raises(service.AuthError):
        await service.request_otp(session, "nope", IP)
    assert _auth_lines(caplog) == [f"login rejected reason=bad_password ip={IP}"]


async def test_login_locked_out_line(
    session: AsyncSession,
    clean_auth_tables: None,
    admin_settings: Settings,
    caplog: pytest.LogCaptureFixture,
) -> None:
    for _ in range(service.LOCKOUT_FAILURES):
        with pytest.raises(service.AuthError):
            await service.request_otp(session, "nope", IP)
    caplog.set_level(logging.INFO, logger="app.auth")
    caplog.clear()
    with pytest.raises(service.AuthError) as exc:
        await service.request_otp(session, TEST_ADMIN_PASSWORD, IP)
    assert exc.value.status_code == 429
    assert _auth_lines(caplog) == [f"login rejected reason=locked_out ip={IP}"]


async def test_login_code_sent_line(
    session: AsyncSession,
    clean_auth_tables: None,
    admin_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    _mock_send(monkeypatch)
    caplog.set_level(logging.INFO, logger="app.auth")
    await service.request_otp(session, TEST_ADMIN_PASSWORD, IP)
    assert _auth_lines(caplog) == [f"login accepted code_sent ip={IP}"]


async def test_login_delivery_failure_line(
    session: AsyncSession,
    clean_auth_tables: None,
    admin_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    _mock_send(monkeypatch, fail=True)
    caplog.set_level(logging.INFO, logger="app.auth")
    with pytest.raises(service.AuthError):
        await service.request_otp(session, TEST_ADMIN_PASSWORD, IP)
    assert _auth_lines(caplog) == [f"login failed reason=delivery ip={IP}"]


async def test_login_development_emits_outcome_line(
    session: AsyncSession,
    clean_auth_tables: None,
    admin_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    monkeypatch.setattr(get_settings(), "environment", "development")
    _mock_send(monkeypatch)
    caplog.set_level(logging.INFO)
    await service.request_otp(session, TEST_ADMIN_PASSWORD, IP)
    assert _auth_lines(caplog) == [f"login accepted code_sent ip={IP}"]
    assert any("DEV: OTP" in r.getMessage() for r in caplog.records)


async def test_verify_no_challenge_line(
    session: AsyncSession,
    clean_auth_tables: None,
    admin_settings: Settings,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO, logger="app.auth")
    with pytest.raises(service.AuthError):
        await service.verify_otp(session, KNOWN_CODE, IP)
    assert _auth_lines(caplog) == [f"otp rejected reason=no_challenge ip={IP}"]


async def test_verify_expired_line(
    session: AsyncSession,
    clean_auth_tables: None,
    admin_settings: Settings,
    caplog: pytest.LogCaptureFixture,
) -> None:
    await _challenge(session, expired=True)
    caplog.set_level(logging.INFO, logger="app.auth")
    with pytest.raises(service.AuthError):
        await service.verify_otp(session, KNOWN_CODE, IP)
    assert _auth_lines(caplog) == [f"otp rejected reason=expired ip={IP}"]


async def test_verify_max_attempts_line(
    session: AsyncSession,
    clean_auth_tables: None,
    admin_settings: Settings,
    caplog: pytest.LogCaptureFixture,
) -> None:
    await _challenge(session, attempts=OTP_MAX_ATTEMPTS)
    caplog.set_level(logging.INFO, logger="app.auth")
    with pytest.raises(service.AuthError):
        await service.verify_otp(session, KNOWN_CODE, IP)
    assert _auth_lines(caplog) == [f"otp rejected reason=max_attempts ip={IP}"]


async def test_verify_mismatch_and_accepted_lines(
    session: AsyncSession,
    clean_auth_tables: None,
    admin_settings: Settings,
    caplog: pytest.LogCaptureFixture,
) -> None:
    await _challenge(session)
    caplog.set_level(logging.INFO, logger="app.auth")
    with pytest.raises(service.AuthError):
        await service.verify_otp(session, "000000", IP)
    await service.verify_otp(session, KNOWN_CODE, IP)
    assert _auth_lines(caplog) == [
        f"otp rejected reason=mismatch ip={IP}",
        f"otp accepted ip={IP}",
    ]


def _patch_resend(monkeypatch: pytest.MonkeyPatch, result: Any) -> None:
    def send(payload: Any) -> Any:
        if isinstance(result, Exception):
            raise result
        return result

    monkeypatch.setattr(resend.Emails, "send", staticmethod(send))
    monkeypatch.setattr(get_settings(), "resend_api_key", "re_secretkey123")


async def test_email_success_line(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    _patch_resend(monkeypatch, {"id": "abc-123"})
    caplog.set_level(logging.INFO, logger="app.core.email")
    await email.send_email(to=ADMIN, subject="s", html="<p>x</p>")
    assert [r.getMessage() for r in caplog.records] == [
        "email sent id=abc-123 to_domain=example.com"
    ]


async def test_email_success_without_id_logs_none(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    _patch_resend(monkeypatch, {})
    caplog.set_level(logging.INFO, logger="app.core.email")
    await email.send_email(to=ADMIN, subject="s", html="<p>x</p>")
    assert [r.getMessage() for r in caplog.records] == [
        "email sent id=none to_domain=example.com"
    ]


async def test_email_resend_error_logs_status_and_redacts_address(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    err = ResendError(
        code=403,
        error_type="validation_error",
        message=f"You can only send to {ADMIN} " + "x" * 400,
        suggested_action="",
    )
    _patch_resend(monkeypatch, err)
    caplog.set_level(logging.INFO, logger="app.core.email")
    with pytest.raises(email.EmailSendError):
        await email.send_email(to=ADMIN, subject="s", html="<p>x</p>")
    (record,) = caplog.records
    msg = record.getMessage()
    assert record.levelno == logging.ERROR
    assert msg.startswith("email send failed error=ResendError status=403 message=")
    assert ADMIN not in msg and "@" not in msg
    assert len(msg.split("message=", 1)[1]) <= 200


async def test_email_non_resend_error_status_none(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    _patch_resend(monkeypatch, TimeoutError("timed out"))
    caplog.set_level(logging.INFO, logger="app.core.email")
    with pytest.raises(email.EmailSendError):
        await email.send_email(to=ADMIN, subject="s", html="<p>x</p>")
    (record,) = caplog.records
    assert record.getMessage() == (
        "email send failed error=TimeoutError status=none message=timed out"
    )


async def test_no_secrets_in_any_log_record(
    session: AsyncSession,
    clean_auth_tables: None,
    admin_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Every path, production mode: no code, password, recipient or key in logs."""
    caplog.set_level(logging.DEBUG)
    password = TEST_ADMIN_PASSWORD
    bad = "wrong-pw-SECRET-xyz"

    # Real email path with Resend mocked: success then provider failure.
    codes: list[str] = []
    real_send_otp = email.send_otp

    async def capture(code: str, to: str) -> None:
        codes.append(code)
        await real_send_otp(code, to)

    monkeypatch.setattr(email, "send_otp", capture)
    monkeypatch.setattr(get_settings(), "admin_email", ADMIN)
    _patch_resend(monkeypatch, {"id": "abc-123"})
    await service.request_otp(session, password, IP)  # code_sent
    _patch_resend(
        monkeypatch,
        ResendError(
            code=422,
            error_type="x",
            message=f"bad recipient {ADMIN} key re_secretkey123",
            suggested_action="",
        ),
    )
    with pytest.raises(service.AuthError):
        await service.request_otp(session, password, IP)  # delivery

    with pytest.raises(service.AuthError):
        await service.request_otp(session, bad, IP)  # bad_password

    await _challenge(session)
    with pytest.raises(service.AuthError):
        await service.verify_otp(session, "000000", IP)  # mismatch
    await service.verify_otp(session, KNOWN_CODE, IP)  # accepted
    with pytest.raises(service.AuthError):
        await service.verify_otp(session, KNOWN_CODE, IP)  # no_challenge
    await _challenge(session, expired=True)
    with pytest.raises(service.AuthError):
        await service.verify_otp(session, KNOWN_CODE, IP)  # expired
    await session.rollback()
    await _challenge(session, attempts=OTP_MAX_ATTEMPTS)
    with pytest.raises(service.AuthError):
        await service.verify_otp(session, KNOWN_CODE, IP)  # max_attempts

    for _ in range(service.LOCKOUT_FAILURES):
        with pytest.raises(service.AuthError):
            await service.request_otp(session, bad, "198.51.100.1")
    with pytest.raises(service.AuthError):
        await service.request_otp(session, password, "198.51.100.1")  # locked_out

    assert codes, "email path must have been exercised"
    forbidden = [KNOWN_CODE, password, bad, ADMIN, "re_", *codes]
    for record in caplog.records:
        text = record.getMessage() + " " + str(record.args)
        for secret in forbidden:
            assert secret not in text, (secret, text)
