# Design — portfolio-sid-v2 Clean Railway Deployment

**Date:** 2026-09-02 · **Status:** APPROVED (user, 2026-09-02)
**Supersedes in part:** `docs/handoff/HANDOFF-2026-08-31-CLEAN-REBUILD.md` (design refined here; runbook stays authoritative for command details)
**Code base:** `main` @ `595b57e` + 3 small commits from this effort (see §4)

Old project `awake-success` is **already deleted** — this is a from-scratch build, not a migration.
Nothing is harvested from the old project. All secrets come from the user's local `backend/.env`
(gitignored) or are freshly generated.

---

## 1. Architecture

```
Cloudflare (registrar + DNS only — no services, no R2)
  siddhesh-chaudhari.com        CNAME → frontend-production-XXXX.up.railway.app
  admin.siddhesh-chaudhari.com  CNAME → admin-production-XXXX.up.railway.app

Railway project "portfolio-sid-v2" / production
                                 ┌──────────────────────────────────────────┐
  PUBLIC (custom + generated)    │  frontend  ─rewrites /api,/media─┐        │
                                 │  admin     ─nginx proxies /api,  │        │
                                 │              /media,/health ────┼───┐    │
                                 └─────────────────────────────────┼───┼────┘
  PRIVATE (no public domain)     ┌─────────────────────────────────┼───┼────┐
                                 │  backend  :8080 (volume /data)◄─┼───┘    │
                                 │  cron     */5 scheduler ◄───────┘        │
                                 │  pgbouncer :6432 (scram, transaction)    │
                                 │  Postgres  :5432 (Railway plugin)        │
                                 └──────────────────────────────────────────┘

Data path: backend/cron → pgbouncer.railway.internal:6432 → postgres.railway.internal:5432
```

Same topology as local `docker-compose.yml` (postgres + pgbouncer sidecar on 6432) — prod mirrors
local, per user instruction. Optimizations happen in code/tuning, not topology.

## 2. Services & builds

| Service | Exposure | Build | Start |
|---|---|---|---|
| frontend | public | Railpack, rootDirectory `/frontend` | `npm run start` (`next start`, NOT standalone) |
| admin | public | `admin/Dockerfile`, rootDirectory `admin` | nginx with dynamic resolver (self-heals across backend redeploys) |
| backend | private only | `/Dockerfile` (repo root) | `alembic upgrade head && uvicorn :8080` |
| cron | private only | same image as backend | `python -m app.jobs.scheduler` (cron `*/5 * * * *`) |
| pgbouncer | private only | image `edoburu/pgbouncer:1.22.1-p0` | listens :6432 |
| Postgres | private only | Railway plugin — NEVER repo-connected | :5432 |

**Cron purpose (confirmed with user):** promotes content with `status=scheduled` and
`publish_at <= now()` to published, prunes crawler hits older than 90 days, and revalidates
affected frontend cache tags. Runs one pass per invocation and exits (perfect fit for the
Railway cron service type — billed per run, isolated from backend crashes).

**Storage:** Railway Volume `/data` on backend (`STORAGE_KIND=local`, `LOCAL_STORAGE_DIR=/data`).
**No R2 in production at all** — R2_* vars are dev-only MinIO config; nothing cloud-storage
related is created or touched in this deployment.

## 3. Env inventory

Secrets source: local `backend/.env` (gitignored). Nothing secret enters git/logs/chat-echoes.

