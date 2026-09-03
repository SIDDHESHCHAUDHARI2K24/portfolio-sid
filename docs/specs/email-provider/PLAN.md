# Plan — Email Provider Abstraction (Deferred, Keep Resend)

**Status:** Deferred per 2026-08-31 decision — keep `Resend` for prod, add swappable `EmailProvider` later. **Do not implement in the manual handoff session.**

## Why
`backend/app/core/email.py:1` is the sole `resend>=2.35.0` consumer (`resend.api_key` + `to_thread(Emails.send)` → OTP critical path `auth/service.py:134` / `forms/service.py:73`). Two templates to one inbox (OTP 6-digit, `New Contact/Dealflow`). User wants self-host trial with fallback — abstraction (~30 LoC, no call-site rewrites) is the correct seam. `resend` 3k/mo free + managed DKIM/warm IPs prevents OTP spam-lockout today; any self-host still needs SMTP relay.

## Important note
`freesend.io` ≠ email (file transfer). The Resend-compatible self-host is `sluhtie/freesend` (1★, 1 commit, Postgres+`pg-boss`, one image, BYO SMTP, `POST /api/v1/emails` `fs_live_`, DKIM `nodemailer`). It **does not deliver itself** — deliverability is the relay. Not prod-ready for OTP.

## Scope (when implemented)
- **`backend/app/core/email.py:1`** → `Protocol EmailProvider { async send(*, to, subject, html) }` + `ResendProvider` (current), `FreesendProvider` (`baseUrl=FREESEND_BASE_URL`, `fs_live_`), `SmtpProvider` (`aiosmtplib`) / `SesProvider` (`boto3`), factory via `EMAIL_PROVIDER` env (`resend|freesend|smtp|ses`, default `resend`).
- **`backend/app/core/config.py:52`** + `backend/.env.example` + `docs/handoff/env-vars-registry.md:25` add `EMAIL_PROVIDER`, `FREESEND_BASE_URL/API_KEY` or `SMTP_HOST/PORT/USER/PASS/FROM`.
- **`docker-compose.yml:1`** add `mailpit:1025:8025` dev only (not MailHog).
- **Call sites unchanged** — `auth/service.py` `502` rollback + `development` swallow + `forms/service.py` skip/swallow preserved; tests patch `email.send_email`/`send_otp` remain green (`auth/tests/test_auth.py:30`, `forms/tests/test_forms.py:44`, `conftest.py:94`).
- **Railway:** 587 outbound only (blocks 25 inbound, so Postal/Mailu off-Railway VMs out of scope). For self-host trial: SES `us-east-1` verified domain + Cloudflare DNS, env `EMAIL_PROVIDER=smtp` with `railway variable set`.

## Acceptance
- Default `resend` behavior unchanged; `pytest app/features/auth app/features/forms` green after toggle; OTP failure still `502` + challenge deleted in prod, warned in `development`.
- `RESEND_API_KEY` backward compatible until migration; new provider toggle via env only; no frontend changes.

## Effort
~0.5 day. Wire after hosting stable (+ Umami/GlitchTip DNS). Do not wire in the manual-infra session — track as `TD-34/35`-adjacent tech-debt.

## Temporal (F29 voice agent)
Deferred — no `temporal|celery|arq` deps (`pyproject.toml`), `scheduler.py:1` 5-min idempotent `publishables` + `run_crawler_retention` 90d stays cron (`railway.toml` + `Dockerfile` reuse). F29 `backend/app/features/agent/` deferred, no scheduling requirements. Re-evaluate only when voice agent spec gains durable timers/retries (STT→LLM→TTS + human waits) — compare Temporal vs lightweight `arq`/`pg-boss` vs LangGraph persistence.
