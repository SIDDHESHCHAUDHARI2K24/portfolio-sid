# E03-W4 plan — prose `?group=` filter

## Findings
- Public `GET /api/v1/prose` ignores any query param. `repository.list_by_group` and `service.list_by_group_dicts` exist but nothing calls them.
- Pattern to mirror: posts `?collection=` (`posts/endpoints/router.py`): `str | None` query, `if value:` guard, enum coercion, `HTTPException(422)` on `ValueError`, else the unfiltered list.
- Frontend callers (`frontend/app/page.tsx`, `frontend/app/sitemap.ts`, `frontend/app/llms.txt/route.ts`) call `/prose` with no params. Admin uses the admin router only. No frontend change.
- DB enum labels are member names (`HOBBIES`, ...). Pass `ProseGroup` members to the query, not raw strings.

## Ordered TDD steps
1. Tests first (`backend/app/features/prose/tests/test_prose.py`):
   - `?group=hobbies` returns only hobbies pages; the same for `work_views` and `investor_intro`.
   - Drafts in the requested group are excluded (`public_filter` intact).
   - Unknown group (`?group=nope`) returns 422.
   - Valid group with no pages returns `[]`.
   - No param returns all published pages (existing behavior).
   - Confirm the new tests fail before implementation.
2. Repository: `list_by_group(session, group: ProseGroup)` keeps `public_filter`. Order by `group`, then `sort_order`, to match the unfiltered list.
3. Service: `list_by_group_dicts` takes `ProseGroup`. It's already present; adjust the type only.
4. Router: add `group: str | None = Query(None)` to `list_public`. When set, coerce with `ProseGroup(group)`, map `ValueError` to 422 `Unknown group: <x>`, then call the service. Otherwise call `list_public_dicts`.
5. Run the prose tests, then the full suite, `ruff`, and `mypy`.
6. Regenerate OpenAPI (`scripts/export_openapi.py`). If `openapi.json` changes, run `npm ci && npm run openapi:generate` in `admin/` and `frontend/`.
7. Update `docs/features/prose.md` (API table row for `?group=`, invariant) and tick the spec checkbox. Set Status to "Done (local)".
8. Commit `fix(prose): honour ?group= filter (E03-W4)`.

## Edge-case decisions
- Empty `?group=` is treated as no parameter, matching posts `?collection=` (`if collection:`).
- Unknown value → 422, never 200 with an empty list.

## Files
- `backend/app/features/prose/endpoints/router.py`
- `backend/app/features/prose/repository.py`
- `backend/app/features/prose/service.py`
- `backend/app/features/prose/tests/test_prose.py`
- `backend/openapi.json` (if changed)
- `admin/src/api.d.ts`, `frontend/src/api.d.ts` (only if openapi changed)
- `docs/features/prose.md`
- `docs/epics/E03-content/E03-W4-prose-group-filter/SPEC.md`
