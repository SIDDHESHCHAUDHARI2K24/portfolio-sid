# Env Vars Registry

References only — **no secret values in this file**. `STITCH_API_KEY` lives ONLY in the local gitignored `.env` (never Railway, never git).

## Backend service (Railway)

| Var | Purpose | Set by | Consumed by |
|---|---|---|---|
| `DATABASE_URL` | Postgres 16 connection — use Railway **internal** URL (no egress) | TD-M4 | TD-07, TD-16+ (all models/queries) |
| `R2_ENDPOINT` | S3 endpoint `https://<account-id>.r2.cloudflarestorage.com` | TD-M2 → wired TD-M4 | TD-08 StorageAdapter |
| `R2_ACCESS_KEY_ID` | S3-compatible access key (bucket-scoped token) | TD-M2 → wired TD-M4 | TD-08 |
| `R2_SECRET_ACCESS_KEY` | Secret half of the key pair | TD-M2 → wired TD-M4 | TD-08 |
| `R2_BUCKET` | `portfolio-media` | TD-M2 → wired TD-M4 | TD-08; TD-25/26/28/29 uploads |
| `R2_PUBLIC_BASE_URL` | `https://media.siddhesh-chaudhari.com` (custom domain, not r2.dev) | TD-M2 → wired TD-M4 | TD-08 `get_url`; frontend `images.remotePatterns` |
| `RESEND_API_KEY` | Sending API key (dashboard → API Keys) | TD-M3 → wired TD-M4 | TD-17 OTP email, TD-29 form notifications |
| `ADMIN_EMAIL` | Sole OTP / notification recipient | TD-M4 | TD-17 |
| `TURNSTILE_SECRET_KEY` | Server-side `/siteverify` key | TD-M2 → wired TD-M4 | TD-17 antispam helper, TD-29 forms |
| `SESSION_SECRET` | `itsdangerous` signed-cookie key (generate: `openssl rand -hex 32`) | TD-M4 | TD-17 session cookie |
| `ADMIN_PASSWORD_HASH` | Argon2id hash from `uv run python -m app.cli hash-password` — hash only, never the password | TD-M4 (after TD-17 CLI exists) | TD-17 login |
| `CORS_ALLOW_ORIGINS` | **Empty in production — deliberate.** Admin+API same-origin via tunnel. Permissive value here is a misconfiguration that never announces itself | TD-M4 | TD-03 app factory (dev: `http://localhost:5173`) |
| `CF_ACCESS_ENABLED` | Gates Access JWT verification; `false` until TD-36 cutover, rollback path if Access locks out | TD-M6 | TD-17 Access dependency |
| `CF_ACCESS_TEAM_DOMAIN` | `<team>.cloudflareaccess.com` (JWKS at `/cdn-cgi/access/certs`) | TD-M6 | TD-17 |
| `CF_ACCESS_AUD` | Access application AUD tag | TD-M6 | TD-17 |
| `SENTRY_DSN` | Backend error tracking (gap G11) | TD-36 | TD-36 |
| `GLITCHTIP_DSN` | **GlitchTip** (open-source Sentry-compatible) DSN for error tracking on both backend + frontend. Set to a GlitchTip instance DSN on Railway. | TD-36 | TD-36 new `app/core/glitchtip.py`, frontend sentry configs |
| `NEXT_PUBLIC_GLITCHTIP_DSN` | Client-side GlitchTip DSN (frontend only). Both DSN vars skip init when unset, so local dev needs neither. | TD-36 | `frontend/sentry.client.config.ts` |
| `NEXT_PUBLIC_CF_BEACON_TOKEN` | Cloudflare Web Analytics beacon token (TD-33). Beacon script no-ops without it. | TD-M2 | `frontend/app/layout.tsx` |
| `REVALIDATION_SECRET` | Shared secret for the Next.js revalidate route; backend sends it in the webhook header | TD-M4 | TD-19 (sender side) |

## Frontend service (Railway)

| Var | Purpose | Set by | Consumed by |
|---|---|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | Backend URL the browser calls (backend public Railway URL; same-origin via tunnel after cutover) | TD-M4 | TD-21 fetch layer |
| `NEXT_PUBLIC_INDEXABLE` | `false` until launch — emits `noindex` so Railway hostnames are never indexed. Flip to `true` only in TD-36 after domain verified | TD-M4 | TD-04; flipped TD-36 |
| `REVALIDATION_SECRET` | Lives where the revalidate route reads it — **frontend build env**. Must equal the backend value | TD-M4 | TD-19 (route handler) |
| `TURNSTILE_SITE_KEY` | Public widget key (safe to expose) | TD-M2 → wired TD-M4 | TD-29 contact/dealflow forms |
| `SENTRY_DSN` | Frontend error tracking | TD-36 | TD-36 |

## Cron service (Railway)

Reuses the backend image with a different start command — wire the **same env as backend**, at minimum `DATABASE_URL` (internal) and `REVALIDATION_SECRET`. Set in TD-M4; consumed by TD-19 scheduler.

## Tunnel service (Railway)

| Var | Purpose | Set by | Consumed by |
|---|---|---|---|
| `CLOUDFLARE_TUNNEL_TOKEN` | Named-tunnel token from Zero Trust dashboard; runs `cloudflared tunnel run` | TD-M6 | TD-M6 |

## GitHub environment secrets

| Var | Purpose | Set by | Consumed by |
|---|---|---|---|
| `RAILWAY_TOKEN` | Project token for CLI deploys. **Environment secret in `production` only** (with required reviewer, branch rule `main`) — never a repository secret | TD-M5 | TD-15 deploy workflow |

## Local `.env` (gitignored — mirrors `backend/.env.example`)

| Var | Dev value shape | Notes |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://...@localhost:5432/portfolio` | Docker Compose Postgres (TD-06) |
| `R2_ENDPOINT` | `http://localhost:9000` | MinIO (TD-06) |
| `R2_ACCESS_KEY_ID` / `R2_SECRET_ACCESS_KEY` | MinIO credentials from compose | Same S3 API as prod |
| `R2_BUCKET` | `portfolio-media` | Created by `createbuckets` init container |
| `R2_PUBLIC_BASE_URL` | `http://localhost:9000/portfolio-media` | |
| `SESSION_SECRET` | Any random dev string | Never reuse prod value |
| `ADMIN_EMAIL`, `ADMIN_PASSWORD_HASH` | Dev values | Hash via CLI once it exists |
| `CORS_ALLOW_ORIGINS` | `http://localhost:5173` | Dev-only divergence |
| `CF_ACCESS_ENABLED` | `false` | |
| `STITCH_API_KEY` | Stitch key | **Local only. Never Railway, never git.** `.mcp.json` references `${STITCH_API_KEY}` (TD-10) |

## Dashboard-held values (not env vars)

| Value | Where | Set by | Consumed by |
|---|---|---|---|
| Zone: `siddhesh-chaudhari.com` | Cloudflare dashboard → zone | TD-M1 | Everything DNS |
| Web Analytics beacon token | Cloudflare → Analytics & Logs → Web Analytics | TD-M2 | TD-33 beacon in `app/layout.tsx` |
| Turnstile site key (public copy) | Cloudflare → Turnstile | TD-M2 | Frontend `TURNSTILE_SITE_KEY` |
| Resend verified-domain status + API key | Resend dashboard | TD-M3 | Backend `RESEND_API_KEY` |
| Railway Postgres backup policy | Railway → Postgres → Settings | TD-M4 | restore-procedure.md (gap G12) |
