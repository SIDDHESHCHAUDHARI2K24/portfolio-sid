# Epic E04: CI/CD hardening — gated, ordered, verified deploys

**Status:** Implemented on the branch 2026-10-18; awaiting `railway config apply` and merge approval
**Coordinator:** Coordinator 1 (session `fd08bb3a-b07e-4a18-a7f4-032a1fb0a404`)
**Opened:** 2026-10-18 · **Branch:** `epic/E04-cicd` in worktree `Portfolio/.worktrees/E04-cicd`

## Goal

A push to `main` reaches production only after CI is green. The frontend build survives a backend restart. Every deploy is checked automatically against the live site. CI builds what production builds, on the same Postgres major version.

## Scope

- `.railway/railway.ts`: `checkSuites: true` on every GitHub-sourced service; deploy ordering (see W4).
- `frontend/lib/api.ts`: bounded build-time retry.
- `.github/workflows/`: admin build in CI, Postgres 18 in CI and E2E, a post-deploy smoke workflow, action version bumps, a decision on `react-doctor.yml`.
- `scripts/smoke.sh`: one production smoke script shared by the smoke workflow and `deploy.yml`.
- Docs: `docs/DEPLOYMENT.md`, the steady-state handoff.

## Non-goals

- Migration rehearsal against a production snapshot (separate epic; needs a staging environment).
- Local `docker-compose.yml` Postgres 16 to 18 (needs a local dump and restore; separate ticket).
- Preview environments per pull request.
- Visual regression suites in CI (darwin baselines; tracked under TD-36).

## Findings

| # | Finding | Evidence |
|---|---------|----------|
| F1 | Railway deploys every push to `main` without waiting for CI: `checkSuites: false` on all four GitHub sources. | `.railway/railway.ts:4,80,93` |
| F2 | Every service rebuilds on every push and they deploy in parallel, so the frontend prerender can run while the backend restarts. | E03 release, 2026-10-18: frontend build failed on a 502 from `/` prerender; redeploy succeeded |
| F3 | Build-time fetches go through the public admin proxy (the builder cannot resolve `*.railway.internal`), with one fallback attempt and no retry. A 502 during a backend restart fails the build. | `frontend/lib/api.ts` `apiFetch`, `getFallbackServerBase` |
| F4 | The backend runs `alembic upgrade head` at container start, so its restart window includes migration time. | `Dockerfile:13` |
| F5 | CI never runs `vite build` for admin. The frontend `next build` runs only inside E2E. | `.github/workflows/ci.yml` admin job; `e2e.yml` build step |
| F6 | CI and E2E use `postgres:16-alpine`; production runs Postgres 18. | `ci.yml`, `e2e.yml` services |
| F7 | Nothing checks production after a native deploy. `deploy.yml` has a health gate, but only for its manual runs. | `.github/workflows/deploy.yml` `health` job |
| F8 | Actions are pinned to older majors (`checkout@v4`, `setup-node@v4`, `setup-uv@v5`, `upload-artifact@v4`). | all workflow files |
| F9 | `react-doctor.yml` is untracked; it runs on push to `main` and would add a check suite that W3's gate waits for. | `git status` |

## Work items

| ID | Title | Depends on |
|----|-------|-----------|
| [E04-W1](E04-W1-ci-builds-and-postgres18/SPEC.md) | CI builds admin; CI and E2E on Postgres 18 | none |
| [E04-W2](E04-W2-frontend-build-resilience/SPEC.md) | Frontend build retries the API through a backend restart | none |
| [E04-W3](E04-W3-gate-deploys-on-ci/SPEC.md) | Gate Railway deploys on green CI (`checkSuites: true`) | W1, W6 merged |
| [E04-W4](E04-W4-deploy-ordering/SPEC.md) | Deploy ordering: backend before frontend | W2, W3 |
| [E04-W5](E04-W5-post-deploy-smoke/SPEC.md) | Automatic post-deploy smoke check | none (trigger depends on W4 choice) |
| [E04-W6](E04-W6-workflow-maintenance/SPEC.md) | Action version bumps; `react-doctor.yml` decision | none |

W1, W2, W5 and W6 can run in parallel. W3 lands after W1 and W6, so the gate waits on the final set of checks. W4 lands last.

## Decisions (user, 2026-10-18)

1. **W4 ordering:** Option A, Railway watch paths plus W2's build-time retry. Native deploys stay.
2. **W6 `react-doctor.yml`:** commit it advisory-only, pinned, on pull requests only (no `push` trigger).

## Acceptance criteria

1. A push to `main` with a failing CI job deploys nothing on Railway.
2. A push to `main` with green CI deploys every changed service.
3. A frontend build started while the backend restarts succeeds, or fails only after the bounded retry with a clear log line.
4. Within 15 minutes of a production deploy, a GitHub run reports pass or fail for backend health and the key pages.
5. CI runs `vite build` for admin; CI and E2E run on `postgres:18-alpine`.
6. No workflow uses a deprecated action major; `react-doctor.yml` is committed or deleted.
7. `docs/DEPLOYMENT.md` and the steady-state handoff describe the new pipeline.

## Verification plan

- Branch: every workflow change runs on the epic's pull request (CI, E2E, react-doctor if kept).
- Local: `npm run lint && npm test && npm run build` in `frontend/` with the backend stopped mid-build (W2); `scripts/smoke.sh` against production (read-only GETs).
- Production (user-approved): `railway config apply` for W3 and W4; one push with green CI that deploys; observe the smoke run. Gate test: a deliberately red commit on a throwaway branch is not enough (Railway watches `main` only), so the gate is verified from Railway's UI showing "Waiting for CI" on the next real push.

## Sessions

- Coordinator 1: `fd08bb3a-b07e-4a18-a7f4-032a1fb0a404`
