# Handoff — Steady State (2026-09-03)

**Status:** `portfolio-sid-v2` fully deployed and healthy. All DoD gates green. This doc is the new-session entry point; `docs/DEPLOYMENT.md` is the deployment troubleshooting bible.

## Current state

- Railway project `portfolio-sid-v2` (`e0f5e770-6a95-41aa-99e4-3be94884d6ca`, production `a6f89029-ec4a-46a7-9950-84dbfb3d4fc6`). The old project `awake-success` is deleted.
- 6 services — frontend (public), admin (public), backend (private, volume `/data`), cron (private, `*/5`), pgbouncer (private, 6432), Postgres plugin (private). Full ID table in `docs/specs/portfolio-sid-v2-deployment/POST-DEPLOYMENT.md`.
- Custom domains live + SSL: `siddhesh-chaudhari.com`, `admin.siddhesh-chaudhari.com` (Cloudflare registrar+DNS only).
- Content seeded: 6 resumes / 14 timeline / 6 overview (+ PDFs on the volume).
- All Postgres traffic flows backend/cron → pgbouncer:6432 → Postgres:5432.
- Restore drill PASS (recorded in `docs/conventions.md` §Postgres backup policy; server is Postgres 18).

## Deploy mechanisms (all three verified)

1. **Push to `main`** → native Railway GitHub triggers deploy all 4 code services (Postgres/pgbouncer never deploy from repo).
2. **CI fallback** — `gh workflow run deploy.yml -f service=all` (dispatch-only; uses the `production` environment secret `RAILWAY_TOKEN`, injected as `RAILWAY_API_TOKEN`).
3. **Infra changes** — `.railway/railway.ts` IaC (single source of truth; secrets stay on Railway via `preserve()`). Edit → `railway config plan` → `railway config apply`.

## Key docs

- `docs/DEPLOYMENT.md` — architecture, env map, build matrix, troubleshooting guide (read FIRST for any deployment issue)
- `docs/specs/portfolio-sid-v2-deployment/DESIGN.md` (decisions D1–D13) · `PLAN.md` (gotchas) · `POST-DEPLOYMENT.md` (results)
- `docs/conventions.md` — invariants #1–#15 (architectural contract)
- `docs/handoff/env-vars-registry.md` — env var reference (incl. pgbouncer service, `NEXT_PUBLIC_BASE_URL`, `PUBLIC_API_PROXY`, `BACKEND_UPSTREAM`)

## Open items (future sessions)

- Flip `NEXT_PUBLIC_INDEXABLE=true` only after launch verification (invariant #13) — user decision.
- Umami analytics (`NEXT_PUBLIC_UMAMI_*`) — deferred.
- Untracked local files: `doctor.config.ts`, `.agents/`, `.claude/`, `.openhands/` — react-doctor hook prints a warning on every commit ("configuration differs between index and worktree"); harmless but noisy. Resolve or gitignore.
- Dashboard canvas: variable-reference edges were created via IaC — confirm they render (cosmetic only).
- Contact content editing — **LIVE** (`backend/app/features/contact/` singleton profile, seeded by migration `cc8619b8d037`, public `GET /api/v1/contact`, admin `GET/PUT /api/v1/admin/contact`, admin → Contact sidebar form). Edits revalidate the `contact` cache tag; the `/contact` page falls back to inline defaults if the row is missing.

## Secrets

- Everything in Railway env vars / gh `production` environment secret / local gitignored `backend/.env`. Never in git, logs, or docs.
- The admin portal password was generated fresh during this deployment and shown once in session chat; reset path = `uv run python -m app.cli hash-password "<new>"` + update `ADMIN_PASSWORD_HASH` on the backend service.
