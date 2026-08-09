# TD-13: CI — OpenAPI Drift + Alembic Single-Head

**Phase:** P0 · **Wave:** 4 · **Executor:** agent · **Effort:** M (half day)
**Source:** development-plan-P0.md → P0.T6.S3, P0.T6.S4
**Depends on:** TD-12, TD-07 · **Blocks:** TD-24 (contention protocol)

## Purpose
Contract drift is silent until runtime; multiple migration heads fail
`alembic upgrade head` outright. Both are cheap to catch in CI and expensive
on a deploy. Phase 2's six parallel branches WILL produce duplicate heads —
this gate is not hypothetical.

## Paths
- Create: `backend/openapi.json` (committed export), `frontend/src/api/schema.ts`, `admin/src/api/schema.ts` (generated)
- Modify: `frontend/package.json` + `admin/package.json` (`openapi:generate` scripts), CI contract jobs

## Steps
1. Backend exports its schema: start the app, dump `app.openapi()` to `backend/openapi.json`, commit it
2. `npm i -D openapi-typescript` in frontend and admin; add `openapi:generate` script running `openapi-typescript ../../backend/openapi.json -o src/api/schema.ts` (pattern proven in the jobs-tracker repo)
3. CI contract job: start backend → regenerate openapi.json → `npm run openapi:generate` in both apps → `git diff --exit-code` across all three artifacts
4. Alembic head check job: `uv run alembic heads`; assert exactly one line of output; on failure print the full output so the offending revision names appear in the CI log
5. Document the resolution in `docs/conventions.md`: rebase on main and REGENERATE the migration before opening the PR; `alembic merge` only for what slips through
6. Negative tests on a throwaway branch: change a Pydantic schema without regenerating → red; add a second migration sharing a down_revision → red, naming both revisions

## Tests
- Schema change without typegen fails CI; regenerate + commit makes it pass
- Two migrations sharing a down_revision fail the build with both revision names in the output

## Acceptance Criteria
- [ ] Changing a Pydantic schema without regenerating types fails CI
- [ ] Regenerating and committing makes it pass
- [ ] Two heads fail the build; the error names the offending revisions
- [ ] openapi.json + both generated schema.ts files committed and current

## Verify
`cd backend && uv run alembic heads && git status --short openapi.json`

## Commit
`ci: contract checks — OpenAPI drift gate + alembic single-head`

## Invariants
- One migration per feature branch, generated against current origin/main; never hand-edit down_revision
- Generated types are committed artifacts — CI diffs them, it does not trust them
- Resolution order: rebase + regenerate first, `alembic merge` as fallback
