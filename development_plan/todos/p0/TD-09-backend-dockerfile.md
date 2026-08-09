# TD-09: Multi-Stage Backend Dockerfile (Admin + API, One Container)

**Phase:** P0 · **Wave:** 2 · **Executor:** agent · **Effort:** M (4 hrs)
**Source:** development-plan-P0.md → P0.T3.S7
**Depends on:** TD-03, TD-05 · **Blocks:** TD-14, TD-M4

## Purpose
FastAPI serves both the API and the built admin SPA from one container on one
origin. Mount order is the trap: routers first, StaticFiles last — static
mounted first shadows every API route with 404s and no obvious cause.

## Paths
- Create: `backend/Dockerfile`, `.dockerignore`
- Modify: `backend/app/app.py` (static mount + SPA catch-all)

## Steps
1. Stage 1 `node:20-alpine`: COPY `admin/`, then `npm ci && npm run build`
2. Stage 2 `python:3.12-slim`: install uv, COPY `backend/`, `uv sync --frozen`
3. `COPY --from=0 /admin/dist ./static`
4. In `create_app()`: register ALL API routers FIRST (`/api/v1` prefix, including `/api/v1/health`), THEN mount `StaticFiles(directory="static", html=True)` at `/` LAST; keep the root `/health` liveness route registered before the static mount
5. Add a catch-all returning `static/index.html` for unmatched non-`/api` paths so client-side routing survives refresh
6. Build from the repo root (Railway's root dir covers backend+admin): `docker build -f backend/Dockerfile -t portfolio-backend .`
7. Run the container with TD-06 compose env values and exercise every route class

## Tests
- `docker build -f backend/Dockerfile .` succeeds from the repo root
- `curl localhost:8000/` returns the admin SPA HTML; `curl localhost:8000/api/v1/health` returns 200 JSON
- `curl localhost:8000/some/deep/admin/route` returns index.html (SPA), not a 404

## Acceptance Criteria
- [ ] `docker build` succeeds from the repo root
- [ ] Container serves the admin UI at `/` and the API at `/api/v1/health`
- [ ] Refreshing a deep admin route returns the SPA, not a 404
- [ ] `/health` liveness route responds outside the static mount

## Verify
`docker build -f backend/Dockerfile -t portfolio-backend . && curl -s localhost:8000/api/v1/health && curl -sI localhost:8000/deep/admin/route`

## Commit
`feat(backend): multi-stage Dockerfile — admin SPA served by FastAPI`

## Invariants
- Routers registered BEFORE the StaticFiles mount — mount order determines precedence
- Admin SPA + API share one hostname in production (single Access app, TD-M6)
- Accepted coupling: any admin change rebuilds and redeploys the API container
