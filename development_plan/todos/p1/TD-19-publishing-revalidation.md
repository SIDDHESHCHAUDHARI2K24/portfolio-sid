# TD-19: Publishing & Revalidation — Route, Triggers, Scheduler Cron, public_filter Enforcement

**Phase:** P1 · **Wave:** 5 · **Executor:** agent · **Effort:** L (2–3 days)
**Source:** development-plan-P1.md → P1.T4 (S1–S4)
**Depends on:** TD-16, TD-04 · **Blocks:** TD-20, TD-21

## Purpose
Close the loop between an admin write and the public page: the revalidation
webhook, post-commit triggers, the scheduled-publish cron, and structural
draft-leak protection on every public read path.

## Paths
- Create: `frontend/src/app/api/revalidate/route.ts`, `backend/app/core/revalidation.py`, `backend/app/jobs/scheduler.py`, `backend/tests/helpers/leak_check.py`
- Modify: `docs/conventions.md` (5-min latency note), backend app factory (scheduler wiring)

## Steps
1. `route.ts`: POST with a shared secret in a header, compared timing-safe (`crypto.timingSafeEqual`); body carries tags; call `revalidateTag(tag)` for each — tags, not paths: a tag invalidates every page consuming that data, whereas paths must be enumerated and will be forgotten; invalid secret → 401 (an unauthenticated revalidation endpoint is a cheap DoS vector)
2. `core/revalidation.py`: `revalidate(tags)` helper invoked from feature service layers rather than routers, so admin API and the scheduler share one path; fire **after commit, never inside the transaction** — revalidating a change that then rolls back publishes a lie; failures log at error level but never fail the write: the content is saved and correct, only the cache is stale (silent failure here is exactly the "edits don't work" trap)
3. `jobs/scheduler.py`: iterate the models registry — never a hardcoded list — querying every publishable model for `status == SCHEDULED AND publish_at <= now()`, setting `status = PUBLISHED` and `published_at = now()`, then revalidating affected tags; idempotent — a second run within the same minute is a no-op with no repeated revalidation. The cron service provisioned in TD-M4 becomes real here
4. `docs/conventions.md`: the scheduler runs every 5 minutes → up to 5 minutes of latency against the scheduled time; acceptable for a portfolio, stated so it is never mistaken for a bug
5. Leak enforcement: reusable test helper asserting any public endpoint excludes draft and future-scheduled records, applied per feature in Phase 2; prefer a shared base repository whose public read method applies `public_filter` by default, so a feature opts *out* rather than remembering to opt in
6. Tag names come from shared constants (backend constants + `frontend/src/lib/cacheTags.ts`, landed in TD-21) — never duplicated string literals; a mismatched tag means revalidation silently does nothing

## Tests
- Valid secret triggers revalidation; invalid secret → 401; missing secret → 401; a fetch tagged `timeline` returns fresh data after a call
- Revalidation fires after commit; simulated webhook failure logs an error and the write still persists
- Entry scheduled for the past is published on the next scheduler run; future-scheduled entries untouched; repeated runs cause no duplicate work or repeated revalidation
- Leak helper: public reads exclude drafts and future-scheduled rows; admin endpoints see everything
- Scheduler iterates the registry: a scratch publishable model registered in the registry is picked up without scheduler code changes

## Environment
- `REVALIDATION_SECRET` — same value in backend env and frontend env; Railway production + local `.env` (gitignored)
- `FRONTEND_URL` — base URL the backend calls `POST /api/revalidate` on (localhost:3000 in dev)

## Acceptance Criteria
- [ ] Creating an entry in admin surfaces it publicly within seconds
- [ ] Webhook failure logs an error and does not roll back the write
- [ ] Scheduler is registry-driven and idempotent
- [ ] Leak test helper present, passing, and reusable by Phase 2 features
- [ ] 5-minute scheduling latency documented in `conventions.md`

## Verify
`uv run pytest backend/tests/publishing -q && uv run python -m app.jobs.scheduler --once` (docker Postgres up; frontend `npm run dev` for the webhook round-trip)

## Commit
`feat(publishing): revalidate route, post-commit triggers, scheduler cron, leak guard`

## Invariants
- Revalidate after commit, never in-transaction
- Tags, not paths; tag constants shared between backend and `frontend/src/lib/cacheTags.ts` — never string literals in two places
- The scheduler iterates the models registry — a feature that forgets to register would otherwise never publish on schedule
- `public_filter` is the only sanctioned public read path; leaking a draft is the failure this card exists to make structurally hard
