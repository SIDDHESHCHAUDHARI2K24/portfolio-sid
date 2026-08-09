# TD-18: Relevance Engine — Map Table, Pure Resolver, Map Endpoint, Postgres Tests

**Phase:** P1 · **Wave:** 5 · **Executor:** agent · **Effort:** L (2 days)
**Source:** development-plan-P1.md → P1.T3 (S1–S4)
**Depends on:** TD-16 · **Blocks:** TD-20 (transitively TD-21/22/23)

## Purpose
One mechanism behind highlight/dim on Timeline and Projects, tile visibility
on Overview, and resume variant selection — three features, one
implementation. Kept a pure function over plain data so the identical logic
ships to the client and parity is testable (TD-21).

## Paths
- Create: `backend/app/core/relevance.py`, `backend/app/features/relevance/` (models, schemas, repository, service, router)
- Modify: `backend/app/core/models_registry.py`, new migration (map table + seed rows)

## Steps
1. `AudienceTagMap` model: `audience` (enum) + `topic_tag_id`, unique together; seeded in the migration with sensible defaults — `engineering` + `consulting` for RECRUITERS, `startup` + `fundraising` for FOUNDERS, and equivalents for TECHIES, INVESTORS, PERSONAL — so the feature is demonstrable before any hand configuration
2. `core/relevance.py` — exact signature, pure, no ORM objects, no database access:
   ```python
   def is_relevant(item_tag_slugs: set[str], overrides: set[Audience], audience: Audience,
                   tag_map: dict[Audience, set[str]]) -> bool:
       if audience in overrides:
           return True
       return bool(item_tag_slugs & tag_map.get(audience, set()))
   ```
3. Load the tag map once per request, never per item — per-item resolution is N+1 by construction
4. `GET /api/v1/relevance/map` returning `{audience: [tag_slug, ...]}` for all five audiences; small and rarely changing — cache aggressively and revalidate the cache tag when the admin edits the mapping (TD-19/TD-23 path); ship it in the initial payload of every content page
5. Integration tests against real Postgres (docker compose service container) — do not mock the database; tag intersection is exactly the query logic where a mock confidently returns whatever you told it to

## Tests
Six mandatory cases against real Postgres:
1. No tags → not relevant
2. Tags matching one audience only → relevant for that audience only
3. Tags matching several audiences → relevant for each
4. Override with no matching tags → relevant
5. Override plus matching tags → relevant
6. Empty tag map for an audience → not relevant

Plus: `Audience.DEFAULT` highlights nothing; map endpoint returns all five audiences; editing the mapping invalidates the cached response.

## Acceptance Criteria
- [ ] Mapping persists and enforces (audience, topic_tag_id) uniqueness
- [ ] Seed data present immediately after migration
- [ ] Matching tags highlight; non-matching do not; an override forces highlight regardless of tags
- [ ] `Audience.DEFAULT` highlights nothing
- [ ] All six cases covered and passing against real Postgres in CI
- [ ] Editing the mapping in admin invalidates the cached `/api/v1/relevance/map` response

## Verify
`uv run pytest backend/tests/relevance -q` (docker Postgres up) · `curl -s localhost:8000/api/v1/relevance/map | jq 'keys | length'` → 5

## Commit
`feat(relevance): audience tag map, pure is_relevant resolver, cached map endpoint`

## Invariants
- `is_relevant` stays pure — plain data in, bool out; it is mirrored exactly in `frontend/src/lib/relevance.ts` (TD-21) and a shared fixture asserts identical outputs for identical inputs on both implementations
- Tag map loaded once per request
- Mapping lives in the database, not a config file — changing it must not require a deploy
