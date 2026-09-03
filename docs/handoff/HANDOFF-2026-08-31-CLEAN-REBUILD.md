# Handoff — Clean Railway Rebuild (PLAN FIRST)

**Date:** 2026-08-31 · **Status:** DESIGN APPROVED — execute ONLY after Phase 0 planning in the new session
**New project:** `portfolio-sid-v2` · **Old project (deprecated):** `awake-success` (`5edae34e-b3aa-4240-8410-f54d2d6b14d4`, env `production` `09b974a1-c963-4e29-bdcb-1d27abe887e2`) — delete after cutover
**Supersedes:** `HANDOFF-2026-08-31-ADMIN-PRIVATE-BUILD-FAILURES.md` (old env is deprecated)
**Code:** `main` @ `595b57e` is complete — no code changes expected except `.github/workflows/deploy.yml` (separate task, §6)
**Prereqs to read:** `docs/conventions.md` (invariants #1–#15, esp. #13 noindex, #14 CORS empty, #15 secrets), `docs/handoff/env-vars-registry.md`, `docs/handoff/restore-procedure.md`, `LOCAL.md`

---

## §0 INVARIANT — this session MUST plan before executing

1. Read this doc + `docs/conventions.md` + `env-vars-registry.md` + `restore-procedure.md`.
2. Run superpowers **brainstorming**, then **writing-plans**, over the DESIGN in §1. Confirm the plan with the user at a checkpoint **before touching Railway**.
3. Execute phase by phase (§2). Record **PASS/FAIL** per gate (§3). **Never advance on FAIL.** Use `systematic-debugging` per failing service; use `verification-before-completion` before every PASS claim.
4. No secrets in git (§5). `graphify update .` after any file edits.

---

## §1 Target system design

```
Cloudflare (registrar + DNS only — stays as-is)
  siddhesh-chaudhari.com        → CNAME → <frontend>.up.railway.app   (new hostname after cutover)
  admin.siddhesh-chaudhari.com  → CNAME → <admin>.up.railway.app      (new hostname after cutover)

Railway project "portfolio-sid-v2" / production
  ┌ frontend  PUBLIC   Next.js SSR/ISR · rewrites /api/* → BACKEND_URL (private)
  ├ admin     PUBLIC   nginx SPA · proxies /api, /media, /health → backend.railway.internal:8080
  ├ backend   PRIVATE  FastAPI :8080 · alembic upgrade head at start · volume /data
  ├ cron      PRIVATE  cron */5 · python -m app.jobs.scheduler · same env as backend
  ├ pgbouncer PRIVATE  edoburu/pgbouncer:1.22.1-p0 · LISTEN 6432
  └ Postgres  PRIVATE  Railway plugin · postgres.railway.internal:5432
```

### 1.1 Data path — ALL connections through pgbouncer

```
backend/cron → pgbouncer.railway.internal:6432 → postgres.railway.internal:5432
                 AUTH_TYPE=scram-sha-256           (Railway Postgres plugin)
                 POOL_MODE=transaction
                 MAX_CLIENT_CONN=100 / DEFAULT_POOL_SIZE=20 / RESERVE_POOL_SIZE=5
```

- Backend engine: `database_pool_size=10`, `database_max_overflow=5`, `pool_pre_ping=True`,
  **both** asyncpg statement caches disabled via `connect_args` when `PGBOUNCER_ENABLED=true`
  (already implemented in `backend/app/core/database.py::build_engine`, tests in
  `backend/app/tests/test_pgbouncer_config.py` — 10 passed).
- Nothing else connects to Postgres directly. The only service with Postgres URL is pgbouncer itself.

### 1.2 Exposure matrix

| Service | Public domain | Private DNS | Build |
|---|---|---|---|
| frontend | ✅ custom + generated | — | RAILPACK, `rootDirectory=/frontend`, `startCommand=npm run start` (`next start`, NOT standalone) |
| admin | ✅ custom + generated | `admin.railway.internal` | Dockerfile `admin/Dockerfile`, `rootDirectory=admin` |
| backend | ❌ **none — never `railway domain`** | `backend.railway.internal:8080` | Dockerfile `/Dockerfile` (repo root) |
| cron | ❌ n/a | `cron.railway.internal` | same image as backend, `startCommand=python -m app.jobs.scheduler`, `cronSchedule=*/5 * * * *` |
| pgbouncer | ❌ none | `pgbouncer.railway.internal:6432` | image `edoburu/pgbouncer:1.22.1-p0` |
| Postgres | ❌ none | `postgres.railway.internal:5432` | Railway plugin — **NEVER repo-connected** |

### 1.3 Volumes

- `backend-volume` → `/data` on backend (`STORAGE_KIND=local`, `LOCAL_STORAGE_DIR=/data`).
  **No R2 in prod** — `R2_*` are dev-only (MinIO in docker-compose).
- Postgres plugin has its own volume (auto-created with the plugin).
- Before deleting the old project: inspect old `backend-volume` `/data` (0.8 GB) — expected empty;
  copy anything real to the new volume via a scratch download before teardown.

### 1.4 Env inventory (values harvested at §2 phase 1; placeholders only here — invariant #15)

| Service | Vars |
|---|---|
| backend | `ENVIRONMENT=production`, `DATABASE_URL=postgresql+asyncpg://postgres:<NEW_DB_PW>@pgbouncer.railway.internal:6432/railway`, `PGBOUNCER_ENABLED=true`, `DATABASE_POOL_SIZE=10`, `DATABASE_MAX_OVERFLOW=5`, `STORAGE_KIND=local`, `LOCAL_STORAGE_DIR=/data`, `MEDIA_BASE_URL=https://admin.siddhesh-chaudhari.com`, `SESSION_SECRET`, `ADMIN_PASSWORD_HASH`, `ADMIN_EMAIL=siddheshcoursemail@gmail.com`, `RESEND_API_KEY`, `RESEND_FROM=onboarding@resend.dev`, `REVALIDATION_SECRET`, `CORS_ALLOW_ORIGINS=` (empty), `CF_ACCESS_ENABLED=false` |
| cron | same core as backend: `ENVIRONMENT`, `DATABASE_URL` (via pgbouncer), `PGBOUNCER_ENABLED`, `REVALIDATION_SECRET`, `STORAGE_KIND`, `LOCAL_STORAGE_DIR`, `MEDIA_BASE_URL` |
| frontend | `BACKEND_URL=http://backend.railway.internal:8080`, `NEXT_PUBLIC_INDEXABLE=false`, `REVALIDATION_SECRET` (same value as backend). `NEXT_PUBLIC_UMAMI_*` deferred |
| admin | none (pure proxy) |
| pgbouncer | `DATABASE_URL=postgresql://postgres:<NEW_DB_PW>@postgres.railway.internal:5432/railway`, `POOL_MODE=transaction`, `AUTH_TYPE=scram-sha-256`, `MAX_CLIENT_CONN=100`, `DEFAULT_POOL_SIZE=20`, `RESERVE_POOL_SIZE=5`, `LISTEN_ADDR=*`, `LISTEN_PORT=6432`, `ADMIN_USERS=postgres`, `IGNORE_STARTUP_PARAMETERS=extra_float_digits` |

Notes:
- `<NEW_DB_PW>` comes from the **new** Postgres plugin's own `DATABASE_URL` (Railway generates it) —
  never reuse the old DB password. Old DB content is empty anyway; content comes from the seed (§2 phase 8).
- `SESSION_SECRET` / `ADMIN_PASSWORD_HASH` / `RESEND_API_KEY` / `REVALIDATION_SECRET`: harvest from the
  **old** project before deletion (`railway variables --service backend`) — or regenerate
  (`openssl rand -hex 32`), keeping backend/cron/frontend `REVALIDATION_SECRET` identical.
- `RESEND_FROM=onboarding@resend.dev` stays until TD-M3 (DNS SPF/DKIM/DMARC for portfolio@).

### 1.5 GitHub wiring (both mechanisms — user decision)

1. **Native triggers:** user re-authorizes the Railway GitHub App on `SIDDHESHCHAUDHARI2K24/portfolio-sid`
   (Railway dashboard → service → Source → Connect GitHub; OAuth once). After that,
   `railway service source connect` creates real push triggers. Today this fails with
   *"Cannot create deployment trigger … because no one in the project has access to it"* —
   that must be fixed BEFORE §2 phase 5, else phase 5 cannot PASS.
2. **CI fallback:** `.github/workflows/deploy.yml` (manual `workflow_dispatch`, RAILWAY_TOKEN) — separate
   task, see §6. Token in gh `production` environment secret must be **rotated to a token scoped to
   `portfolio-sid-v2`** (current one belongs to the old project).

### 1.6 Hard-won invariants (each one cost a real failure on 2026-08-31 — do not relearn)

1. pgbouncer image tag is **`edoburu/pgbouncer:1.22.1-p0`** — tag `1.22` does not exist.
2. `AUTH_TYPE=scram-sha-256` (image writes the plaintext password to `userlist.txt`; pgbouncer 1.22.1
   derives SCRAM). `auth_type=any` → *"auth_type=any requires forced user"* (unsupported by the image);
   `md5` fails against Postgres 16 scram verifiers.
3. PgBouncer **transaction mode + asyncpg prepared statements** → `DuplicatePreparedStatementError`.
   Fixed in code (both caches off under `PGBOUNCER_ENABLED=true`). Verified: 12 connections through local
   docker-compose pgbouncer, cache sizes 0 on the live asyncpg connection.
4. **Never connect the Postgres plugin to the GitHub repo** — it then builds the DB from app code via
   RAILPACK and shows "Deploy failed".
5. Frontend must run `npm run start` (`next start`); `output:"standalone"` was removed in `a25434a`.
6. Admin nginx needs the **dynamic resolver** (reads `/etc/resolv.conf`, brackets IPv6) — already in
   `admin/nginx.conf` + `admin/Dockerfile` (`595b57e`). Otherwise every backend redeploy 502s admin
   until manual restart.
7. Backend migrations run in the start command (`alembic upgrade head && uvicorn …`), never at build time
   (private networking is runtime-only). `alembic heads` must be exactly one head (HEAD is
   `3acf873925fa`; chain is valid only at ≥ `cb98d15` — deploys must build from `main` HEAD).
8. Backend listens on `PORT` (Railway sets 8080) — admin/frontend proxies target `:8080`, not 8000.
9. `railway up --service <x>` builds from the **current linked project** — never run rebuild commands
   against the old project after linking the new one; keep an explicit old-project context for harvest only.

---

## §2 Runbook (phases 1–10)

> Every `railway` command below must run with the CLI **linked to the intended project**.
> Harvest (phase 1) = old project context. Everything else = `portfolio-sid-v2`.

### Phase 0 — PLAN (mandatory gate)
Brainstorm + writing-plans over §1 with the user. Produce a written plan with per-phase
acceptance criteria and checkpoints. **Checkpoint: user approves plan.** Nothing on Railway before this.

### Phase 1 — Harvest secrets + new project skeleton
1. Linked to OLD project: `railway variables --service backend` and `--service frontend`; copy
   `SESSION_SECRET`, `ADMIN_PASSWORD_HASH`, `RESEND_API_KEY`, `REVALIDATION_SECRET`, `ADMIN_EMAIL`
   into local notes (never git). Also `railway variables --service Postgres` (keep old DB URL aside
   only for forensics; NOT reused).
2. Create project: `railway init -n portfolio-sid-v2` (verify flags via `railway init --help`; dashboard
   alternative: railway.com → New Project). Production environment is auto-created.
3. Create Postgres plugin: `railway add -d postgres -s Postgres`.
4. Create services (empty, then wire sources in phase 5):
   - `railway add -s backend`
   - `railway add -s cron`
   - `railway add -s frontend`
   - `railway add -s admin`
   - `railway add --image edoburu/pgbouncer:1.22.1-p0 --service pgbouncer`
5. Volume for backend `/data` (dashboard: backend → Settings → Volumes → add `backend-volume` @ `/data`).
6. Record every service ID + environment ID (`railway service list --json`).

**Gate:** `railway service list` shows 6 services in `portfolio-sid-v2/production`; old project untouched.

### Phase 2 — Data layer (Postgres → pgbouncer)
1. Set pgbouncer env (§1.4, using the NEW plugin's `DATABASE_URL` from
   `railway variables --service Postgres`).
2. Deploy pgbouncer (variable set triggers redeploy).
3. **Gate:** `railway logs --service pgbouncer` → `listening on 0.0.0.0:6432`, `PgBouncer 1.22.1 … process up`.
4. Smoke: from backend's eventual URL values, verify `postgres.railway.internal:5432` reachable by
   pgbouncer (`login attempt: db=railway user=postgres` appears when a client connects; a connection
   from the new backend in phase 3 is the real proof).

### Phase 3 — backend (private, via pgbouncer)
1. Set backend env (§1.4). `DATABASE_URL` points at `pgbouncer.railway.internal:6432`.
2. Deploy: GitHub source isn't connected yet, so first deploy via
   `railway up --service backend` from **repo root** (Dockerfile `/Dockerfile`).
3. **Gates:** deployment SUCCESS · logs show `alembic …` then `Uvicorn running on http://0.0.0.0:8080`,
   NO `DuplicatePreparedStatementError`, NO `KeyError` in alembic · `railway run --service backend -- sh -c "..."`
   executes `select pg_catalog.version()` against pgbouncer (via the app's own env) successfully.
4. Confirm backend has **no public domain** (`railway domain` shows none) and `RAILWAY_PRIVATE_DOMAIN` present.

### Phase 4 — cron
1. Set cron env (same core as backend, §1.4).
2. Set instance: `cronSchedule="*/5 * * * *"`, `startCommand="python -m app.jobs.scheduler"`,
   same Dockerfile build config (via `serviceInstanceUpdate` — introspect
   `__type(name:"ServiceInstanceUpdateInput")` for exact fields).
3. Deploy via `railway up --service cron` from repo root.
4. **Gate:** next run within 5 min logs `scheduler: promoted 0 row(s) across 8 model(s)` with no asyncpg errors.

### Phase 5 — GitHub wiring (native triggers) + first full push
1. **User action:** re-authorize Railway GitHub App on the repo (dashboard OAuth). **Gate before proceeding:**
   `railway service source connect --repo SIDDHESHCHAUDHARI2K24/portfolio-sid --branch main --service backend --json`
   succeeds AND a trigger deploy fires.
2. Connect all four code services (backend, cron, frontend, admin — **NEVER Postgres**).
3. Set per-service build config:
   - backend: `dockerfilePath="/Dockerfile"`, `rootDirectory=null`
   - cron: same + `cronSchedule` + `startCommand` (already in phase 4)
   - frontend: `rootDirectory="/frontend"`, builder RAILPACK, `startCommand="npm run start"`
   - admin: `dockerfilePath="admin/Dockerfile"`, `rootDirectory="admin"`
4. Trigger: push a small commit to `main` (e.g. this handoff doc).
5. **Gates:** all four deployments appear from the push with **SUCCESS**; deployment metas show the
   intended builder/dockerfilePath/rootDirectory; `railway logs` show Uvicorn (backend), scheduler (cron),
   nginx (admin), next start (frontend).

### Phase 6 — CI fallback workflow (separate task — see §6)
- Draft, review, and merge `.github/workflows/deploy.yml` per its own plan (§6).
- Rotate gh `production` env secret `RAILWAY_TOKEN` to a token scoped to `portfolio-sid-v2`.
- **Gate:** `gh secret list --env production` shows `RAILWAY_TOKEN`; a manual `workflow_dispatch`
  deploys all four services to `portfolio-sid-v2` and the workflow's health-check step passes.

### Phase 7 — Frontends + proxies
1. Admin deploy (from phase 5 push) → **Gates:** `curl https://<admin>.up.railway.app/` 200 (SPA);
   `/api/v1/health` 200; `/media/…` proxies without 404 (backend serves `/media` from `/data`).
2. Frontend → **Gates:** `bash scripts/check_ssr.sh --all https://<frontend>.up.railway.app` → **13/13**;
   `/api/v1/health` 200 via rewrites; direct backend URL → 404/private (no public domain).
3. Kill-test: `railway service restart --service backend --yes` → admin `/api/v1/health` recovers to 200
   **without** admin restart (proves the nginx dynamic resolver).

### Phase 8 — Content seed
1. Dry-run: `railway run --service backend -- bash -lc "uv run --project backend python backend/scripts/seed_resumes.py --canon backend/scripts/resume_canon.json --dry-run"`.
2. Real run: same without `--dry-run`.
3. **Gates:** `/api/v1/resumes` → 6 · `/api/v1/timeline` → 14 · overview 6 rows · `check_ssr.sh --seo` passes;
   pgbouncer logs show the traffic; Postgres dashboard shows connections through pgbouncer.

### Phase 9 — Custom domains + docs
1. `railway domain siddhesh-chaudhari.com --service frontend` and
   `railway domain admin.siddhesh-chaudhari.com --service admin`; update Cloudflare CNAMEs to the new
   Railway targets. **Gates:** `dig +short` returns Railway · `curl -sI https://…` 200 · SSL green
   (Railway auto-certs) · `/api/v1/health` 200 on the custom admin domain.
2. Update `docs/conventions.md` §Connection pooling (a dedicated pgbouncer service IS now deployed —
   current text claims "no sidecar service is deployed") + image tag `1.22.1-p0` + prepared-statement
   note. Update `env-vars-registry.md` (pgbouncer service vars, `PGBOUNCER_ENABLED`). Commit as
   `docs(...)`. Run `graphify update .`.

### Phase 10 — Cutover + teardown + drill
1. Re-run full gates on the new project (§3 DoD).
2. Inspect old project `backend-volume` `/data`; copy anything real; then delete old project
   (`railway delete` — verify flag via `--help`; dashboard deletion is the safe fallback).
3. Restore drill per `docs/handoff/restore-procedure.md` §3 (scratch docker Postgres) — record result
   in `docs/conventions.md`.
4. Final: `git status` clean of secrets; `gh secret list --env production`; handoff archived.

---

## §3 Gates — final DoD checklist

- [ ] All 4 code services deploy from a GitHub push (native trigger) — SUCCESS status
- [ ] CI fallback `workflow_dispatch` deploys all 4 (RAILWAY_TOKEN rotated to portfolio-sid-v2)
- [ ] backend: Uvicorn 8080, alembic clean, zero prepared-statement/auth errors, no public domain
- [ ] cron: `*/5` running, `promoted …` through pgbouncer
- [ ] pgbouncer: 6432, transaction, scram — connections visible in Postgres dashboard
- [ ] admin 200 + `/api/v1/health` 200 (+ self-heals across backend restarts)
- [ ] frontend `check_ssr.sh --all` **13/13**, `/api/v1/health` 200, backend direct = private
- [ ] `NEXT_PUBLIC_INDEXABLE=false` · `CORS_ALLOW_ORIGINS` empty · no secrets in git
- [ ] custom domains SSL green on both hostnames · Cloudflare CNAMEs updated
- [ ] seed: 6 resumes / 14 timeline / 6 overview
- [ ] old project deleted · restore drill executed and recorded

---

## §4 Gotchas

- Railway CLI interactive prompts: supply flags (`--service`, `--image`, `--repo`, `--branch`, `--yes`);
  never rely on piped stdin.
- `railway run` executes **locally** with env injection — not inside the container; use it only for
  env access, not for "run on the server".
- Build logs for a specific deployment: `railway logs <deployment-id> --build`.
- Transient Docker Hub timeouts (`DeadlineExceeded` on registry metadata) → just redeploy; not a code bug.
- `railway service restart` needs `--yes` in non-interactive shells.
- Postgres "Deploy failed" badge historically = a repo-triggered RAILPACK build of the DB plugin;
  remedy = ensure no repo connection on Postgres + redeploy last SUCCESS
  (`deploymentRedeploy` mutation).
- Alembic chain: intermediate commits `2bd928f..7527153` have a broken chain (`KeyError:
  '869fc8d8c856'`) — builds must come from `main` HEAD (≥ `cb98d15`). Never deploy intermediate commits.

---

## §5 Secrets

- Nothing secret enters git, logs, or this doc — placeholders only. Values harvested in phase 1 stay
  in local notes or Railway env.
- `RAILWAY_TOKEN` lives ONLY as the GitHub `production` environment secret (rotate to new project).
- Local `backend/.env`, `resumes/*.pdf` stay gitignored.

---

## §6 Separate task — `.github/workflows/deploy.yml` (CI fallback deployer)

**Do not fold this into the rebuild. It is its own planned task** (own commit `ci(deploy): …`).

### Why it is complex
Multiple build contexts (repo root for backend/cron, `frontend/` for frontend, `admin/` for admin),
one cron service that must keep its `startCommand`, a token that must never be logged, interplay with
native Railway triggers (double-deploy risk), and slow `railway up` uploads (needs `workdir` per job +
`.gitignore`-aware uploads). Plan it separately with its own brainstorm/plan step.

### Design inputs (for the planning session)
- Trigger: `workflow_dispatch` by default (native triggers already deploy on push — avoid double builds).
  Optional `push: branches: [main]` gated behind a `deploy-fallback` boolean input for emergencies.
- Input: `service` choice (`all` | `backend` | `cron` | `frontend` | `admin`).
- Runner: `ubuntu-latest`; Railway CLI via `ghcr.io/railwayapp/cli` (verify image name) or
  `npx @railway/cli` — pin a version.
- Auth: `RAILWAY_TOKEN` from `environment: production` secret; `env:`-inject only, never echo;
  add `RAILWAY_SILENT=true` to shrink output.
- Per-service jobs (matrix over service × workdir):
  - backend: workdir repo root → `railway up --service backend --detach`
  - cron: repo root → `railway up --service cron --detach`
  - frontend: `frontend/` → `railway up --service frontend --detach`
  - admin: `admin/` → `railway up --service admin --detach`
  - (pgbouncer, Postgres: NOT deployed by CI)
- After deploy: `railway status` + `curl -f https://<frontend>/api/v1/health` health gate step;
  fail the job on non-200 with logs (`railway logs --service <s> --lines 50`).
- `concurrency: ci-deploy` (cancel-in-progress) · `timeout-minutes: 30` · `permissions: contents: read`.
- Project targeting: link via `RAILWAY_PROJECT_ID` env (new project id) so the workflow never
  touches the old project.

### Acceptance criteria
- Manual dispatch → 4 services SUCCESS in `portfolio-sid-v2`, health gate green.
- No secret value in workflow logs or repo.
- Native push triggers and this workflow never run concurrently on the same service (concurrency +
  dispatch-only default).

---

## §7 Prompt for the new session

```
Read docs/handoff/HANDOFF-2026-08-31-CLEAN-REBUILD.md. This is a PLAN-FIRST session:
run brainstorming + writing-plans over §1 design, checkpoint with the user, then execute
§2 phases 0–10 in order. Old project (awake-success) is deprecated — do not "fix" it; build
portfolio-sid-v2 fresh and delete the old one after cutover. All Postgres connections go
through pgbouncer (6432, scram-sha-256, transaction). Only admin + frontend are public;
backend/cron/pgbouncer/Postgres stay private. Plan .github/workflows/deploy.yml as its own
separate task (§6). Record PASS/FAIL per gate; never advance on FAIL.
```
