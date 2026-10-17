# E01-W4 — Auth and email observability

**Epic:** E01 Auth · **Ticket:** E01-W4 · **Status:** Done locally (production check pending) · **Depends on:** none (rebase onto W3 if it lands first; both touch `request_otp`)

## Purpose
The outage could not be diagnosed from logs: login outcomes are not logged, and email failures log only the exception class name.

## Goal
Every login and verify outcome, and every send result, is diagnosable from Railway logs without exposing secrets.

## Reference files
- `backend/app/core/email.py` (`send_email`)
- `backend/app/features/auth/service.py` (`request_otp`, `verify_otp`)
- `backend/app/features/auth/tests/test_auth.py`
- `docs/features/auth.md`, `docs/conventions.md` (invariant 15: no codes or secrets in logs)

## Functionality
Logger `app.auth` at INFO, one line per outcome, always with `ip=<resolved ip>`:
- Login: `login rejected reason=locked_out|bad_password`, `login accepted code_sent`, `login failed reason=delivery`.
- Verify: `otp rejected reason=no_challenge|expired|max_attempts|mismatch`, `otp accepted`.
- Email (`app.core.email`): success → INFO `email sent id=<resend id> to_domain=<domain>`. Failure → ERROR `email send failed error=<class> status=<code> message=<provider message>`, with the message truncated to 200 characters.
- Never log: the OTP, password, hash, email body or subject, full recipient address, API key, or session token.

## Edge cases
- A non-Resend exception (timeout, DNS) has no status → `status=none`; the class name is still logged.
- The provider message could echo the recipient address → redact `\S+@\S+` from the message before logging.
- A Resend response with no `id` → `id=none`.
- Development path: keep the existing DEV warning; also emit the same outcome lines.
- The log call must never raise (no formatting on `None`).

## Testing
- `caplog` test per outcome line.
- A secret-leak test: run every path with a known password and code, then assert that no log record contains the code, the password, the full recipient address, or `re_`.
- A mocked `resend` exception with a status and message containing an email address → status logged, address redacted.
- `uv run ruff check . && uv run mypy app && uv run pytest -q`.

## Acceptance criteria
- [x] All outcome lines are emitted and tested.
- [x] The leak test passes.
- [x] The `docs/features/auth.md` "Logs" section lists the lines.

## Rollback
Revert and redeploy the backend.
