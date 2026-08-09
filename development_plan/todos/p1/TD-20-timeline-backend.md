# TD-20: Timeline Backend Slice — Model → Schemas → Repository/Service → Routers → Tests

**Phase:** P1 · **Wave:** 6 · **Executor:** agent · **Effort:** L (2–3 days)
**Source:** development-plan-P1.md → P1.T5 (S1–S5)
**Depends on:** TD-16, TD-17, TD-18, TD-19 · **Blocks:** TD-21, TD-23

## Purpose
The first feature slice, end-to-end. Its shape is the template nine Phase 2
slices will copy — layout matters as much as behaviour. Timeline was chosen
as the hardest case: two record kinds merged, the most complex tag logic,
publishing states, and admin CRUD in one slice.

## Paths
- Create: `backend/app/features/timeline/` — `models.py`, `schemas.py`, `repository.py`, `service.py`, `router.py`
- Modify: `backend/app/core/models_registry.py` (one import line), new migration, app factory (register routers)

## Steps
1. `TimelineEntry` inheriting `UUIDMixin`, `TimestampMixin`, `SortableMixin`, `PublishableMixin`: `kind` (`EDUCATION`/`EXPERIENCE`), `title`, `organisation`, `location`, `start_date`, `end_date` (nullable — null means current), `summary` (markdown), `highlights` (JSONB array of strings), `external_url`, `audience_override` (array of audience enum), many-to-many to `TopicTag`; index `(start_date DESC)`. One model, not two — the kinds differ only in labels and render identically in one chronological list; separate models would mean union queries and duplicated tag/publishing logic
2. Schemas (Pydantic v2, `model_config = ConfigDict(from_attributes=True)`): `TimelineEntryPublic` (omits status, `publish_at`, overrides — never return the admin schema from a public endpoint), `TimelineEntryAdmin` (everything), `TimelineEntryCreate`, `TimelineEntryUpdate` (all optional for PATCH); model validator enforcing `end_date >= start_date`
3. `repository.py`: `list_public()` applies `public_filter`, `selectinload(TimelineEntry.topic_tags)` to avoid N+1, order `start_date DESC` with `sort_order` tiebreak; plus `list_admin()`, `get()`, `create()`, `update()`, `delete()`; the repository never imports FastAPI
4. `service.py`: orchestration — validation, tag attachment, and `revalidate(tags)` after every mutation via the TD-19 path
5. Routers: `/api/v1/timeline` public read-only; `/api/v1/admin/timeline` full CRUD with `dependencies=[Depends(require_admin)]` at **router level**, not per endpoint, so a new endpoint cannot be added unprotected by omission; register both in `create_app()`
6. Add the timeline models import to `models_registry.py` and confirm autogenerate sees the table

## Tests
- Query-count assertion: the list endpoint issues a constant number of queries regardless of entry count
- Full API suite (`httpx.AsyncClient` + Postgres service container): CRUD with auth assertions — every admin endpoint 401 without a session
- Draft-leak test via the shared TD-19 helper: public list excludes drafts; admin list includes them
- Scheduled entry appears publicly only after the cron runs
- Create triggers revalidation (mock the webhook, not the database)
- Invalid date range → 422 with a clear message; relevance resolution across audiences on real entries

## Acceptance Criteria
- [ ] Both kinds persist with tags and overrides; null `end_date` means current
- [ ] Migration applies and reverses cleanly; registry entry confirmed by autogenerate
- [ ] Public responses omit status, `publish_at`, and overrides
- [ ] Constant query count regardless of entry count
- [ ] OpenAPI schema generates cleanly

## Verify
`uv run pytest backend/tests/timeline -q && uv run alembic upgrade head && uv run alembic downgrade -1 && uv run alembic upgrade head` (docker Postgres up)

## Commit
`feat(timeline): model, schemas, repository, service, public+admin routers, api suite`

## Invariants
- Router-level auth — per-endpoint decorators are one forgotten line away from a public admin endpoint
- `public_filter` on every public read, asserted by the reusable leak test
- Service layer triggers revalidation; routers stay thin
- This schema settles before Phase 2 — Projects foreign-keys to `TimelineEntry`
