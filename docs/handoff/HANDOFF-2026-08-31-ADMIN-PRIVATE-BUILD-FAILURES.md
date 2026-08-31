# Handoff — Admin Private + Build Failures (next session)

**Date:** 2026-08-31 03:50 UTC · **Status:** PARTIAL — admin isolated nginx 200, frontend 13/13 SSR, backend private (no public), but backend/cron/postgres GitHub builds failing, PgBouncer not yet inserted
**Project:** portfolio-sid · **Railway:** awake-success `5edae34e-b3aa-4240-8410-f54d2d6b14d4` · **Env:** production `09b974a1-c963-4e29-bdcb-1d27abe887e2` (Postgres service `Postgres` capital P `4492dfb3...`)
**Prereqs:** `docs/handoff/HANDOFF-NEXT-MANUAL-2026-08-31.md` (single handoff before), `SESSION-HANDOFF-RAILWAY-INFRA-COMPLETE.md`, `HANDOFF-RAILWAY-INFRA-PLAN.md`, `docs/conventions.md` #13 `NEXT_PUBLIC_INDEXABLE=false` #14 `CORS_ALLOW_ORIGINS=[]` same-origin via proxies #15 secrets only Railway env / `production` env secret / local `.env`, `docs/handoff/env-vars-registry.md:25`, `docs/specs/email-provider/PLAN.md` DEFERRED (keep Resend `onboarding@resend.dev`), `LOCAL.md`
**Invariants held:** #13 false, #14 empty, #15 no secrets in git. Code phase DONE — resume canon 6 variants `869fc8d8c856` + `seed_resumes.py`, `/timeline/[id]` RSC + `GET /timeline/{id}/projects` scoped, `ContactResumes.tsx` filter, `pgbouncer` 6432 local sidecar `docker-compose.yml:19` + `config.py:17` pool tuning, `openapi.json` + `admin/src/api.d.ts`/`frontend/src/api.d.ts` regenerated, `change-password` `POST /admin/change-password` DB override `admin_credentials` migration `3acf873925fa`.

---

## 0. What is DONE (2026-08-31)

