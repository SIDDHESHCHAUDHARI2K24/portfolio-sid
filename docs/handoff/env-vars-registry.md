# Env Vars Registry

References only — **no secret values in this file**. `STITCH_API_KEY` lives ONLY in the local gitignored `.env` (never Railway, never git).

> **Revised 2026-08-28:** Cloudflare *services* (R2, Turnstile, Web Analytics, Tunnel, Access) are removed.
> The domain `siddhesh-chaudhari.com` stays at Cloudflare as **registrar + DNS only** — so Resend
> SPF/DKIM/DMARC and the admin/media custom-domain records are still Cloudflare DNS records.
> `R2_*` env var names are retained for config compatibility but now point at **MinIO in local dev**
> (S3-compatible). Production storage is the backend's local disk on a **Railway Volume**
> (`STORAGE_KIND=local`), served at `/media`.

## Backend service (Railway)

| Var | Purpose | Set by | Consumed by |
|---|---|---|---|
| `DATABASE_URL` | Postgres 16 connection — use Railway **internal** URL (no egress) | TD-M4 | TD-07, TD-16+ (all models/queries) |
| `STORAGE_KIND` | `local` (prod, Railway Volume) or `s3` (local dev, MinIO) | TD-M4 / code | `storage.py` factory |
| `LOCAL_STORAGE_DIR` | Disk path for local storage; mounted Railway Volume in prod (e.g. `/data`) | TD-M4 | `storage.py` `LocalDiskStorage` |
| `MEDIA_BASE_URL` | Absolute base for `/media` URLs so the separate frontend can load them, e.g. `https://admin.siddhesh-chaudhari.com` | TD-M4 | `storage.py` `LocalDiskStorage.get_url` |
| `R2_ENDPOINT` | **Dev only** — MinIO S3 endpoint `http://localhost:9000` (unused in prod `local` mode) | local dev | `storage.py` (s3 path) |
| `R2_ACCESS_KEY_ID` | **Dev only** — MinIO access key | local dev | `storage.py` (s3 path) |
| `R2_SECRET_ACCESS_KEY` | **Dev only** — MinIO secret key | local dev | `storage.py` (s3 path) |
| `R2_BUCKET` | `portfolio-media` (MinIO dev bucket) | local dev | `storage.py` (s3 path) |
| `R2_PUBLIC_BASE_URL` | **Dev only** — `http://localhost:9000/portfolio-media` (unused in prod) | local dev | `storage.py` (s3 path) |
| `RESEND_API_KEY` | Sending API key (dashboard → API Keys) | TD-M3 → wired TD-M4 | TD-17 OTP email, TD-29 form notifications |
| `ADMIN_EMAIL` | Sole OTP / notification recipient | TD-M4 | TD-17 |
| `SESSION_SECRET` | `itsdangerous` signed-cookie key (generate: `openssl rand -hex 32`) | TD-M4 | TD-17 session cookie |
| `ADMIN_PASSWORD_HASH` | Argon2id hash from `uv run python -m app.cli hash-password` — hash only, never the password | TD-M4 (after TD-17 CLI exists) | TD-17 login |
| `CORS_ALLOW_ORIGINS` | **Empty in production — deliberate.** Admin+API same-origin via single hostname. Permissive value here is a misconfiguration that never announces itself | TD-M4 | TD-03 app factory (dev: `http://localhost:5173`) |
| `CF_ACCESS_ENABLED` | **Permanently `false`** — Cloudflare Access service dropped; app-layer auth (TD-17) carries authn | TD-M6 (set false) | TD-17 Access dependency |
| `GLITCHTIP_DSN` | **GlitchTip** (open-source Sentry-compatible) DSN for error tracking on both backend + frontend. Set to a GlitchTip instance DSN on Railway. | TD-36 | TD-36 `app/core/glitchtip.py`, frontend sentry configs |
| `NEXT_PUBLIC_GLITCHTIP_DSN` | Client-side GlitchTip DSN (frontend only). Both DSN vars skip init when unset, so local dev needs neither. | TD-36 | `frontend/sentry.client.config.ts` |
| `REVALIDATION_SECRET` | Shared secret for the Next.js revalidate route; backend sends it in the webhook header | TD-M4 | TD-19 (sender side) |
| `NEXT_PUBLIC_BASE_URL` | Canonical public site URL the backend/cron POST revalidations to (`https://siddhesh-chaudhari.com` in prod). Defaults to `http://localhost:3000` — an unset var silently breaks every revalidation | portfolio-sid-v2 | `revalidation.py` |
| `PGBOUNCER_ENABLED` | `true` in prod — makes `database.py` disable both asyncpg statement caches (unsafe under pgbouncer transaction pooling) | portfolio-sid-v2 | `database.py::pgbouncer_connect_args`, `alembic/env.py` |

