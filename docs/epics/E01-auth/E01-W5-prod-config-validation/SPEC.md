# E01-W5 — Fail fast on bad auth config in production

**Epic:** E01 Auth · **Ticket:** E01-W5 · **Status:** Ready · **Depends on:** W2 (validates `TRUSTED_PROXY_CIDRS`)

## Purpose
Bad auth config fails silently. A missing hash means every login checks against the timing decoy and returns 200 forever. A missing key or email shows up only when someone tries to sign in. The deploy still looks healthy.

## Goal
In production, the backend refuses to start with a missing or malformed auth setting and logs which variable is wrong (never its value). Railway then keeps the previous deployment serving.

## Reference files
- `backend/app/core/config.py` (`Settings`; `session_secret` defaults to `"dev-only-secret"`)
- `backend/app/app.py` (`create_app`)
- `backend/app/core/startup_checks.py` (new), `backend/app/tests/test_startup_checks.py` (new)
- `docs/handoff/env-vars-registry.md`

## Functionality
`validate_production_auth(settings)` is called first in `create_app()` when `environment == "production"`. It collects every failure, then raises one `RuntimeError` listing the variable names.

| Variable | Rule |
|---|---|
| `ADMIN_PASSWORD_HASH` | set, starts with `$argon2id$`, parses with argon2 |
| `SESSION_SECRET` | set, not `dev-only-secret`, at least 32 characters |
| `RESEND_API_KEY` | set, starts with `re_` |
| `ADMIN_EMAIL` | set, a single `local@domain.tld` |
| `RESEND_FROM` | present in the process environment (the settings default is non-empty, so only an explicit variable counts), no surrounding whitespace, and no quotes around a bare address (`"Name" <a@b.co>` is fine); if it is `onboarding@resend.dev`, log a WARNING (owner-only delivery) but do not fail |
| `TRUSTED_PROXY_CIDRS` | every entry parses as a CIDR (empty allowed, with a WARNING) |

## Edge cases
- Surrounding quotes or whitespace in a value → fail, naming the variable (this is the common Railway paste error).
- A DB override row exists while the env hash is fine → no check (the DB is not available at startup); out of scope.
- Development and test environments → skip entirely, so local dev and CI are unaffected.
- Several failures → report them all at once, not just the first.
- `RAILWAY_ENVIRONMENT_NAME=production` with `ENVIRONMENT` not `production` → fail naming `ENVIRONMENT`, so a mis-set variable cannot silently enable dev mode (dev OTP endpoint).
- The message must not contain any value, including partial prefixes.

## Testing
- Unit: each rule fails with the variable name in the message and the value absent; a valid config passes; the warnings fire; non-production skips.
- Confirm production passes before deploy with `docs/epics/E01-auth/transcripts/checks.sh` (all rules passed on 2026-10-17, except `TRUSTED_PROXY_CIDRS`, which W2 adds; set it before deploying W5).
- `uv run ruff check . && uv run mypy app && uv run pytest -q`.

## Acceptance criteria
- [ ] All rules are tested; no value appears in any message.
- [ ] Production passes validation on deploy.
- [ ] The env registry documents the rules.

## Rollback
Revert and redeploy. A failing check never takes down the running deployment; it only blocks the new one. Note: `alembic upgrade head` runs before validation (Dockerfile CMD), so migrations apply even when validation fails, and the rollback relies on the backend healthcheck (`/api/v1/health`) in `.railway/railway.ts`.