| Area | Artefact | Verify |
|---|---|---|
| **Auth** | `backend/app/features/auth/models.py:46` `AdminCredential` singleton, `service.py:92` `get_effective_password_hash` fallback, `service.py:196` `change_password` 12-128, `schemas.py:14` `ChangePasswordRequest`, `endpoints/router.py:68` `POST /admin/change-password` under `admin_auth()`, `admin/src/routes/settings/ChangePassword.tsx:1` + `admin/src/App.tsx:31` `/settings` + `AdminLayout.tsx:28` Settings nav | `pytest backend/app/features/auth` 29 passed (7 new), `openapi.json` 99671 contains `change-password`, `admin` build 1994 modules gzip 144KB, `alembic upgrade head` → `3acf873925fa` |
| **Secrets** | `SESSION_SECRET` `35dfa285...` `REVALIDATION_SECRET` `c764aed6...` `ADMIN_PASSWORD_HASH` of `ecfqTtqlUYn2b5daIOFjt` `RESEND_API_KEY` `re_ZePXv5dz...` `ADMIN_EMAIL=siddheshcoursemail@gmail.com` `RESEND_FROM=onboarding@resend.dev` (temp, `portfolio@` fails `domain is not verified` until TD-M3), `ENVIRONMENT=production` set `backend/cron` via `railway variable set --stdin --service backend/cron --skip-deploys` + `railway up --detach` | `curl https://backend-production-7a2a/.../api/v1/auth/login` generic 200, OTP email via `onboarding@resend.dev` to Gmail 200, `railway logs --service backend` `Uvicorn 8080` `alembic upgrade ... 3acf873925fa`, `railway variables --service backend/cron` shows 5 |
| **GitHub** | `RAILWAY_TOKEN=c5e95764...` set as `production` ENVIRONMENT secret `gh secret set RAILWAY_TOKEN --env production` PASS (`gh secret list --env production` shows, `gh api .../environments/production` id `20901780902`), auto-deploy enabled `railway service source connect --repo SIDDHESHCHAUDHARI2K24/portfolio-sid --branch main --service backend/frontend/cron` (backend linked true) | `gh secret list --env production` PASS |
| **Admin isolated** | `admin/Dockerfile` nginx multi-stage, `admin/nginx.conf:8` `proxy_pass http://backend.railway.internal:8080` for `/api/`, `/media/`, `/health`, `Dockerfile:1` backend API-only (no `admin-build`), `frontend/lib/api.ts:5` `BACKEND_URL` server vs `NEXT_PUBLIC` client split, `frontend/next.config.ts:36` `rewrites()` to `BACKEND_URL` + `remotePatterns` admin host | `npm run build --prefix admin` 1994, `npm run build --prefix frontend` 20 pages, `railway up --service admin` from `admin/` (isolated, `workdir admin`) → `admin-production-9cc7...` `admin SUCCESS` `nginx 200` `curl /api/v1/health` 200 after `8080` fix (was `8000` 502) |
| **Frontend private** | `railway variable set BACKEND_URL=http://backend.railway.internal:8080 --service frontend` + `railway variable delete NEXT_PUBLIC_API_BASE_URL`, `frontend/lib/api.ts` server `BACKEND_URL` fallback + `isPrivateNetworkError` retry via `https://admin-production-9cc7...` (sub-agent fallback), `next.config.ts` port `8080` | `bash scripts/check_ssr.sh --all https://frontend-production-38ac...` **13/13 PASS** (via sub-agent `d6728b8`+`a25434a` removing `output:"standalone"` → `next start`), `curl /api/v1/health` 200 via rewrites (after `a25434a` fix) |
| **Backend private** | `railway domain delete 8dc62e7d... --service backend --yes` → `No domains` (was `backend-production-7a2a`), `railway variables --service backend` `RAILWAY_PRIVATE_DOMAIN=backend.railway.internal`, `STORAGE_KIND=local` `LOCAL_STORAGE_DIR=/data` Volume `backend-volume` `0.8/48.8GB` READY | `curl https://admin.../api/v1/health` 200, `curl https://frontend.../api/v1/health` 200, `curl https://backend-.../api/v1/health` 404 private as expected |
| **Cron** | `scheduler.py:1` registry-driven `publishables()` 8 models + `run_crawler_retention` 90d, `serviceInstanceUpdate` `cronSchedule="*/5 * * * *"` `startCommand="python -m app.jobs.scheduler"` | `railway logs --service cron` `promoted 0 row(s)`, `railway api` shows `cronSchedule "*/5 * * * *"` |
| **Storage** | Railway Volume `/data` not R2 (your 4), `STORAGE_KIND=local` prod, `R2_*` only dev MinIO `docker-compose.yml:19` `R2_ENDPOINT http://localhost:9000` | `railway service list` `backend-volume` READY |

**Local DB seeded** via `seed_resumes.py` 11 tags/14 timeline inc `umbrella+Feenix Sports 2026-07` pinned/5 projects/43 skills/6 resumes. **Prod DB empty** — needs `railway run` seed after private networking verified.

---

## 1. Current infra (TL;DR)

