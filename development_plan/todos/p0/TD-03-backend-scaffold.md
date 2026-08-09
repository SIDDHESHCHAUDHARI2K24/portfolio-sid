# TD-03: Backend Scaffold — uv + FastAPI Factory + core/

**Phase:** P0 · **Wave:** 1 · **Executor:** agent · **Effort:** L (1 day)
**Source:** development-plan-P0.md → P0.T3.S2
**Depends on:** TD-00 · **Blocks:** TD-07, TD-08, TD-09, TD-12, TD-16

## Purpose
Feature-sliced FastAPI skeleton with the app factory and the `core/` module
every feature slice imports from. `core/` interfaces are the one change that
ripples across all of Phase 2 — get them right while the codebase is empty.

## Paths
- Create: `backend/pyproject.toml`, `backend/uv.lock`, `backend/.env.example`,
  `backend/app/app.py`, `backend/app/core/{config,database,storage,security,deps}.py`,
  `backend/app/core/models_registry.py`, `backend/app/features/` (empty),
  `backend/app/tests/test_health.py`

## Steps
1. `uv init backend/` (Python 3.12); then `uv add fastapi uvicorn sqlalchemy asyncpg alembic pydantic-settings python-multipart argon2-cffi pyjwt itsdangerous slowapi resend boto3`
2. `uv add --dev pytest pytest-asyncio httpx ruff mypy`
3. `app/core/config.py`: `pydantic-settings` `Settings` reading env vars — DATABASE_URL, R2_*, RESEND_API_KEY, TURNSTILE_SECRET_KEY, SESSION_SECRET, ADMIN_PASSWORD_HASH, CORS_ALLOW_ORIGINS, CF_ACCESS_ENABLED
4. `app/core/database.py`: async engine + session factory over asyncpg; declarative `Base`; `get_db` dependency
5. `app/core/storage.py`, `security.py`, `deps.py`: skeletons only — real logic lands in TD-08 / TD-17
6. `app/app.py`: `create_app() -> FastAPI` factory; `/health` returns `{"status":"ok"}`; CORS middleware driven by CORS_ALLOW_ORIGINS (empty list = same-origin only)
7. `backend/pyproject.toml`: ruff lint+format config and mypy **strict** — strict is free against an empty codebase, enable it now rather than retrofitting
8. `backend/.env.example`: every Settings field with safe dev placeholders, matching TD-06 compose values
9. Smoke test `app/tests/test_health.py` via httpx AsyncClient
10. Run locally: `uv run uvicorn app.app:create_app --factory --reload`

## Tests
- `uv run pytest` — health test green
- `uv run ruff check && uv run ruff format --check && uv run mypy app` — clean

## Acceptance Criteria
- [ ] `uv run uvicorn app.app:create_app --factory` starts locally
- [ ] `GET /health` returns 200 `{"status":"ok"}`
- [ ] ruff check, ruff format --check, and mypy strict all pass on the skeleton
- [ ] `.env.example` covers every Settings field; no real secret anywhere

## Verify
`cd backend && uv run pytest && uv run ruff check && uv run mypy app`

## Commit
`feat(backend): uv scaffold — FastAPI factory, core/, strict ruff+mypy`

## Invariants
- `core/` is the only shared surface; feature slices never import each other
- boto3 only in `core/storage.py` (TD-08)
- Secrets via env vars only: `.env` gitignored, `.env.example` committed
- CORS_ALLOW_ORIGINS must ship empty in production (TD-M4)
