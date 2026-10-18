# E04-W4: Deploy ordering — backend before frontend

**Epic:** E04 CI/CD hardening · **Ticket:** E04-W4 · **Depends on:** W2, W3

## Purpose

All services rebuild on every push and deploy in parallel, so the frontend can prerender against a restarting backend (EPIC finding F2).

## Goal

The frontend never builds against a backend that is mid-restart, or survives it when it does.

## Decision (user, 2026-10-18): Option A

**Option A, recommended: watch paths plus W2's retry.**
- `frontend` rebuilds only on `frontend/**`; `admin` only on `admin/**`; `backend` and `cron` on `backend/**` and `Dockerfile`.
- Most pushes then touch one app, so there is no race. When backend and frontend both change, W2's retry covers the restart window.
- Small change, stays on native deploys.

**Option B: GitHub-driven ordered deploy.**
- Disable native triggers; `deploy.yml` runs on `workflow_run` after CI succeeds on `main`.
- Order: backend, wait for SUCCESS, health check; then frontend, admin and cron in parallel; then W5's smoke.
- Strict ordering, but deploys depend on the `RAILWAY_TOKEN` secret and on `railway up` uploads, and every deploy rebuilds every service.

## Reference files

- `.railway/railway.ts`
- `.github/workflows/deploy.yml`
- `docs/DEPLOYMENT.md`

## Functionality (Option A)

- Add watch patterns per service in `railway.ts`, if the IaC SDK supports them. If it does not, stop and ask: setting them in the dashboard may be wiped by the next `config apply` ("omitted means deleted").
- Patterns: backend and cron `["backend/**", "Dockerfile"]`; frontend `["frontend/**"]`; admin `["admin/**"]`.
- Changes outside these paths (docs, workflows, `.railway/`) deploy nothing.

## Edge cases

- A shared change (e.g. regenerated `openapi.json` plus both `api.d.ts` files) rebuilds all three apps; W2 covers it.
- `frontend` uses `rootDirectory: "/frontend"`; confirm whether patterns are relative to the repo root or the root directory, from the Railway docs.
- A docs-only push deploys nothing, which is intended.

## Testing

- Config plan shows only watch-pattern changes.
- After apply: a docs-only push deploys nothing; a frontend-only push deploys only `frontend`.

## Acceptance criteria

- [x] The user has chosen A (2026-10-18).
- [ ] (A) Watch patterns applied with approval; the two pushes above behave as stated.
- [ ] (B) `deploy.yml` deploys in order after CI; native triggers disabled; one full ordered deploy succeeds.
- [ ] `docs/DEPLOYMENT.md` describes the chosen flow.

## Rollback

(A) Remove the patterns and re-apply. (B) Re-enable native triggers and revert `deploy.yml`.