> `CF_ACCESS_TEAM_DOMAIN` and `CF_ACCESS_AUD` are **removed** (Access service dropped).
> `SENTRY_DSN` removed in favour of GlitchTip. `TURNSTILE_*` removed (replaced by honeypot + rate-limit).

## Frontend service (Railway)

| Var | Purpose | Set by | Consumed by |
|---|---|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | Backend URL the browser calls (backend public Railway URL / admin custom domain); same-origin via single hostname after cutover. Also the host for `/media` images | TD-M4 | TD-21 fetch layer; `next.config.ts` `images.remotePatterns` |
| `NEXT_PUBLIC_INDEXABLE` | `false` until launch — emits `noindex` so Railway hostnames are never indexed. Flip to `true` only in TD-36 after domain verified | TD-M4 | TD-04; flipped TD-36 |
| `REVALIDATION_SECRET` | Lives where the revalidate route reads it — **frontend build env**. Must equal the backend value | TD-M4 | TD-19 (route handler) |
| `NEXT_PUBLIC_UMAMI_SRC` | Self-hosted Umami script URL (e.g. `https://umami.yourhost/script.js`); beacon no-ops when unset | TD-36 / prep | `frontend/app/layout.tsx` |
| `NEXT_PUBLIC_UMAMI_WEBSITE_ID` | Umami website ID for this site; no-ops when unset | TD-36 / prep | `frontend/app/layout.tsx` |
| `BACKEND_URL` | `http://${{backend.RAILWAY_PRIVATE_DOMAIN}}:8080` — SSR fetches + Next rewrites target (Railway variable reference) | portfolio-sid-v2 | `next.config.ts` rewrites, `lib/api.ts` `getServerBase` |
| `PUBLIC_API_PROXY` | Public admin origin used as the build-time prerender fallback when `*.railway.internal` is unresolvable (`https://admin-production-d152.up.railway.app`). Read server-side only | portfolio-sid-v2 | `lib/api.ts` `getFallbackServerBase` |
| `NEXT_PUBLIC_BASE_URL` | Canonical site URL for `robots.ts`/`sitemap.ts`/`llms.txt`/JSON-LD (`https://siddhesh-chaudhari.com`) — never the generated hostname | portfolio-sid-v2 | robots/sitemap/llms.txt/contact/jsonld |
| `NEXT_PUBLIC_API_BASE_URL` | **Unset in prod** — browser uses relative `/api` via rewrites (backend is private) | — | `lib/api.ts` client path |

> `TURNSTILE_SITE_KEY` and `NEXT_PUBLIC_CF_BEACON_TOKEN` removed (Cloudflare dropped).

## Cron service (Railway)

Reuses the backend image with a different start command — wire the **same env as backend**, at minimum `DATABASE_URL` (internal, via pgbouncer), `REVALIDATION_SECRET`, `STORAGE_KIND`, `LOCAL_STORAGE_DIR`, `MEDIA_BASE_URL`, `NEXT_PUBLIC_BASE_URL` (revalidation webhook target). Set in TD-M4; consumed by TD-19 scheduler. Runs one pass per `*/5` tick via `startCommand=python -m app.jobs.scheduler`; standalone (no backend API calls — see `DESIGN.md` D11).

