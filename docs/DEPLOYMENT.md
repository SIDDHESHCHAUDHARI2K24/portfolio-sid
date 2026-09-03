# DEPLOYMENT.md — Architecture, Runbook & Troubleshooting

Deployment bible for the portfolio stack on Railway (`portfolio-sid-v2`). Read this first for any deployment issue. Companion docs: `docs/specs/portfolio-sid-v2-deployment/*`, `docs/conventions.md`, `docs/handoff/env-vars-registry.md`, `docs/handoff/restore-procedure.md`.

## 1. Architecture

```
Cloudflare (registrar + DNS only)
  siddhesh-chaudhari.com        → frontend (Railway custom domain)
  admin.siddhesh-chaudhari.com  → admin    (Railway custom domain)

Railway project portfolio-sid-v2 / production   (project e0f5e770-6a95-41aa-99e4-3be94884d6ca)
  PUBLIC   frontend   Next.js SSR/ISR · rewrites /api,/media → backend (private)
  PUBLIC   admin      nginx SPA · proxies /api,/media,/health → backend:8080
  PRIVATE  backend    FastAPI :8080 · alembic at start · volume /data
  PRIVATE  cron       */5 · python -m app.jobs.scheduler (standalone — no backend calls)
  PRIVATE  pgbouncer  edoburu/pgbouncer:1.22.1-p0 · :6432
  PRIVATE  Postgres   Railway plugin · :5432 (Postgres 18) — NEVER repo-connected

  Data path: backend/cron → pgbouncer.railway.internal:6432 → postgres.railway.internal:5432
```

Service IDs: see `docs/specs/portfolio-sid-v2-deployment/POST-DEPLOYMENT.md`.

## 2. Build matrix

| Service | Builder | dockerfilePath | rootDirectory | startCommand |
|---|---|---|---|---|
| backend | DOCKERFILE | `/Dockerfile` | — | (image CMD: alembic upgrade head && uvicorn :8080) |
| cron | DOCKERFILE | `/Dockerfile` | — | `python -m app.jobs.scheduler`, cronSchedule `*/5 * * * *` |
| frontend | RAILPACK | — | `/frontend` | `npm run start` (NOT standalone) |
| admin | DOCKERFILE | `admin/Dockerfile` | `admin` | (nginx; `BACKEND_UPSTREAM` env templated) |
| pgbouncer | image | `edoburu/pgbouncer:1.22.1-p0` | — | — |
| Postgres | plugin | — | — | — |

These values live in `.railway/railway.ts` (IaC, committed). `railway config plan` must show no drift after any manual dashboard edit.

## 3. Env essentials

- backend/cron `DATABASE_URL` = `postgresql+asyncpg://postgres:${{Postgres.POSTGRES_PASSWORD}}@${{pgbouncer.RAILWAY_PRIVATE_DOMAIN}}:6432/railway` (composed reference — dashboard edges). `PGBOUNCER_ENABLED=true`.
- pgbouncer: `DATABASE_URL=${{Postgres.DATABASE_URL}}`, `POOL_MODE=transaction`, `AUTH_TYPE=scram-sha-256`, pools 100/20/5, `SERVER_RESET_QUERY=DISCARD ALL`.
- `NEXT_PUBLIC_BASE_URL` (backend/cron/frontend) = `https://siddhesh-chaudhari.com` — revalidation webhook target; missing it silently breaks content updates.
- frontend `BACKEND_URL` / admin `BACKEND_UPSTREAM` = `http://${{backend.RAILWAY_PRIVATE_DOMAIN}}:8080`; frontend `PUBLIC_API_PROXY` = `https://admin-production-d152.up.railway.app` (build-time prerender fallback).
- Full reference: `docs/handoff/env-vars-registry.md`.

## 4. Deploy paths

1. **Normal:** push to `main` → native triggers deploy backend/cron/frontend/admin from the pushed commit. Verify: `railway status` / per-service deployments show the commit hash + SUCCESS.
2. **CI fallback:** `gh workflow run deploy.yml -f service=all` (or per service). Waits per-service for SUCCESS and runs a health gate. Token = gh `production` secret `RAILWAY_TOKEN` (account-level).
3. **Infra:** edit `.railway/railway.ts` → `railway config plan` (review!) → `railway config apply`. Omit = delete; secrets via `preserve()`; never `--include-variables`.
4. **One-off code deploy:** `railway up -y -d -s <service> -e production -p <project-id>` from repo root (uploads the git repo root; per-service configs select the build context). `railway redeploy -s <service> --from-source` rebuilds from the connected GitHub source's latest commit.

## 5. Troubleshooting (symptom → cause → fix)

