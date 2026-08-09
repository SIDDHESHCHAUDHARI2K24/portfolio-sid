# TD-07: Async Alembic + Models Registry

**Phase:** P0 · **Wave:** 2 · **Executor:** agent · **Effort:** M (4 hrs)
**Source:** development-plan-P0.md → P0.T3.S3
**Depends on:** TD-03, TD-06 · **Blocks:** TD-13, TD-16

## Purpose
Alembic's default env.py is synchronous and fails against an async engine.
Every migration in every later phase inherits this configuration, and the
models registry prevents the classic silently-empty autogenerate.

## Paths
- Create/modify: `backend/alembic.ini`, `backend/alembic/env.py`, `backend/alembic/versions/`
- Modify: `backend/app/core/models_registry.py` (from TD-03 skeleton)

## Steps
1. `cd backend && uv run alembic init alembic`
2. `alembic.ini`: leave `sqlalchemy.url` blank — env.py reads DATABASE_URL from Settings (asyncpg URL)
3. Rewrite `alembic/env.py` with the async pattern:
   - Import `app.core.models_registry` BEFORE any metadata access
   - `target_metadata = Base.metadata` (Base from `app.core.database`)
   - `run_migrations_online()`: `connectable = async_engine_from_config(config.get_section(config.config_ini_section, {}), prefix="sqlalchemy.", poolclass=pool.NullPool)`; inside an `async def do_run_migrations(connection)` call `connection.run_sync(context.run_migrations)`; drive it with `asyncio.run()`
   - `context.configure(..., compare_type=True)`
4. `app/core/models_registry.py` imports every feature's models module; feature slices append their imports here as they land (empty registry + Base in P0)
5. Add a temporary scratch model (e.g. `app/features/scratch/models.py`) registered in the registry to prove autogenerate
6. `uv run alembic revision --autogenerate -m "scratch"` — the revision MUST be non-empty
7. `uv run alembic upgrade head` against the TD-06 docker Postgres; confirm the table via `docker compose exec postgres psql -U portfolio -c '\dt'`
8. Delete the scratch model and its migration; final state is a clean single head

## Tests
- Autogenerate for the scratch model produces a non-empty revision
- `uv run alembic heads` returns exactly one head
- `upgrade head` / `downgrade base` round-trip against docker Postgres

## Acceptance Criteria
- [ ] `uv run alembic upgrade head` succeeds against local docker Postgres
- [ ] `uv run alembic revision --autogenerate` produces a non-empty migration for the scratch model
- [ ] `uv run alembic heads` returns exactly one head
- [ ] `compare_type=True` active; models_registry imported in env.py

## Verify
`cd backend && uv run alembic heads && uv run alembic upgrade head`

## Commit
`feat(backend): async Alembic — run_sync env.py pattern, models registry`

## Invariants
- Every feature's models import through `app/core/models_registry.py` — unimported models are invisible to autogenerate
- Migrations: rebase on main + regenerate; never hand-edit `down_revision`; single head enforced in CI (TD-13)
- DB verification via `docker compose exec postgres psql` only (no local psql)