## PgBouncer service (Railway, private)

`edoburu/pgbouncer:1.22.1-p0` — the ONLY service holding the Postgres URL.

| Var | Value / purpose |
|---|---|
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` (Railway reference to the Postgres plugin) |
| `POOL_MODE` | `transaction` |
| `AUTH_TYPE` | `scram-sha-256` (image derives SCRAM from the plaintext password; `md5`/`any` fail) |
| `MAX_CLIENT_CONN` / `DEFAULT_POOL_SIZE` / `RESERVE_POOL_SIZE` | `100` / `20` / `5` |
| `LISTEN_ADDR` / `LISTEN_PORT` | `*` / `6432` |
| `ADMIN_USERS` | `postgres` |
| `IGNORE_STARTUP_PARAMETERS` | `extra_float_digits` |
| `SERVER_RESET_QUERY` | `DISCARD ALL` — deallocates prepared statements on pooled server connections between clients |

## Admin service (Railway, public)

| Var | Value / purpose |
|---|---|
| `BACKEND_UPSTREAM` | `http://${{backend.RAILWAY_PRIVATE_DOMAIN}}:8080` — nginx upstream, templated into `admin/nginx.conf` at container start (`admin/Dockerfile` CMD defaults to `http://backend.railway.internal:8080` when unset) |

## Railway variable references

Cross-service env values use `${{Service.VAR}}` references (dashboard dependency edges + auto-updates). Gotcha: the Railway **CLI and GraphQL API resolve references at write time** — references must be picked in the dashboard variable editor; the CLI stores the resolved literal. Literal-only by design: `NEXT_PUBLIC_BASE_URL`, `MEDIA_BASE_URL` (canonical custom domains), secrets.

## GitHub environment secrets

| Var | Purpose | Set by | Consumed by |
|---|---|---|---|
| `RAILWAY_TOKEN` | Project token for CLI deploys. **Environment secret in `production` only** (with required reviewer, branch rule `main`) — never a repository secret | TD-M5 | TD-15 deploy workflow |

## Local `.env` (gitignored — mirrors `backend/.env.example`)

| Var | Dev value shape | Notes |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://...@localhost:5432/portfolio` | Docker Compose Postgres (TD-06) |
| `STORAGE_KIND` | `s3` | Local dev uses MinIO (S3-compatible) |
| `R2_ENDPOINT` | `http://localhost:9000` | MinIO (TD-06) |
| `R2_ACCESS_KEY_ID` / `R2_SECRET_ACCESS_KEY` | MinIO credentials from compose | Same S3 API as prod |
| `R2_BUCKET` | `portfolio-media` | Created by `createbuckets` init container |
| `R2_PUBLIC_BASE_URL` | `http://localhost:9000/portfolio-media` | |
| `SESSION_SECRET` | Any random dev string | Never reuse prod value |
| `ADMIN_EMAIL`, `ADMIN_PASSWORD_HASH` | Dev values | Hash via CLI once it exists |
| `CORS_ALLOW_ORIGINS` | `http://localhost:5173` | Dev-only divergence |
| `CF_ACCESS_ENABLED` | `false` | Access service dropped |
| `STITCH_API_KEY` | Stitch key | **Local only. Never Railway, never git.** `.mcp.json` references `${STITCH_API_KEY}` (TD-10) |

## Dashboard-held values (not env vars)

| Value | Where | Set by | Consumed by |
|---|---|---|---|
| Zone: `siddhesh-chaudhari.com` | Cloudflare dashboard → zone (registrar + DNS only) | TD-M1 | Everything DNS |
| Umami instance (self-hosted) | Stand up in "prepare for hosting" | TD-36 prep | `NEXT_PUBLIC_UMAMI_SRC` / `_WEBSITE_ID` |
| Resend verified-domain status + API key | Resend dashboard | TD-M3 | Backend `RESEND_API_KEY` |
| Railway Postgres backup policy | Railway → Postgres → Settings | TD-M4 | restore-procedure.md (gap G12) |
