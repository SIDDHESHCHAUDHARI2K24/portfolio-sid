# E01-W1 — Restore admin access

**Epic:** E01 Auth · **Ticket:** E01-W1 · **Status:** Done (2026-10-17) · **Depends on:** none

## Purpose
Every production login was rejected at the password check, so no OTP was ever sent (EPIC F1).

## Goal
The admin can sign in to production with a known password.

## Reference files
- `backend/app/cli.py` (`hash-password`)
- `backend/app/features/auth/service.py` (`get_effective_password_hash`)

## Functionality
1. User generated a new Argon2id hash locally with `uv run python -m app.cli hash-password` (getpass prompt; the agent never saw the password).
2. User set `ADMIN_PASSWORD_HASH` on the Railway backend service, which redeployed.
3. Effective hash = the `admin_credentials` row if one exists, else the env var.

## Edge cases
- A row in `admin_credentials` overrides the env var; it must be deleted for an env reset to take effect.
- Quotes or whitespace pasted into the Railway value break the hash (W5 now guards this at startup).
- A tripped shared-IP lockout returns 429 even with the right password; it clears after 15 minutes (W2 removes the shared IP).

## Testing and acceptance criteria
- [x] Admin signed in on production with the new password, received the OTP, and reached the dashboard (user-confirmed 2026-10-17).

## Rollback
Restore the previous `ADMIN_PASSWORD_HASH` from Railway variable history.