| Service | Status | Build | Public | Private | Env (set) | Env (missing/deferred) |
|---|---|---|---|---|---|---|
| Postgres (`Postgres`) | ● Online (Deploy failed old) | — | — | `postgres.railway.internal:5432` `postgres-volume` | — | — |
| backend | ● Online (Deploy failed old GitHub, SUCCESS via CLI `b5d8b7db` DOCKERFILE) | Dockerfile `/Dockerfile` (API-only) | **None** (deleted, private `backend.railway.internal:8080`) | `DATABASE_URL=${{Postgres.DATABASE_URL}}` `STORAGE_KIND=local` `LOCAL_STORAGE_DIR=/data` `MEDIA_BASE_URL=https://admin.siddhesh-chaudhari.com` `CF_ACCESS_ENABLED=false` `ENVIRONMENT=production` `BACKEND_URL=http://backend.railway.internal:8080` | GlitchTip `GLITCHTIP_DSN` TD-36 deferred |
| admin | ● SUCCESS (CLI `admin/` isolated, nginx) | `admin/Dockerfile` `node:20-alpine`→`nginx:alpine` | `https://admin-production-9cc7.up.railway.app` (custom `admin.siddhesh-chaudhari.com` pending) | `admin.railway.internal` | *none* (proxy only) | `RAILWAY_DOCKERFILE_PATH` if reconnect to GitHub |
| frontend | ● Online (GitHub RAILPACK, `rootDirectory=/frontend`, `startCommand npm run start`) | `frontend/railway.toml` `builder=RAILPACK` | `https://frontend-production-38ac.up.railway.app` (custom `siddhesh-chaudhari.com` pending) | — | `BACKEND_URL=http://backend.railway.internal:8080` `NEXT_PUBLIC_INDEXABLE=false` `REVALIDATION_SECRET=c764...` | `NEXT_PUBLIC_UMAMI_*` deferred |
| cron | ● Completed (GitHub) | RAILPACK `python -m app.jobs.scheduler` | none | `cron.railway.internal` | same core as backend, `cronSchedule */5 * * * *` | — |
| pgbouncer | **NOT YET** — local sidecar `docker-compose.yml:19` `edoburu/pgbouncer:1.22` `6432:5432` `100/20/5`, `config.py:17` `database_pool_size/max_overflow/pgbouncer_enabled` `database.py:1` `pool_pre_ping` QueuePool | — | to be `pgbouncer.railway.internal:6432` | — | — |
| Volume | `backend-volume` `/data` READY | — | — | — | — | — |

**Build status nuance:** `railway deployment list --service backend` shows `7fcee73a FAILED` (old commit `153d285` RAILPACK, no `dockerfilePath`) and `b5d8b7db SUCCESS` (CLI DOCKERFILE). Recent pushes `2bd928f..7527153`+`cb98d15` did **not** create new backend deployments via GitHub (list still 2) — GitHub trigger not firing or still RAILPACK. `frontend` `admin` GitHub builds now SUCCESS after fixes (`a25434a` removed `output:"standalone"`). `postgres` also `Deploy failed` old.

---

## 2. Remaining tasks (do not reorder — your 4 decisions)

### TD-M3 Resend — **DEFERRED per your input**
- Keep `RESEND_FROM=onboarding@resend.dev` (works to `siddheshcoursemail@gmail.com`, verified `{"id":"6abd79ad..."}`), `RESEND_API_KEY` live. `siddhesh-chaudhari.com` verify later via Resend dashboard + Cloudflare DNS grey-cloud SPF/DKIM `resend._domainkey`/DMARC `_dmarc`, then revert `railway variable set RESEND_FROM=portfolio@siddhesh-chaudhari.com --service backend/cron` + `railway up`. Verify `dig TXT ...` + Resend `Verified`.

### Backend / Cron / Postgres builds — **FAILING**
- **Symptom:** `railway deployment list --service backend` latest GitHub `7fcee73a FAILED` (RAILPACK, commit `153d285`), CLI `b5d8b7db SUCCESS` (DOCKERFILE). Recent pushes not listed → GitHub webhook not building backend (watchPatterns? builder?). `cron`/`postgres` similarly `Deploy failed` (old).
- **Root hypothesis:** `backend` service `builder=RAILPACK` `dockerfilePath=null` `rootDirectory=null` per `railway api` — GitHub builds use Railpack, not Dockerfile, so `153d285` failed (maybe `uv` missing). Successful CLI used `builder=DOCKERFILE` `dockerfilePath=/Dockerfile`. `cron` same. `postgres` is managed DB, not code — `Deploy failed` may be auto-backup or healthcheck, not code.
- **Fix:** Force `backend`/`cron` to use Dockerfile via GitHub: set `RAILWAY_DOCKERFILE_PATH=Dockerfile` variable **or** `serviceInstanceUpdate` `dockerfilePath="Dockerfile"` + `builder` via `railway api` (Builder enum only `RAILPACK`/`NIXPACKS` — Dockerfile auto-detected if `dockerfilePath` set). Alternatively keep backend on `railway up --service backend` CLI (current SUCCESS) and note GitHub auto-deploy for backend is via CLI, not GitHub (contradicts `enable auto deploy` — decide). Verify `railway logs --service backend --lines 80` shows `Uvicorn` not Railpack, `railway deployment list` new SUCCESS.

