# TD-06: Docker Compose — Postgres 16 + MinIO + Bucket Init

**Phase:** P0 · **Wave:** 1 · **Executor:** agent · **Effort:** S (2 hrs)
**Source:** development-plan-P0.md → P0.T3.S8
**Depends on:** TD-00 · **Blocks:** TD-07, TD-08

## Purpose
Local Postgres and MinIO so development matches production storage semantics
via the same S3 API. The bucket-creation init container prevents the
confusing first-upload failure when the bucket does not yet exist.

## Paths
- Create: `docker-compose.yml` at repo root
- Reference: `backend/.env.example` (TD-03) — credentials must match compose values

## Steps
1. `postgres:16-alpine` service: named volume `pgdata:/var/lib/postgresql/data`, POSTGRES_USER/POSTGRES_PASSWORD/POSTGRES_DB env, port 5432:5432, healthcheck `pg_isready`
2. `minio/minio` service: command `server /data --console-address ":9001"`, ports 9000 (S3 API) and 9001 (console), named volume `miniodata:/data`, MINIO_ROOT_USER/MINIO_ROOT_PASSWORD env, healthcheck
3. `createbuckets` one-shot service: `minio/mc` image, depends on minio healthy, entrypoint `mc alias set local http://minio:9000 $MINIO_ROOT_USER $MINIO_ROOT_PASSWORD && mc mb -p local/portfolio-media`
4. Align credentials with `backend/.env.example`: DATABASE_URL `postgresql+asyncpg://portfolio:portfolio@localhost:5432/portfolio`, STORAGE_ENDPOINT `http://localhost:9000`, bucket `portfolio-media`
5. `docker compose up -d`; wait for healthchecks
6. Local Postgres access is via `docker compose exec postgres psql` — there is no local psql install, and all Alembic work targets this service

## Tests
- `docker compose ps` shows postgres + minio healthy and createbuckets completed (exit 0)
- `docker compose exec postgres psql -U portfolio -c 'select 1'` returns 1
- `docker compose exec minio mc ls local/` lists `portfolio-media`

## Acceptance Criteria
- [ ] `docker compose up -d` brings up Postgres 16 + MinIO + console
- [ ] Bucket `portfolio-media` exists on first boot (mc mb ran)
- [ ] Backend (TD-03) connects to Postgres and uploads to MinIO using `.env` values from `.env.example`

## Verify
`docker compose up -d && docker compose ps && docker compose exec postgres psql -U portfolio -c 'select 1'`

## Commit
`chore: docker compose — Postgres 16, MinIO, bucket init container`

## Invariants
- Named volumes only; no bind mounts for data
- Compose credentials are dev-only placeholders; production values live in Railway env vars
- All DB verification goes through `docker compose exec postgres psql` — no local Postgres/psql install
