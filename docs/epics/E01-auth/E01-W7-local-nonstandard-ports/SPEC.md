# E01-W7 — Non-standard local ports

**Epic:** E01 Auth · **Ticket:** E01-W7 · **Status:** Ready · **Depends on:** none (unblocks local verification of W2–W5)

## Purpose
Local services bind standard ports (5432, 6432, 9000/9001, 8000, 3000, 5200), which collide with other projects on the same machine. This was found when another project's MinIO held port 9000 and the storage tests failed (user request, 2026-10-17).

## Goal
Every host port this project binds locally sits in a dedicated `247xx` block, so it can run alongside other projects.

## Port map (local host ports only)
| Service | Old | New |
|---|---|---|
| Frontend (Next dev/start) | 3000 | 24730 |
| Postgres (direct) | 5432 | 24732 |
| pgbouncer | 6432 | 24733 |
| Admin (Vite dev) | 5200 | 24752 |
| Backend (uvicorn dev) | 8000 | 24780 |
| MinIO API | 9000 | 24790 |
| MinIO console | 9001 | 24791 |

## Reference files
- `docker-compose.yml` (host side of each port mapping only; container ports stay)
- `backend/app/core/config.py` (`database_url` default and comments), `backend/app/core/database.py` (comments), `backend/.env.example`
- `backend/app/tests/test_storage.py` (`MINIO_PORT`), `backend/app/tests/test_pgbouncer_config.py`
- `admin/vite.config.ts` (dev server port and `/api` proxy target), `admin/.env.example`
- `frontend/package.json` (dev/start port), `frontend/.env.example`, `frontend/next.config.ts` (image `remotePatterns`), `frontend/playwright.config.ts`, `frontend/tests/journeys/critical.spec.ts`
- `frontend/app/robots.ts`, `sitemap.ts`, `llms.txt/route.ts`, `contact/page.tsx`, `frontend/lib/jsonld.ts` (`localhost:3000` fallbacks)
- `scripts/check_ssr.sh`, `.github/workflows/e2e.yml`, `.github/workflows/ci.yml`
- `docs/handoff/env-vars-registry.md`, `frontend/README.md`

## Functionality
- Change only local host ports. Production is unchanged: Railway `$PORT`, `pgbouncer.railway.internal:6432`, the Dockerfile `${PORT:-8000}`, nginx, `.railway/railway.ts`.
- Container-internal ports stay (`postgres:5432`, `minio:9000`, `DB_PORT: 5432`, the healthcheck).
- CI: keep the service containers on their internal ports, but update host and URL references so the e2e job starts backend and frontend on the new ports, consistent with `playwright.config.ts`.

## Edge cases
- Existing developer `.env` files still point at the old ports. Document the change in `.env.example`; never edit a real `.env`.
- Existing Docker volumes keep their data; only the mappings change, so `docker compose up -d` recreates the containers.
- Backend `cors_allow_origins` examples must use the new frontend and admin ports.
- `NEXT_PUBLIC_BASE_URL` / `next_public_base_url` defaults move to `http://localhost:24730`.
- `LOCAL.md` is an untracked user file. Do not edit it; the coordinator gets the user's approval first.

## Testing
- `docker compose up -d`: all containers healthy on the new ports, with no bind errors while the other projects are running.
- Backend: `uv run ruff check app && uv run mypy app && uv run pytest -q`. All pass, including the storage tests against MinIO on 24790.
- Admin: `npm run lint && npm run build`. Frontend: `npm run lint && npm test && npm run build`.
- `grep` finds no remaining local-dev reference to the old ports outside the exempt production and container-internal spots.

## Acceptance criteria
- [ ] The port map is applied everywhere listed.
- [ ] The full backend suite passes locally, with no storage failures.
- [ ] Production config is untouched.

## Rollback
Revert the commit, then run `docker compose up -d`.