### PgBouncer — **NOT YET** (your 4)
- **Current:** `docker-compose.yml:19` `pgbouncer:6432` `POOL_MODE=transaction` `MAX_CLIENT_CONN=100` `DEFAULT_POOL_SIZE=20` `RESERVE_POOL=5`, `backend/app/core/config.py:17` `database_pool_size 10` `max_overflow 5` `pgbouncer_enabled` `database.py:1` `pool_pre_ping`. Local tests `test_pgbouncer_config.py` 8 passed. Railway Postgres dashboard **does not show connections via pgbouncer** (your observation) — `DATABASE_URL` still `${{Postgres.DATABASE_URL}}` direct.
- **Plan:** Add Railway service `pgbouncer` ( `edoburu/pgbouncer:1.22` or `bitnami/pgbouncer` ), `DATABASE_URL` → `pgbouncer.railway.internal:6432`, env `PGBOUNCER_ENABLED=true` `DATABASE_URL=postgresql+asyncpg://...@pgbouncer.railway.internal:6432/railway` for `backend`/`cron`, keep `5432` for direct tests. `railway add -d pgbouncer` or Docker image service, set `DB_HOST=postgres.railway.internal` `DB_PORT=5432` etc., healthcheck `pg_isready`. Verify `railway variables --service backend` shows `DATABASE_URL` via pgbouncer, `railway logs --service pgbouncer` `pool`, and dashboard connections go through.

### File storage — **DONE, keep**
- Volume `backend-volume` READY, `app.py:136` `StaticFiles` `/media`, `MEDIA_BASE_URL=https://admin.siddhesh-chaudhari.com` (future custom, currently `admin-production-9cc7` works). No R2: `storage_kind` prod `local`, dev MinIO `R2_*` dev-only (`backend/.env.example:30` + `docker-compose.yml`).

### Custom domains — **after builds green**
- `admin` → `admin.siddhesh-chaudhari.com` via `railway domain admin.siddhesh-chaudhari.com --service admin` + Cloudflare `CNAME admin → <railway-target>` `dig +short` → Railway, `curl -sI https://admin...` SPA 200 `curl /api/v1/health` 200.
- `frontend` → `siddhesh-chaudhari.com` similarly (keep `frontend-production-38ac` until then). Verify `check_ssr.sh --all/--seo` 13/13 via sub-agent already PASS.

---

## 3. Execution order (next session)

1. **Fix backend/cron/postgres builds** — set `RAILWAY_DOCKERFILE_PATH` or `serviceInstanceUpdate` correctly, ensure `docker-compose` not needed, push, verify `railway deployment list` SUCCESS, `railway logs` `Uvicorn`/`scheduler promoted`.
2. **Add pgbouncer service** — `railway add` pgbouncer, wire `DATABASE_URL` via pgbouncer, set `PGBOUNCER_ENABLED=true`, verify dashboard.
3. **Re-verify admin/frontend proxies** — `curl https://admin.../api/v1/health` 200, `curl https://frontend.../api/v1/health` 200, `check_ssr.sh --all` 13/13.
4. **Custom domains** — `admin` + `frontend` as above, flip `MEDIA_BASE_URL` if needed, `railway up`.
5. **Seed prod** — `railway run --service backend -- bash -lc "uv run --project backend python backend/scripts/seed_resumes.py --canon backend/scripts/resume_canon.json --dry-run"` → real → `curl /api/v1/resumes | jq` 6, `timeline` 14, `check_ssr.sh --seo`.
6. **Restore drill** — `restore-procedure.md` scratch DB (deferred TD-36).

Record PASS/FAIL after each (`rhealth 200`, `check_ssr 13/13`, `dig`, `gh secret list -e production`, `railway service list`).

---

## 4. Specs to read

