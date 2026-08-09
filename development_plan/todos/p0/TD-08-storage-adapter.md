# TD-08: StorageAdapter — R2/MinIO, Content-Hashed Keys

**Phase:** P0 · **Wave:** 2 · **Executor:** agent · **Effort:** M (4 hrs)
**Source:** development-plan-P0.md → P0.T3.S4
**Depends on:** TD-03, TD-06, TD-M2 · **Blocks:** TD-M4 (storage env wiring), Phase 2 media pipelines

## Purpose
One abstraction so R2, MinIO, and local development are a config change
rather than a refactor. Content-hashed keys make cached media immune to
staleness; the immutable cache header makes that safe at the edge.

## Paths
- Modify: `backend/app/core/storage.py` (skeleton from TD-03)
- Create: `backend/app/tests/test_storage.py`
- Reference: `backend/.env.example` STORAGE_* vars; R2 credentials via Railway (TD-M2 registry)

## Steps
1. Abstract base `StorageAdapter` in `app/core/storage.py`: `put(key, data, content_type)`, `get_url(key)`, `delete(key)`, `exists(key)`
2. One `S3Storage(StorageAdapter)` implementation via boto3 with configurable `endpoint_url` — the same code serves R2 (`https://<account-id>.r2.cloudflarestorage.com`) and MinIO (`http://localhost:9000`)
3. `put()` sets `ContentType` and `Cache-Control: public, max-age=31536000, immutable`
4. Key helper: content-hashed keys, pattern `<dir>/<name>-<sha256[:12]>.<ext>` (e.g. `certs/aws-sa-3f9a1b2c4d5e.pdf`) — replacing a file changes its URL, so the edge cache can never serve a stale version
5. Factory `get_storage()` selecting the implementation from Settings; expose it as a FastAPI dependency in `core/deps.py`
6. Tests against TD-06 MinIO: upload/download/exists/delete round-trip; assert the immutable header via `docker compose exec minio mc stat local/portfolio-media/<key>`; assert different content produces a different key
7. R2 parity check once TD-M2 credentials exist: the same suite passes with only STORAGE_* env changes

## Tests
- `uv run pytest app/tests/test_storage.py` green against local MinIO
- `mc stat` output shows `Cache-Control: public, max-age=31536000, immutable`
- `git grep -n "boto3" backend/app -- ':!backend/app/core/storage.py'` returns nothing

## Acceptance Criteria
- [ ] Uploads against local MinIO and against R2 both succeed with only an env change
- [ ] Uploaded objects carry the immutable cache header
- [ ] Replacing content produces a different key
- [ ] Nothing outside `core/storage.py` imports boto3

## Verify
`cd backend && uv run pytest app/tests/test_storage.py && git grep -n "boto3" backend/app`

## Commit
`feat(backend): StorageAdapter — S3-compatible R2/MinIO, content-hashed keys`

## Invariants
- boto3 only in `core/storage.py`; feature slices consume the adapter dependency
- Keys embed content hashes; published URLs are immutable
- R2 credentials live in Railway env vars (registry references only), never git
