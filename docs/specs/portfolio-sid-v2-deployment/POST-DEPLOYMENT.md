# POST-DEPLOYMENT — portfolio-sid-v2

**Date:** 2026-09-02/03 · **Status:** complete (final DoD + restore drill recorded at the end)

Results log for the clean Railway rebuild. Design: `DESIGN.md` · Plan: `PLAN.md`.

## Service/ID map (Railway)

| Service | ID | Exposure |
|---|---|---|
| frontend | 3f80c970-28ff-4eeb-9366-a2fbd0456afa | public — siddhesh-chaudhari.com + frontend-production-bf2a.up.railway.app |
| admin | b3aceea2-616d-4dd1-8b27-f7e9bda71369 | public — admin.siddhesh-chaudhari.com + admin-production-d152.up.railway.app |
| backend | f21cc3ff-3046-4c00-ab9e-7e6e7d959a27 | private, volume backend-volume @ /data |
| cron | 1da11d3f-778b-4353-af44-47e62f8116dc | private, `*/5` scheduler |
| pgbouncer | bcf2d4ce-14d2-4414-9c53-5b8596015899 | private, 6432 |
| Postgres | ac7a4426-d3ae-4b6f-8e02-1a56b00cb1c6 | plugin |

Project `e0f5e770-6a95-41aa-99e4-3be94884d6ca` · env production `a6f89029-ec4a-46a7-9950-84dbfb3d4fc6`.

## Gates (recorded PASS/FAIL per phase)

- P1 skeleton: PASS (6 services, volume attached, IDs recorded)
- P2 pgbouncer: PASS (`listening on 0.0.0.0:6432`, `PgBouncer 1.22.1 … process up`, scram/transaction/100-20-5)
- P3 backend: PASS (alembic chain → `3acf873925fa`, Uvicorn 8080, no public domain, traffic through pgbouncer). Fixed mid-phase: `alembic/env.py` engine now uses `pgbouncer_connect_args` (`3dca291`) after redeploys crashed with `DuplicatePreparedStatementError`.
- P4 cron: PASS (`scheduler: promoted 0 row(s) across 8 model(s)` via pgbouncer, `*/5`, standalone design confirmed — see DESIGN D11)
- P5 native triggers: PASS (4× `deploymentTriggerCreate` via `railway service source connect` after user re-authorized the Railway GitHub App; 4 SUCCESS deploys from the trigger push)
- P6 CI fallback: PASS (`.github/workflows/deploy.yml` rewritten; token rotated; manual dispatch deploys all 4 + health gate green)
- P7 frontends: PASS (admin 200 + `/api/v1/health` 200 + `/media` 200; frontend `check_ssr.sh --all` 13/13; kill-test: backend restart → admin self-heals without restart)
- P8 seed: PASS (6 resumes / 14 timeline / 6 overview / PDF 200 via volume; SEO 6/6; seed run in-container via `railway ssh`)
- P9 domains: PASS (both custom domains verified ACTIVE, dig → Railway, SSL green, `/api/v1/health` 200 on both; docs updated)
- P10 cutover: PASS (see below)

## Hard-won lessons (all encoded in PLAN.md Global Constraints)

1. `railway up` uploads the **git repo root** regardless of CWD — non-root build contexts need `--path-as-root <dir>`; `.` as PATH panics ("prefix not found"). Once per-service build configs exist (`dockerfilePath`/`rootDirectory`), plain `railway up -s <svc>` from repo root builds correctly.
2. **Every engine** (app AND alembic) must disable asyncpg statement caches under pgbouncer (`pgbouncer_connect_args`). Alembic forgetting it crashed every redeploy.
3. Source-connect pins the deploy commit until a trigger push or `redeploy --from-source` — push code fixes before connecting.
4. Railway CLI/API resolve `${{Service.VAR}}` references at write time; dashboard variable editor is the only way to create reference edges.
5. `railway volume -s <name> add` panics (use service ID). `variable set --stdin` with empty stdin writes an EMPTY value. `$`-containing values must go via `--stdin`.
6. `railway run`/`shell` run locally; in-container execution = `railway ssh` (register a key: `railway ssh keys add`; one key per Railway account).
7. Railway cron services tick-redeploy from the pinned source commit; a stale pin rebuilds stale (broken) code every 5 min.
8. `SERVER_RESET_QUERY=DISCARD ALL` on pgbouncer prevents prepared-statement pollution of pooled server connections.

## Secrets

- All prod secrets live only in Railway env (backend/cron/frontend services) — nothing in git, logs, or docs.
- `RAILWAY_TOKEN` lives only as the GitHub `production` environment secret.
- Local notes during the build lived in `/tmp/portfolio-sid-v2/` (chmod 700) — deleted after completion.

## Cutover

- Old project `awake-success` was already deleted before this build — nothing to tear down.
- Cloudflare: registrar + DNS only. CNAMEs: apex → `btelnw4p.up.railway.app` (verification), admin → `ye3ffi48.up.railway.app` (verification); Railway verification TXT records added then removed after ACTIVE (user action, 2026-09-02).

## Restore drill (restore-procedure.md §3)

See "Restore drill" section at the bottom — result recorded after execution.

## DoD checklist (final)

- [x] All 4 code services deploy from a GitHub push (native trigger) — SUCCESS
- [x] CI fallback `workflow_dispatch` deploys all 4 (token verified against portfolio-sid-v2)
- [x] backend: Uvicorn 8080, alembic clean single head, zero prepared-statement/auth errors, no public domain
- [x] cron: `*/5` running, `promoted …` through pgbouncer
- [x] pgbouncer: 6432, transaction, scram, DISCARD ALL — connections visible in Postgres dashboard
- [x] admin 200 + `/api/v1/health` 200 (+ self-heals across backend restarts)
- [x] frontend `check_ssr.sh --all` 13/13, `/api/v1/health` 200, backend direct = private
- [x] `NEXT_PUBLIC_INDEXABLE=false` · `CORS_ALLOW_ORIGINS` empty · no secrets in git
- [x] custom domains SSL green on both hostnames · Cloudflare CNAMEs updated
- [x] seed: 6 resumes / 14 timeline / 6 overview (+ PDF download 200)
- [x] restore drill executed and recorded · docs updated (`conventions.md`, `env-vars-registry.md`, `LOCAL.md`)