- `docs/conventions.md:6` domain hosts, `docs/conventions.md:86` #13 noindex, `docs/conventions.md:89` #14 CORS empty, `docs/conventions.md:92` #15 secrets, `docs/conventions.md:23` pgbouncer sidecar + pool tuning.
- `docs/handoff/env-vars-registry.md:25` (backend `RESEND_API_KEY` `ADMIN_EMAIL` `SESSION_SECRET` `ADMIN_PASSWORD_HASH` `REVALIDATION_SECRET`, frontend `NEXT_PUBLIC_API_BASE_URL` deleted, `BACKEND_URL`, `NEXT_PUBLIC_INDEXABLE`, `cron` same, `RAILWAY_TOKEN` production env).
- `docs/specs/email-provider/PLAN.md` (DEFERRED — `resend` stays, `sluhtie/freesend` note `freesend.io` file-transfer).
- `docs/handoff/POST-DEVELOPMENT-RECAP-2026-08-30.md` (resume `869fc8d8c856` 6 PDFs hashed `resumes/{variant}-{sha12}.pdf`, timeline `[id]` + `/{id}/projects` 27 passed, pgbouncer `6432` 8 passed).
- `backend/app/core/config.py:17` pool, `backend/app/core/database.py:1` QueuePool, `backend/app/jobs/scheduler.py:1` 5-min idempotent, `backend/app/features/auth/service.py:92` `change_password` + `admin_credentials`, `admin/src/routes/settings/ChangePassword.tsx:1`.
- `docker-compose.yml:19` pgbouncer, `admin/Dockerfile:1` + `admin/nginx.conf:8` proxy `8080`, `frontend/next.config.ts:36` rewrites `BACKEND_URL` `frontend/lib/api.ts:5` fallback via `admin` public, `frontend/package.json:8` `next start` (not standalone).

---

## 5. Useful commands

```bash
railway status; railway service list --json | python3 -m json.tool | head -n 60
railway variables --service backend | grep -E "DATABASE_URL|STORAGE|ADMIN|SESSION|RESEND|MEDIA|RAILWAY_PRIVATE"
railway variables --service frontend | grep -E "BACKEND_URL|NEXT_PUBLIC"
railway variables --service admin | grep -E "RAILWAY_PRIVATE|RAILWAY_SERVICE"
railway logs --service backend --lines 80; railway logs --service admin --lines 80; railway logs --service frontend --lines 80; railway logs --service cron --lines 30
railway deployment list --service backend --json | python3 -m json.tool | head -n 80
railway api "query { service(id:\"57cd6875-5de4-4d5c-9e27-cd0d062c0c58\") { serviceInstances(first:1){ edges{ node{ builder dockerfilePath rootDirectory cronSchedule startCommand } } } } }" | python3 -m json.tool
curl -s https://admin-production-9cc7.up.railway.app/api/v1/health | head
curl -s https://frontend-production-38ac.up.railway.app/api/v1/health | head
bash scripts/check_ssr.sh --all https://frontend-production-38ac.up.railway.app 2>&1 | tail -n 20
gh secret list --env production; gh auth switch --user SIDDHESHCHAUDHARI2K24; git push origin main; gh auth switch --user feenix-sid-2k26
# pgbouncer add
railway add --service pgbouncer --image edoburu/pgbouncer:1.22 # then set DB_HOST=postgres.railway.internal etc., or via Dashboard
# seed prod (after private verified)
railway run --service backend -- bash -lc "uv run --project backend python backend/scripts/seed_resumes.py --canon backend/scripts/resume_canon.json --dry-run"
railway run --service backend -- bash -lc "uv run --project backend python backend/scripts/seed_resumes.py --canon backend/scripts/resume_canon.json"
```

---

## 6. Git state at handoff

