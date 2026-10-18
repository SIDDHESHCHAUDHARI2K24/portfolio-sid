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

1. **Push to `main`** → native Railway GitHub triggers deploy the code services whose watch paths changed, after CI is green (E04; pending `railway config apply`; Postgres/pgbouncer never deploy from repo).
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
- Contact content editing — **LIVE v2** (`backend/app/features/contact/`): singleton `ContactProfile` (consent text) + ordered `ContactItem` list (kind/label/url/sort_order — emails, socials, booking links, phone…). Public `GET /api/v1/contact` returns `{consent_text, items}`; admin `PUT /api/v1/admin/contact` full-replaces items (array order = sort_order) and revalidates the `contact` tag. Admin → Contact sidebar form has add/remove/reorder + kind select. Frontend `/contact` renders icons per kind (brand icons inlined in `frontend/components/icons/BrandIcons.tsx` — lucide dropped brand icons) and falls back to inline defaults if the row is missing. Seeded via migrations `cc8619b8d037` → `a605878385db` (3 public emails + LinkedIn/Cal/GitHub).

## Auth hardening — Epic E01 (2026-10-17)

See `docs/epics/E01-auth/EPIC.md`. Production login was failing on a password mismatch (fixed by resetting `ADMIN_PASSWORD_HASH`). The epic then shipped:
- Real client IP: `app/core/net.client_ip` trusts `X-Real-IP` only from `TRUSTED_PROXY_CIDRS` peers (prod `["10.0.0.0/8","fd00::/8"]`, JSON list); IPv6 is keyed per /64. Admin nginx forwards the edge's `X-Real-IP`.
- A wrong password returns 400 "Incorrect password." and the admin app stays on the login page; success returns "Code sent.".
- `app.auth` / `app.core.email` INFO outcome logs (no codes, passwords, full addresses or keys).
- Production startup validation (`app/core/startup_checks.py`) blocks a deploy with bad auth env; the backend healthcheck `/api/v1/health` (IaC) keeps the old deployment serving.
- Local ports moved to the 247xx block (see `docs/epics/E01-auth/E01-W7-local-nonstandard-ports/SPEC.md`).
- graphify removed; CodeGraph is the navigation tool. `AGENTS.md` holds the agent workflow; `CLAUDE.md` imports it.
- Pre-deploy check: `docs/epics/E01-auth/transcripts/checks.sh` (gitignored, local).
- Open: optional E01-W6 (verify the Resend domain; the sandbox sender only delivers to the account owner).

## CI/CD hardening — Epic E04 (2026-10-18)

See `docs/epics/E04-cicd/EPIC.md` and `docs/DEPLOYMENT.md` §4.
- Railway waits for green CI (`checkSuites: true`) and rebuilds only services whose watch paths changed.
- The frontend build retries the API for about 90 seconds through a backend restart.
- `.github/workflows/smoke.yml` runs `scripts/smoke.sh` after each successful production deploy.
- CI builds admin; CI and E2E run on Postgres 18. `react-doctor.yml` runs advisory on pull requests.

## Secrets

- Everything in Railway env vars / gh `production` environment secret / local gitignored `backend/.env`. Never in git, logs, or docs.
- The admin portal password was generated fresh during this deployment and shown once in session chat; reset path = `uv run python -m app.cli hash-password "<new>"` + update `ADMIN_PASSWORD_HASH` on the backend service.
