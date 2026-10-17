# Epic E01: Auth System

**Status:** W1–W5, W7 implemented and verified locally; production verification pending; W6 optional
**Coordinator:** Coordinator 1
**Opened:** 2026-10-17

## Goal

Restore admin sign-in on production and harden the auth system so that a failed login can be diagnosed from logs alone, a correct password visibly leads to the OTP step, and the lockout and rate limits apply to the real caller instead of the shared proxy.

## Scope

- Admin login (`POST /api/v1/auth/login`), OTP issue and verify, lockout, and rate limiting.
- Email delivery through Resend for the OTP.
- Client IP resolution across the Railway edge, the admin nginx proxy, and uvicorn.
- Session cookie and admin gate behavior, as far as they are touched by the items above.
- Production config validation for every auth-related env var.
- Docs: `docs/features/auth.md`, `docs/handoff/env-vars-registry.md`, the steady-state handoff.

## Non-goals

- Replacing Resend or adding a provider abstraction (`docs/specs/email-provider/PLAN.md` stays deferred).
- Multi-user admin, OAuth, passkeys, backup codes.
- Server-side session revocation. Sessions stay stateless signed cookies with an 8-hour max age.
- Public-site features. The public Next.js site has no auth.

## Findings

Evidence gathered on 2026-10-17 from production env shape, backend logs, and code. No secret values were printed.

| # | Finding | Evidence | Confidence |
|---|---------|----------|------------|
| F1 | Every production login attempt failed the password check. | `ENVIRONMENT=production`; six `POST /api/v1/auth/login` returned 200; no `email send failed` log line; Resend shows zero API usage. In production, a correct password either reaches Resend or returns 502, so 200 with no send is only possible on a password mismatch (`service.py:request_otp`). | High |
| F2 | The env password hash is well formed. | `ADMIN_PASSWORD_HASH` is 97 chars, starts with `$argon2id$`, has five `$` segments, no stray quotes or spaces, parses as argon2. | High |
| F3 | The mismatch was either a DB override row in `admin_credentials` or a hash made from a different password. | Resolved by W1: after the env hash was reset, login worked. | Closed |
| F4 | All requests reach the backend from one IP, the admin nginx container. Lockout and rate limits are therefore global, not per caller. | Every log line shows `10.164.196.239`. uvicorn runs without `--forwarded-allow-ips` (`Dockerfile`), and `client_ip()` reads `request.client.host`. | High |
| F5 | The login endpoint gives the same 200 for right and wrong passwords, so the UI always moves to the OTP screen. The user cannot tell a wrong password from a delivery problem. | `GENERIC_LOGIN_DETAIL`; `admin/src/routes/login.tsx` navigates on any 2xx. | High (by design, now unwanted) |
| F6 | Email failures are logged only as the exception class name, so a Resend rejection cannot be diagnosed from logs. | `core/email.py:send_email`. | High |
| F7 | The Resend sender is `onboarding@resend.dev`, the test sender. It only delivers to the Resend account owner's address. This works today because `ADMIN_EMAIL` is that address, but form notifications and any future recipient will fail. | User confirmed on 2026-10-17. | High |
| F8 | A wrong-password response must not use 401: `admin/src/lib/api.ts` turns every 401 into a redirect to `/login` and drops the message. | `apiFetch` 401 branch. | High |

Verified healthy: `RESEND_API_KEY` set with `re_` prefix, `ADMIN_EMAIL`, `SESSION_SECRET`, `DATABASE_URL` set. Cookie settings are correct for the same-origin admin host.

## Work items

Each work item has its own folder with a `SPEC.md`.

| ID | Title | Depends on | Production action |
|----|-------|-----------|-------------------|
| [E01-W1](E01-W1-restore-admin-access/SPEC.md) | Restore admin access (password reset) — **Done** | none | Done by user |
| [E01-W2](E01-W2-real-client-ip/SPEC.md) | Resolve the real client IP behind the proxy | none | Deploy |
| [E01-W3](E01-W3-explicit-password-feedback/SPEC.md) | Explicit wrong-password feedback | W2 | Deploy |
| [E01-W4](E01-W4-auth-observability/SPEC.md) | Auth and email observability | none | Deploy |
| [E01-W5](E01-W5-prod-config-validation/SPEC.md) | Fail fast on bad auth config in production | W2 | Deploy |
| [E01-W6](E01-W6-resend-sender-domain/SPEC.md) | Verified Resend sender domain (optional) | none | Yes: DNS and env, user-run |
| [E01-W7](E01-W7-local-nonstandard-ports/SPEC.md) | Non-standard local ports (247xx block) | none | No (local and CI only) |

Order: W1 is done. W2 and W4 run in parallel; W3 follows W2 (an explicit password check without per-caller lockout invites brute force); W5 follows W2 (validates `TRUSTED_PROXY_CIDRS`). W2 to W5 ship in a single deploy, after user approval. W6 is optional and run by the user.

## Acceptance criteria (epic)

1. The admin can sign in on production: correct password, OTP email arrives, code accepted, admin pages load.
2. A wrong password shows an error on the login page and does not open the OTP screen.
3. Login attempts from two different external IPs are counted separately for lockout and rate limiting; a forged `X-Forwarded-For` from the client cannot change the recorded IP.
4. A Resend failure produces a log line with the provider's error name, status, and message, and never the code or email body.
5. The backend refuses to start in production when an auth env var is missing or malformed, with a log line naming the variable (not its value).
6. `docs/features/auth.md` and `docs/handoff/env-vars-registry.md` match the shipped behavior.
7. Backend tests, mypy, ruff, admin lint and build all pass.

## Verification plan

- Local: `cd backend && uv run pytest app/features/auth -q`, `uv run mypy app`, `uv run ruff check app`; `cd admin && npm run lint && npm run build`.
- Local end to end: run the stack per `LOCAL.md`, sign in with right and wrong passwords, check the dev OTP endpoint path still works.
- Production, after each deploy (user-approved): one login with a wrong password (expect the error), one with the right password (expect the OTP email and Resend usage to increment), then verify. Check backend logs show the real client IP and the new auth log lines.

## Risks

- W3 deliberately reveals whether a password is correct. Mitigated by W2 (per-caller lockout of 10 failures in 15 minutes, 5 logins per minute) and by the OTP as a second factor.
- W2 depends on how the Railway edge forwards the client IP. The spec includes a verification step before trusting any header.
- W5 can block a deploy if production config is wrong. That is the intent, but the rollback is documented.

## Sessions

- Coordinator 1: `fd08bb3a-b07e-4a18-a7f4-032a1fb0a404` (transcript copy in `transcripts/`, gitignored)
