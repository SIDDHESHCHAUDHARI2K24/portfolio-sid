# TD-17: Admin Auth & Anti-Abuse — Argon2, OTP, Resend, Session, Lockout, Access JWT

**Phase:** P1 · **Wave:** 5 · **Executor:** agent · **Effort:** XL (3–4 days)
**Source:** development-plan-P1.md → P1.T2 (S1–S7)
**Depends on:** TD-16, TD-M3 · **Blocks:** TD-23

## Purpose
With no domain-gated Access in the interim and a public repository
documenting the entire API surface, app-layer auth is the only barrier. It
has to be right rather than adequate: password + hashed OTP + signed session
+ rate limiting + DB-backed lockout, with Cloudflare Access verification
ready for when the edge gate turns on.

## Paths
- Create: `backend/app/core/security.py`, `backend/app/core/email.py`, `backend/app/core/deps.py`, `backend/app/core/antispam.py`, `backend/app/features/auth/` (models, schemas, service, router), `backend/app/cli.py`
- Modify: `backend/app/core/config.py`, `backend/app/core/models_registry.py`, new migration (`OtpChallenge`, `LoginAttempt`)

## Steps
1. Argon2id via `argon2-cffi` `PasswordHasher` with library defaults; CLI `uv run python -m app.cli hash-password` generates the hash offline; hash stored only as `ADMIN_PASSWORD_HASH` env via pydantic-settings — no password in DB, code, or git; catch `VerifyMismatchError` explicitly; return an identical generic response for wrong-password and unknown-state so responses and timing reveal nothing
2. OTP: `secrets.randbelow(1_000_000)` zero-padded to six digits — never `random`; store hashed with SHA-256 (Argon2 cost is unwarranted for a five-minute secret and would be paid on every attempt); compare with `hmac.compare_digest`
3. `OtpChallenge` model: `id`, `code_hash`, `expires_at` (5-minute TTL), `attempts` (max 5), `consumed_at`, `created_ip`; issuing a new challenge invalidates any outstanding one — an attacker cannot widen the valid-code space by requesting many
4. `core/email.py`: wrap the Resend SDK with `send_otp(code)` so Phase 2 form notifications reuse one client; send asynchronously but **await the result before returning success** — fire-and-forget that silently fails locks you out with no signal; log delivery failures at error level
5. Session: `itsdangerous.URLSafeTimedSerializer(SESSION_SECRET)`; cookie flags `HttpOnly`, `Secure`, `SameSite=Strict`, `max_age=8h`, `path=/` — `Lax` permitted via config in development only, never production; no JWT (one user, no distributed verification); rotate the session value on login; `require_admin()` dependency in `core/deps.py` raises 401 on absent or invalid cookie
6. Anti-abuse: `slowapi` IP limits — login 5/min, OTP issuance 3/15min; DB-backed `LoginAttempt` (IP, timestamp, outcome) with lockout after 10 failures in 15 minutes — the DB counter is replica-safe and the real protection; slowapi is the cheap first line; success clears the counter; 429 with generic message
7. Cloudflare Access: verify `Cf-Access-Jwt-Assertion` with PyJWT against `https://<team>.cloudflareaccess.com/cdn-cgi/access/certs`, cached with a TTL — never fetched per request; validate `aud` against the Access application AUD and `iss` against the team domain; whole dependency gated on `CF_ACCESS_ENABLED`
8. Turnstile helper for Phase 2 forms: `antispam.py` `verify_turnstile(token, remote_ip) -> bool` against `/siteverify`, called **before any database write**, identical response on failure as success; `honeypot` helper accepts and silently discards submissions with the hidden field populated

## Tests
- Correct password verifies; incorrect fails with timing-identical response
- Expired, consumed, and over-attempted codes all rejected; new challenge invalidates previous
- Tampered or expired session cookie → 401; all four cookie flags asserted in production config
- 6th login in a minute → 429; 10 failures lock out across process restarts; success clears counter
- CF flag on: request without valid assertion → 403; flag off: app-layer auth unchanged; JWKS fetched once
- Turnstile: valid passes; expired/reused/forged fails; honeypot returns success without persisting

## Acceptance Criteria
- [ ] Password + OTP grants a session; no plaintext password in code, logs, or git history
- [ ] Codes are never logged or returned in any response body
- [ ] Timing does not distinguish failure modes
- [ ] OTP email arrives within seconds; send failure returns a clear error, not a false success
- [ ] Lockout persists across restarts (DB-backed)
- [ ] JWKS cached with TTL, not refetched per request

## Verify
`uv run pytest backend/tests/auth -q && uv run python -m app.cli hash-password --help` (docker Postgres up; Resend recipient verified per TD-M3)

## Commit
`feat(auth): argon2 password, hashed otp via resend, signed session, lockout, access jwt`

## Invariants
- OTP codes: single-use, 5-minute TTL, 5 attempts, stored hashed, never logged or echoed
- `SameSite=Lax` only in development; production is always `Strict`
- Secrets env-only: `ADMIN_PASSWORD_HASH`, `SESSION_SECRET`, `RESEND_API_KEY`, CF Access AUD/team
- Argon2's deliberate slowness makes login a DoS target — the rate limiter is not optional