- **Pushed to `main`:** `2bd928f` admin isolate + private backend `+ change-password`, `9dffb0b` admin isolated Dockerfile fix, `626369b` repo-root Dockerfile for GitHub, `c241174`/`060b5f9` empty triggers, `efb2c1d` frontend standalone, `a25434a` frontend `next start` (sub-agent, now SUCCESS), `7527153` admin 8080, `cb98d15` code-phase 37 files (resume canon etc.), plus `d6728b8` fallback. **Pending local:** admin `DOCKERFILE` isolated vs repo-root divergence (admin now CLI `admin/` isolated, GitHub `admin/Dockerfile` repo-root) — keep CLI isolated, GitHub admin is `source=None` (CLI) not `RAILPACK` — note divergence.
- **Working tree still `M`:** `.gitignore` `resumes/*.pdf` gitignored, `backend/.env` `RESEND_API_KEY` live, `admin/src/routes/...` etc. — see `git status --short`. `resumes/*.pdf` 6 files hashed locally, not in git. `RAILWAY_TOKEN` value `c5e95764...` rotate after use (in `production` env secret).
- **DoD before UI:** backend/cron/postgres builds green, pgbouncer 6432 via dashboard, admin+frontend proxies 200, SSR 13/13 + SEO 6/6, `NEXT_PUBLIC_INDEXABLE` false, custom domains SSL green, seed prod 6/14.

---

## 7. Prompt for next session

```
Read docs/handoff/HANDOFF-2026-08-31-ADMIN-PRIVATE-BUILD-FAILURES.md as single source. Do not re-implement code-phase (resume canon, timeline [id], pgbouncer pool) — they are DONE.

Goal: Fix Railway builds for backend/cron/postgres (currently Deploy failed, but Online via old CLI deploy b5d8b7db), add Railway PgBouncer service on 6432 so all Postgres connections go via pgbouncer (dashboard), keep file storage on Railway Volume /data (no R2), keep Resend onboarding@resend.dev deferred, keep admin.siddhesh-chaudhari.com via isolated admin nginx proxy to backend.railway.internal:8080 (backend private, no public domain).

Execution order: backend build (RAILWAY_DOCKERFILE_PATH vs builder RAILPACK, dockerfilePath, watchPatterns) → cron schedule */5 + same env → postgres Deploy failed triage → pgbouncer edoburu/pgbouncer:1.22 between Postgres and backend/cron (DATABASE_URL via pgbouncer, PGBOUNCER_ENABLED=true) → re-verify admin 200 + frontend 200 + check_ssr.sh 13/13 → custom domains → seed prod via railway run seed_resumes.py.

Verify after each: railway deployment list SUCCESS, railway logs Uvicorn/scheduler, curl /api/v1/health 200 via proxies, dig, gh secret list -e production, service list volumes READY. Record PASS/FAIL, do not advance on FAIL. Use systematic-debugging per service, and deepseek v4 flash subagent for deployment retries up to 3.
```

---

## 8. Agent framework (how to work)

For **every** task, use the 8-stage loop via `superpowers` skills (invoke before any response/action):

1. **brainstorm** (`superpowers:brainstorming`) — check gaps; small decisions you can take (note them), big gaps ask user.
2. **plan** (`superpowers:writing-plans` or `plan` skill) — why/what/where/tests/acceptance/chronology/dependencies; keep `docs/` as source of truth, never violate `docs/conventions.md`.
3. **execute** — orchestrate; use sub-agents (`task` with `subagent_type: general`) for independent tracks, respect dependency map (don't parallelize what needs infra).
4. **code** (`superpowers:test-driven-development` before code, `superpowers:systematic-debugging` if same error ×3) — implement per `development_plan/todos/`, create tests + checklist, code-review, use `/react-doctor` for frontend.
5. **test** — per plan acceptance, `pytest`, `ruff check`, `npm run build`, `check_ssr.sh` 13/13.
6. **code review** (`superpowers:requesting-code-review` or `review` skill) — re-verify tests + logic.
7. **verify** — checklist per To-do, if issues loop back via sub-agent plan.
8. **commit** (`conventional` `feat(backend):` `fix(frontend):` `chore:`) — one logical change per commit, never commit secrets, only stage intended files.

**Parallelism:** `dispatching-parallel-agents` skill when 2+ independent tasks (e.g., frontend vs backend) — launch via `task` tool.

**Verification before completion:** `verification-before-completion` skill — run `rhealth`, `check_ssr`, `dig`, `gh secret list`, `railway service list` before claiming PASS.

**Graphify/CodeGraph:** If `graphify-out/` or `.codegraph/` exists, use `graphify query` or `codegraph_explore` before grep/Read for architecture questions.

After code changes, run `graphify update .` and `git push` triggers Railway auto-deploy (since `enable auto deploy`).