| Symptom | Cause | Fix |
|---|---|---|
| Backend/cron crash: `DuplicatePreparedStatementError … __asyncpg_stmt_N__ already exists` on `select pg_catalog.version()` | An engine in the image doesn't disable asyncpg statement caches under pgbouncer. Happened with `alembic/env.py` (separate engine) and with pre-fix builds | Ensure `pgbouncer_connect_args()` is applied in BOTH `app/core/database.py::build_engine` AND `alembic/env.py`; ensure the deployed commit includes `3dca291`; `PGBOUNCER_ENABLED=true`; pgbouncer `SERVER_RESET_QUERY=DISCARD ALL` |
| Cron redeploys every tick and crashes with old-code errors | The GitHub source is pinned to the commit recorded at source-connect time; ticks rebuild that stale commit | Push fixes BEFORE connecting sources. Advance the pin: `railway redeploy -s cron --from-source -y` or any trigger push |
| CI/CLI: "Unauthorized" / "Invalid RAILWAY_TOKEN" | v5 CLI reads `RAILWAY_API_TOKEN` (ignores `RAILWAY_TOKEN`); project-scoped tokens are rejected by the CLI even though the raw API accepts them | Set `RAILWAY_API_TOKEN` env; use an ACCOUNT-level token for CI |
| `railway up` deploys the wrong service image (e.g. admin runs backend code) | The CLI uploads the git repo ROOT regardless of CWD; without per-service build config the builder picks the root Dockerfile | Per-service build configs are now set (see §2); for path override use `railway up -s admin admin --path-as-root`; passing `.` as PATH panics with "prefix not found" |
| Variable reference `${{Service.VAR}}` becomes a resolved/empty value when set via CLI/API | CLI `variable set` and GraphQL `variableUpsert` resolve references at write time | Create references via the IaC file (`.railway/railway.ts`) or the dashboard variable picker |
| Alembic `KeyError` / broken chain on deploy | Deploying an intermediate commit (`2bd928f..7527153` have a broken chain) | Deploy only from `main` HEAD; `alembic heads` must be exactly one head (`3acf873925fa`) |
| Admin 502/504 after backend redeploy | nginx cached the backend IP (no dynamic resolver) | Current image templates `BACKEND_UPSTREAM` + dynamic resolver; admin self-heals within `valid=10s` — no admin restart needed |
| CI health gate "no service domain yet" | `railway domain list` has no `-p` flag; needs a linked project in CI | Workflow runs `railway link -p "$RAILWAY_PROJECT_ID" -e production` first |
| `railway up` in a fresh checkout misses services | CLI link state is global, not per-directory | Pass explicit `-p <project-id> -e production -s <service>` on every command |
| Postgres plugin shows "Deploy failed" badge | The plugin got a repo connection (builds DB from app code) | Ensure no GitHub source on Postgres; redeploy last SUCCESS |
| Transient `DeadlineExceeded` on Docker Hub metadata during build | Docker Hub rate limit/timeout | Redeploy — not a code bug |
| `railway run` behaves like a local command | It IS local (env injection only) — not in-container | In-container execution = `railway ssh -s <service>` (register a key: `railway ssh keys add`; one key per Railway account); DB shells/tunnels = `railway connect Postgres [--tunnel-only -P <port>]` |
| CLI panic `volume -s <name> add` / empty `variable set --stdin` writes | CLI bugs | Pass service IDs, always pipe a real value via `--stdin`; values containing `$` must go via `--stdin` |

## 6. Verification gate suite (after any change)

```bash
railway service status -s <each service>          # SUCCESS
curl -sf https://siddhesh-chaudhari.com/api/v1/health
curl -sf https://admin.siddhesh-chaudhari.com/api/v1/health
curl -sf -o /dev/null https://admin.siddhesh-chaudhari.com/media/resumes/business-50f1c66ca317.pdf
bash scripts/check_ssr.sh --all https://siddhesh-chaudhari.com    # 13/13
curl -s https://siddhesh-chaudhari.com/api/v1/resumes  # 6
curl -s https://siddhesh-chaudhari.com/api/v1/timeline # 14
curl -s https://siddhesh-chaudhari.com/api/v1/overview # 6
railway logs -s cron --lines 20 | grep "scheduler: promoted"      # within 5 min
railway logs -s backend | grep -c DuplicatePreparedStatement      # 0
```

## 7. Restore

`docs/handoff/restore-procedure.md` §3. Server is Postgres **18** — scratch containers must be `postgres:18` (a 16 client aborts with "server version mismatch"). Drill executed 2026-09-02: PASS (14 timeline / 6 overview / 6 resumes / alembic head matched).

## 8. Secrets

Railway env vars, gh `production` environment secrets, local gitignored `backend/.env` — never git/logs/docs. `.railway/railway.ts` uses `preserve()` for every secret value.