### backend
| Var | Value source |
|---|---|
| `ENVIRONMENT` | `production` |
| `DATABASE_URL` | `postgresql+asyncpg://postgres:<NEW_DB_PW>@pgbouncer.railway.internal:6432/railway` (new plugin password) |
| `PGBOUNCER_ENABLED` | `true` (disables both asyncpg caches in `build_engine`) |
| `DATABASE_POOL_SIZE` / `DATABASE_MAX_OVERFLOW` | `10` / `5` |
| `STORAGE_KIND` / `LOCAL_STORAGE_DIR` | `local` / `/data` |
| `MEDIA_BASE_URL` | `https://admin.siddhesh-chaudhari.com` |
| `SESSION_SECRET` | fresh `openssl rand -hex 32` |
| `ADMIN_PASSWORD_HASH` | hash of NEW random password (user sees it once, P3) |
| `ADMIN_EMAIL` | from local `.env` |
| `RESEND_API_KEY` | from local `.env` (user instruction) |
| `RESEND_FROM` | `onboarding@resend.dev` (Resend default) |
| `REVALIDATION_SECRET` | fresh `openssl rand -hex 32` (same value across backend/cron/frontend) |
| `CORS_ALLOW_ORIGINS` | empty (invariant #14) |
| `CF_ACCESS_ENABLED` | `false` |
| `NEXT_PUBLIC_BASE_URL` | `https://siddhesh-chaudhari.com` — **gap fix:** revalidation webhook posts here; handoff omitted it (default = localhost:3000 → every publish silently fails) |

### cron
Same core as backend: `ENVIRONMENT`, `DATABASE_URL` (via pgbouncer), `PGBOUNCER_ENABLED`,
`REVALIDATION_SECRET`, `STORAGE_KIND`, `LOCAL_STORAGE_DIR`, `MEDIA_BASE_URL`, `NEXT_PUBLIC_BASE_URL`.

### frontend
| Var | Value source |
|---|---|
| `BACKEND_URL` | `http://backend.railway.internal:8080` (SSR fetches + rewrites) |
| `NEXT_PUBLIC_INDEXABLE` | `false` (invariant #13) |
| `REVALIDATION_SECRET` | same fresh value as backend |
| `NEXT_PUBLIC_BASE_URL` | `https://siddhesh-chaudhari.com` — **gap fix:** robots/sitemap/llms.txt/contact jsonld would emit localhost:3000 otherwise |
| `PUBLIC_API_PROXY` | `https://<new-admin-host>.up.railway.app` — **new env var** (§4.2) |
| `NEXT_PUBLIC_API_BASE_URL` | unset/empty (browser uses relative `/api` via rewrites; backend is private) |
| `NEXT_PUBLIC_UMAMI_*` | deferred |

### admin
None (pure nginx proxy).

### pgbouncer
`DATABASE_URL=postgresql://postgres:<NEW_DB_PW>@postgres.railway.internal:5432/railway`,
`POOL_MODE=transaction`, `AUTH_TYPE=scram-sha-256`, `MAX_CLIENT_CONN=100`, `DEFAULT_POOL_SIZE=20`,
`RESERVE_POOL_SIZE=5`, `LISTEN_ADDR=*`, `LISTEN_PORT=6432`, `ADMIN_USERS=postgres`,
`IGNORE_STARTUP_PARAMETERS=extra_float_digits`.

### GitHub secrets
`RAILWAY_TOKEN` — value taken from the user's local `.env`, stored ONLY as the `production`
environment secret. Used only by the CI fallback workflow. **Scope caveat:** the stored token
may be account-wide or scoped to the deleted project. P6 first verifies it can act on
`portfolio-sid-v2` (`railway project list` with the token); if it cannot, the user creates a
new token in the Railway dashboard (flagged user action).

## 4. Code changes (3 small commits, before any Railway mutation)

1. `fix(backend): disable asyncpg statement cache for pgbouncer` — commit existing working-tree
   changes: `statement_cache_size: 0` added alongside `prepared_statement_cache_size: 0` in
   `build_engine` connect_args + test update + `AUTH_TYPE=scram-sha-256` in docker-compose.
2. `fix(frontend): make build-time api proxy configurable` — `frontend/lib/api.ts`:
   `const PUBLIC_PROXY = process.env.PUBLIC_API_PROXY ?? ""` replacing the hardcoded
   `https://admin-production-9cc7.up.railway.app` (dead — old project deleted; frontend
   build-time prerender needs a live public proxy). Set `PUBLIC_API_PROXY` env on the frontend
   service to the new admin generated hostname (admin pre-deployed in P3 so the target is live
   before the frontend's first build).
3. `chore: ignore local storage dir` + `docs(handoff):` commit of handoff/design/plan docs.

## 5. Phases (gates: record PASS/FAIL, never advance on FAIL)

- **P0 Plan** — this doc + PLAN.md, user checkpoint. *(nothing on Railway before approval)*
- **P1 Skeleton** — create `portfolio-sid-v2` (user may need to pick paid plan: volumes, Postgres
  plugin, cron), `railway add` Postgres plugin + backend/cron/frontend/admin + pgbouncer image
  service, attach `backend-volume` `/data` to backend. Record all service/env IDs.
  **Gate:** `railway service list` shows 6 services.
- **P2 Data layer** — pgbouncer env (§3) + deploy.
  **Gate:** logs show `listening on 0.0.0.0:6432`, `PgBouncer 1.22.1 … process up`.
- **P3 Backend (+ admin pre-deploy)** — backend env + `railway up --service backend`; also
  `railway up --service admin` so `PUBLIC_API_PROXY` has a live target.
  **Gates:** alembic clean single head, `Uvicorn running on http://0.0.0.0:8080`, zero
  `DuplicatePreparedStatementError`, zero `KeyError` in alembic, no public domain on backend,
  admin generated URL returns 200.
- **P4 Cron** — cron env + instance config (`cronSchedule=*/5 * * * *`,
  `startCommand=python -m app.jobs.scheduler`) + `railway up --service cron`.
  **Gate:** within 5 min: `scheduler: promoted 0 row(s) across 8 model(s)` with no asyncpg errors.
- **P5 GitHub native triggers** — **user action:** re-authorize Railway GitHub App on the repo in
  the dashboard. Then `railway service source connect` for backend/cron/frontend/admin
  (NEVER Postgres), set per-service builder/dockerfilePath/rootDirectory, push trigger commit
  (includes the handoff doc).
  **Gate:** all 4 deployments SUCCESS from the push with correct build meta.
- **P6 CI fallback** — separate task: rewrite `.github/workflows/deploy.yml` (current file is a
  dry-run stub with no admin job, no project targeting, no health gate). Set `RAILWAY_TOKEN` in
  gh `production` environment from the user's local `.env`; **first verify the token can act on
  the new project** (if project-scoped to the deleted project, user creates a new token — flag
  it).
  **Gate:** manual dispatch deploys all 4 to `portfolio-sid-v2`, health step green, no secrets in
  logs.
- **P7 Frontends + proxies** — admin: SPA 200, `/api/v1/health` 200, `/media` proxy works;
  frontend: `scripts/check_ssr.sh --all` 13/13, `/api/v1/health` 200 via rewrites, backend direct
  = private; kill-test: `railway service restart --service backend --yes` → admin `/api/v1/health`
  recovers without admin restart (dynamic resolver proof).
- **P8 Content seed** — run `seed_resumes.py` **inside the backend container** via
  `railway ssh --service backend` (tar the 6 local `resumes/*.pdf` in; `railway run` executes
  locally and cannot write the volume). Fallbacks if ssh/stdin unsupported: deploy-time bootstrap
  or admin-API resume rows + PDF upload path (decide at execution, systematic-debugging).
  **Gate:** `/api/v1/resumes` = 6, `/api/v1/timeline` = 14, overview = 6, PDF downloads 200.
- **P9 Custom domains + docs** — `railway domain` both hostnames; **user action:** update
  Cloudflare CNAMEs to new targets. Verify dig/curl/SSL. Update docs:
  `conventions.md` (pgbouncer section is stale — claims "no sidecar service is deployed"; record
  dedicated service + `1.22.1-p0`), `env-vars-registry.md` (pgbouncer vars, `PGBOUNCER_ENABLED`,
  `NEXT_PUBLIC_BASE_URL`, `PUBLIC_API_PROXY`), `LOCAL.md` (prod pgbouncer note). `graphify update .`.
- **P10 Cutover** — re-run full DoD on the new project; old project already deleted (nothing to
  tear down); restore drill per `restore-procedure.md` §3 (scratch docker Postgres from a Railway
  backup); record result.

## 6. Execution model

- Railway mutations strictly sequential per phase; sub-agents pass explicit
  `--project/--environment/--service` flags (CLI link state is global, not per-shell).
- Parallel sub-agents for independent work within a phase: gate verification, log greps,
  doc updates, local code commits.
- Failing service → `systematic-debugging`; deepseek-v4-flash subagents, ≤3 retries;
  `verification-before-completion` before every PASS claim.
- Deploys always from `main` HEAD (never intermediate commits `2bd928f..7527153` — broken
  alembic chain).

## 7. User actions checklist (flag each when reached)

1. P1: pick/confirm a paid Railway plan (volume + Postgres + cron require it)
2. P3: receive the generated admin password (shown once, store it)
3. P5: re-authorize the Railway GitHub App on the repo in the dashboard
4. P6: approve/confirm `RAILWAY_TOKEN` rotation in gh `production` environment
5. P9: update the two Cloudflare CNAMEs to the new Railway targets

## 8. Decisions log

| # | Decision | By | Rationale |
|---|---|---|---|
| D1 | Separate Railway cron service | user | Scheduled publishing needed; run-once scheduler fits Railway cron type |
| D2 | Env-ize `PUBLIC_API_PROXY` | user | No hardcoded dead hostname; new var set to new admin host |
| D3 | Admin password: generate fresh, show once | user | Old hash unrecoverable (old project deleted) |
| D4 | `RESEND_API_KEY` + `RAILWAY_TOKEN` from local `.env` | user | Avoid dashboard round-trips; values already local |
| D5 | `SESSION_SECRET`/`REVALIDATION_SECRET` regenerated fresh | agent (noted) | Old values unrecoverable; fresh prod values safer than reusing dev ones |
| D6 | No R2 anywhere in prod | user | Railway volume + managed Postgres only |
| D7 | Resend defaults (`RESEND_FROM=onboarding@resend.dev`) | user | Keep until SPF/DKIM/DMARC task |
| D8 | `NEXT_PUBLIC_BASE_URL` added to backend/cron/frontend env | agent (noted) | Gap: revalidation + robots/sitemap/llms.txt would target localhost:3000 |
| D9 | Seed runs in-container via `railway ssh` | agent (noted) | `railway run` is local-only; PDFs must land on `/data` volume |
| D10 | Admin pre-deployed in P3 (before frontend's first build) | agent (noted) | `PUBLIC_API_PROXY` must be live when frontend prerenders |

## 9. Risks & mitigations

- **Frontend first-build chicken-and-egg** (prerender needs live admin proxy) → admin pre-deploy P3 (D10).
- **`railway ssh` stdin/file-transfer limits** → fallback paths documented in P8; verify mechanism before the real run.
- **GitHub App re-auth fails again** → P5 blocked; CI-only fallback (P6) becomes the deploy path (already designed).
- **Railway plan/billing prompts** are user-side and interactive → user actions P1; CLI flags supplied for everything else.
- **Postgres "Deploy failed" badge** → ensure plugin never repo-connected; redeploy last SUCCESS if seen.
- **Secret leakage** → values only via local `.env` reads into Railway/gh; never echoed, never committed.
