# Railway Infra Bootstrap — Session Handoff
**Date:** 2026-08-30  
**Project:** portfolio-sid (Next.js public site + Vite admin SPA + FastAPI backend)  
**Goal:** Move off Cloudflare services (R2, Turnstile, Analytics, Tunnel) → Railway hosting

---

## TL;DR — Current State
| Service | Status | Public URL |
|---|---|---|
| Postgres (`Postgres`) | ✅ Online | internal: `postgres.railway.internal:5432` |
| backend | ✅ Online | `https://backend-production-7a2a.up.railway.app` |
| frontend | ✅ Online | `https://frontend-production-38ac.up.railway.app` |
| cron | ✅ Online | (no public domain) |

**All health checks pass:** backend `/health` + `/api/v1/*` 200, frontend 13/13 SSR routes + SEO assets, cron scheduler runs cleanly. Volume `backend-volume` mounted at `/data` → `/media` serves.

---

## What Was Done (Infra Bootstrap — TD-M2 + TD-M4 + TD-36 partial)

### 1. Services Created (CLI)
```bash
railway add -d postgres -s postgres
railway add -s backend
railway add -s frontend
railway add -s cron
```

### 2. Environment Variables (CLI, `--skip-deploys`)
- **backend:** `DATABASE_URL=${{Postgres.DATABASE_URL}}`, `STORAGE_KIND=local`, `LOCAL_STORAGE_DIR=/data`, `MEDIA_BASE_URL=https://admin.siddhesh-chaudhari.com`, `CF_ACCESS_ENABLED=false`
- **frontend:** `NEXT_PUBLIC_API_BASE_URL=https://backend-production-7a2a.up.railway.app` (bridge, see below), `NEXT_PUBLIC_INDEXABLE=false`
- **cron:** same as backend
- **CORS_ALLOW_ORIGINS** intentionally omitted → app defaults to `[]` (same-origin, invariant #14)

### 3. Volume
```bash
railway service link backend
railway volume -s backend add --mount-path /data   # → backend-volume, Status: Ready
```

### 4. Service Settings (via RAILWAY_TOKEN + GraphQL — CLI `environment edit` does NOT apply these)
- **frontend:** `source.rootDirectory = "/frontend"` (builds from `frontend/`)
- **cron:** `deploy.startCommand = "python -m app.jobs.scheduler"`

### 5. Code Fixes Required to Deploy (all committed)
| Fix | File | Why |
|---|---|---|
| Dockerfile at repo root | `Dockerfile` (moved from `backend/Dockerfile`) | Railway only auto-detects Dockerfile at root; `dockerfilePath` in `railway.toml` is ignored |
| Bind to `$PORT` | `Dockerfile` CMD | Hardcoded 8000 caused edge 502s; Railway proxies to `$PORT` |
| Coerce DB URL to asyncpg | `backend/app/core/config.py` (field_validator `_coerce_asyncpg_driver`) | Railway Postgres emits `postgresql://`; SQLAlchemy async needs `postgresql+asyncpg://` |
| Admin TS error | `admin/src/routes/collections/CollectionsForm.tsx:47` | `cover_key?: string \| null` — build blocker |
| Run alembic on start | `Dockerfile` CMD: `sh -c "uv run alembic upgrade head && uvicorn ..."` | Fresh Railway Postgres has no tables; scheduler + API 500'd on missing relations |

### 6. Verification
- **Backend:** `/health` 200, `/api/v1/certifications` 200 `[]`, `/api/v1/projects` 200 `[]`, `/media/` 404 (mounted), `/` serves Admin SPA
- **Frontend:** `check_ssr.sh --all` → 13/13 PASS; `check_ssr.sh --seo` → all PASS
- **Cron:** logs show `promoted 0 row(s) across 8 model(s); revalidated tags=[]` — no missing-table errors

---

## Critical Decisions & Rationale

1. **Config-as-code (`railway.toml`) is DEPRECATED** — it only holds build/deploy settings; **cannot** set variables, volumes, `rootDirectory`, or `startCommand`. Both toml and `railway environment edit --service-config` are ignored for those fields. Use CLI for env/volumes; GraphQL (or Dashboard) for `rootDirectory`/`startCommand`.

2. **`rootDirectory` cannot be set via CLI** — only Dashboard or GraphQL. We used the provided `RAILWAY_TOKEN` to set it via `serviceInstanceUpdate` mutation.

3. **Deploys via `railway up` (code upload)**, not GitHub App. Bootstrap done via CLI now.

4. **Bridge `NEXT_PUBLIC_API_BASE_URL`** — frontend prerenders pages by fetching the API at build time. The real domain `admin.siddhesh-chaudhari.com` isn't DNS-pointed at Railway yet, so build failed with `ENOTFOUND`. Temporary fix: set to `https://backend-production-7a2a.up.railway.app` (reachable). **Must revert to `https://admin.siddhesh-chaudhari.com` after DNS cutover + redeploy.**

5. **Migrations baked into container start** — `alembic upgrade head` runs before uvicorn on every deploy (idempotent). `env.py:26` feeds alembic the coerced asyncpg URL from `get_settings().database_url`, so it works with the installed asyncpg driver (psycopg2 not installed).

6. **Secrets NOT set** — `SESSION_SECRET`, `ADMIN_PASSWORD_HASH`, `RESEND_API_KEY`, `REVALIDATION_SECRET`, `ADMIN_EMAIL`. Services run without them (admin login + email will fail until set). User will rotate and we redeploy.

7. **Invariants preserved** (from `docs/conventions.md`):
   - #13: `NEXT_PUBLIC_INDEXABLE=false`
   - #14: `CORS_ALLOW_ORIGINS` unset → same-origin
   - #15: No secrets in git/logs

---

## Remaining Tasks (Priority Order)

### A. Secrets (Blocking admin login + email)
```bash
railway variable set SESSION_SECRET --stdin --service backend
railway variable set ADMIN_PASSWORD_HASH --stdin --service backend  # from: uv run python -m app.cli hash-password <pw>
railway variable set RESEND_API_KEY --stdin --service backend
railway variable set REVALIDATION_SECRET --stdin --service backend
railway variable set ADMIN_EMAIL --stdin --service backend
```
Then `railway up --service backend --detach` (and cron/frontend if they consume any).

### B. Host Cutover (Custom Domain + DNS)
1. In Railway Dashboard (or GraphQL): add custom domain `admin.siddhesh-chaudhari.com` to **backend** service.
2. Verify ownership (TXT record) → wait for SSL.
3. At registrar (Cloudflare Domains): update nameservers / CNAME to point `admin.siddhesh-chaudhari.com` → Railway.
4. Once live: set `NEXT_PUBLIC_API_BASE_URL=https://admin.siddhesh-chaudhari.com` on frontend (`railway variable set ... --service frontend`), then `railway up --service frontend --detach`.
5. Verify frontend SSR still passes.

### C. Postgres Backup Policy Drill (TD-36)
- Document exact retention from Railway dashboard → update `docs/conventions.md`.
- Run a from-scratch restore into a scratch DB (see `restore-procedure.md`, create if missing).
- Never overwrite production; target throwaway service.

### D. TD-M6 Deferred
- `dig +short admin.siddhesh-chaudhari.com` → verify points to Railway (after B).

---

## Known Issues / "Not Proper" Concerns (User Flagged)

> **User:** "The current deployment isn't proper in my opinion."

**Possible pain points to investigate next session:**
- **Config-as-code ignored** — we rely on CLI + GraphQL; no declarative IaC. Consider: `railway.toml` is deprecated; maybe adopt a proper IaC tool (Terraform? Railway's own GraphQL API in CI?).
- **Bridge `NEXT_PUBLIC_API_BASE_URL`** — hardcoded Railway URL in production frontend bundle until DNS cutover. Not ideal.
- **Secrets management** — manual `railway variable set --stdin`; no rotation automation.
- **Migrations on every container start** — works but adds ~10-15s to cold start. Could move to a release step if Railway supports it.
- **No healthcheck on cron** — scheduler runs but if it crashes silently, we wouldn't know. Add a `/health` or log heartbeat.
- **Frontend build depends on backend reachability** — coupling at build time. Could switch to dynamic fetching (no SSG for data pages) or ensure backend is always up during frontend deploy.
- **No preview/staging environment** — all deploys to production. Consider Railway preview deploys for PRs.
- **Volume backup strategy** — only Postgres has automated backups; `backend-volume` (uploads) has no backup policy documented.

---

## Files Changed This Session (Key)

| File | Change |
|---|---|
| `Dockerfile` | Root-level, runs alembic + uvicorn on `$PORT` |
| `backend/app/core/config.py` | `_coerce_asyncpg_driver` field_validator |
| `admin/src/routes/collections/CollectionsForm.tsx` | `cover_key?: string \| null` |
| `docs/conventions.md` | Added **Postgres backup policy** section |
| `railway.toml` | `[build] dockerfilePath = "Dockerfile"` |
| `.github/workflows/deploy.yml` | backend/cron from repo root; added cron deploy step |
| `frontend/railway.toml` | `builder="RAILPACK"`, `healthcheckPath="/"` |

---

## Environment Registry (Current)
```bash
# backend (set)
DATABASE_URL=${{Postgres.DATABASE_URL}}
STORAGE_KIND=local
LOCAL_STORAGE_DIR=/data
MEDIA_BASE_URL=https://admin.siddhesh-chaudhari.com
CF_ACCESS_ENABLED=false

# frontend (set — bridge)
NEXT_PUBLIC_API_BASE_URL=https://backend-production-7a2a.up.railway.app
NEXT_PUBLIC_INDEXABLE=false

# cron (set)
DATABASE_URL=${{Postgres.DATABASE_URL}}
STORAGE_KIND=local
LOCAL_STORAGE_DIR=/data
MEDIA_BASE_URL=https://admin.siddhesh-chaudhari.com

# NOT SET (secrets)
SESSION_SECRET
ADMIN_PASSWORD_HASH
RESEND_API_KEY
REVALIDATION_SECRET
ADMIN_EMAIL
```

---

## Useful Commands for Next Session

```bash
# Check service status
railway status
railway service status -s backend
railway service status -s frontend
railway service status -s cron

# View logs
railway logs --service backend --lines 50
railway logs --service frontend --lines 50
railway logs --service cron --lines 50

# Set secrets (example)
railway variable set SESSION_SECRET --stdin --service backend

# Redeploy
railway up --service backend --detach
railway up --service frontend --detach
railway up --service cron --detach

# Verify frontend SSR
bash scripts/check_ssr.sh --all https://frontend-production-38ac.up.railway.app
bash scripts/check_ssr.sh --seo  https://frontend-production-38ac.up.railway.app

# GraphQL (if needed)
TOKEN=<RAILWAY_TOKEN>
curl -s https://backboard.railway.app/graphql/v2 \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"query":"mutation { serviceInstanceUpdate(serviceId:\"0193fd03-ff6c-4022-83fb-df4b3364ef82\", environmentId:\"09b974a1-c963-4e29-bdcb-1d27abe887e2\", input: { rootDirectory: \"/frontend\" }) }"}'
```

---

## Next Session Plan (User Intent)
1. **Plan features** — decide on IaC approach, secret rotation, preview envs, etc.
2. **Finish remaining tasks** — secrets, host cutover, backup drill.
3. **Address "not proper" deployment concerns** — refactor to a cleaner, more maintainable setup.

---

## Git State
- **Clean commits** on `main` (removal, infra x3, fix backend, fix admin, doc backup).
- **Working tree:** restored stashed unrelated work (auth router, admin/api.d.ts, TD-14, react-doctor, handoff docs) — **uncommitted**, ready for user to continue.
- **Stash dropped** (`infra-bootstrap-unrelated` resolved).

---

## Context for Next Agent
- Railway project: `awake-success` (ID `5edae34e-b3aa-4240-8410-f54d2d6b14d4`), env `production` (ID `09b974a1-c963-4e29-bdcb-1d27abe887e2`)
- Postgres service name is **`Postgres` (capital P)** — reference as `${{Postgres.DATABASE_URL}}`
- `railway.toml` is minimal; real config lives in CLI-set env + GraphQL-set service settings
- `RAILWAY_TOKEN` (if reused): `c5e95764-d98c-4551-a03b-b23f69e36ce0` — rotate after use
- All invariants from `docs/conventions.md` are satisfied except those requiring secrets/DNS