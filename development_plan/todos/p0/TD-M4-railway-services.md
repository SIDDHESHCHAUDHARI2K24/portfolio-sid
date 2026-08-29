# TD-M4: Railway — Postgres + Backend/Frontend/Cron Services

**Phase:** P0 · **Wave:** 4 · **Executor:** paired (user: provisioning + secret values; agent: config, deploys, verification) · **Effort:** M (half day)
**Source:** development-plan-P0.md → P0.T2.S1, P0.T2.S2, P0.T2.S3, P0.T2.S4, P0.T4.S7
**Depends on:** TD-09, TD-M2 · **Blocks:** TD-M5, TD-M6

## Purpose
The production runtime: Postgres 16, the combined admin+API backend, the
Next.js frontend, and the scheduler cron. Env wiring follows the registry;
CORS_ALLOW_ORIGINS ships explicitly empty as a deliberate security posture.

## Paths
- Reference: `backend/Dockerfile` (TD-09), `frontend/Dockerfile` (TD-04 standalone), `development_plan/handoff/env-vars-registry.md`
- Modify: `docs/conventions.md` (Postgres backup policy)

## Steps
1. User: create the Railway project; add a PostgreSQL 16 instance; confirm the backup policy for the plan and document it in `docs/conventions.md` (if backups are not automatic, gap G12 requires a weekly pg_dump cron to R2 — schedule as a follow-up); note internal and public connection URLs
2. Agent: railway CLI is already logged in; `railway link` to the project
3. User+agent: create the backend service from `backend/Dockerfile`, root directory set so the build context covers both `backend/` and `admin/`
4. Wire backend env vars per the registry: DATABASE_URL (internal URL), R2_ACCESS_KEY_ID/R2_SECRET_ACCESS_KEY/R2_ENDPOINT_URL/R2_BUCKET, RESEND_API_KEY, TURNSTILE_SECRET_KEY, SESSION_SECRET, ADMIN_PASSWORD_HASH, CF_ACCESS_ENABLED=false (until TD-M6), and CORS_ALLOW_ORIGINS **explicitly empty**
5. Frontend service from `frontend/Dockerfile`; set NEXT_PUBLIC_API_BASE_URL to the backend URL; runs `next start` against the standalone output (never static export)
6. Cron service: reuses the backend image with start command `uv run python -m app.jobs.scheduler`, scheduled every 5 minutes; P0 stub logs and exits 0 (real publishing logic lands in Phase 1)
7. User: place all secret values in Railway service env vars (never git)
8. Agent: `railway up --service <name>` per service; watch deploy logs

## Tests
- `curl -s https://<backend-public>/health` returns 200 `{"status":"ok"}`
- `curl -s https://<frontend-public>/` returns SSR HTML containing page content (no JS execution)
- Railway logs show the cron service executing every 5 minutes and exiting 0
- Backend environment shows CORS_ALLOW_ORIGINS empty

## Acceptance Criteria
- [ ] Postgres 16 reachable — internal URL from services, public URL for local Alembic; backup policy documented
- [ ] /health returns 200 on the backend public URL
- [ ] Frontend curl returns content-bearing SSR HTML
- [ ] Cron runs on schedule, visible in logs; CORS_ALLOW_ORIGINS empty in production

## Verify (agent)
`railway status && curl -s https://$BACKEND_PUBLIC_URL/health && bash scripts/check_ssr.sh https://$FRONTEND_PUBLIC_URL`

## Commit
`chore(infra): Railway services — postgres, backend, frontend, cron wired`

## Invariants
- Internal DATABASE_URL for service-to-service traffic; public URL only for local Alembic runs
- CORS_ALLOW_ORIGINS empty in production is a security posture, not an oversight — admin and API are same-origin by construction
- Railway's filesystem is ephemeral: ISR cache discarded on deploy is expected behaviour, not a fault
- pgbouncer deliberately excluded (tech-stack-analysis §6.1)

> **Cloudflare removal (2026-08-29):** R2/Turnstile/Access dropped. Add `STORAGE_KIND=local`, `LOCAL_STORAGE_DIR`, `MEDIA_BASE_URL`; frontend uses Railway native Next.js preset. See `docs/handoff/HANDOFF-CLOUDFLARE-REMOVAL-PLAN.md`.
