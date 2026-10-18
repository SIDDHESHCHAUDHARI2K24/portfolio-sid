# E04-W1: CI builds admin; CI and E2E on Postgres 18

**Epic:** E04 CI/CD hardening · **Ticket:** E04-W1 · **Depends on:** none

## Purpose

CI type-checks and lints admin but never builds it, so a Vite build failure reaches Railway first. CI tests against Postgres 16 while production runs 18.

## Goal

The CI admin job builds the bundle. CI and E2E run migrations and tests on the production Postgres major.

## Reference files

- `.github/workflows/ci.yml` (`admin` job, `backend` service)
- `.github/workflows/e2e.yml` (service image, `npm run build` step)
- `admin/package.json` (`build: tsc -b && vite build`)

## Functionality

- Admin job: replace the separate `npx tsc --noEmit` step with `npm run build` (it runs `tsc -b` then `vite build`). Keep `npm run lint`.
- Frontend: no new build step. E2E already runs `npm run build` on every push to `main` and on pull requests touching `frontend/**` or `backend/**`, against a seeded backend. A second build in CI without a backend would fail prerender. Decision recorded here.
- Postgres: `postgres:16-alpine` becomes `postgres:18-alpine` in both workflows. Ports, credentials and health checks stay.

## Edge cases

- Postgres 18 images moved `PGDATA` to `/var/lib/postgresql/18/docker`. Service containers have no volumes, so this does not apply in CI.
- Postgres 18 enables data checksums by default and changes some defaults; any test that depended on 16 behaviour must be fixed, not pinned back.
- `tsc -b` uses project references; confirm it covers the same files as `tsc --noEmit` did.

## Testing

- The epic pull request runs CI and E2E green on Postgres 18.
- Break an admin import locally and confirm `npm run build` fails, then revert.

## Acceptance criteria

- [x] CI admin job runs `npm run build` and passes.
- [x] `ci.yml` and `e2e.yml` use `postgres:18-alpine`; backend tests, alembic single-head and E2E pass.
- [x] `docs/DEPLOYMENT.md` CI section lists the admin build and Postgres 18.

## Rollback

Revert the commit. Nothing outside GitHub Actions changes.
