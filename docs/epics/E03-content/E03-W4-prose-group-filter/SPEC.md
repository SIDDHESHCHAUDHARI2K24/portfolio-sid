# E03-W4 — Prose `?group=` filter

**Epic:** E03 Content · **Ticket:** E03-W4 · **Status:** Done (local) · **Depends on:** none

## Purpose
`GET /api/v1/prose?group=hobbies` returns every prose page; the filter is ignored (EPIC F6).

## Goal
`?group=` returns only that group's published pages; an unknown group returns 422, as the posts `?collection=` filter does.

## Reference files
- `backend/app/features/prose/endpoints/router.py`, `service.py`, `repository.py`, `tests/`
- `backend/app/features/posts/endpoints/router.py` (`?collection=` pattern to mirror)
- `docs/features/prose.md`; frontend callers of `/prose` (`grep -rn '"/prose' frontend`)

## Functionality
- Add an optional `group: ProseGroup | None` query parameter; filter in the repository with `public_filter` intact.
- No frontend change unless a caller relies on the current unfiltered result; check callers first.

## Edge cases
- Unknown group → 422.
- No pages in the group → `[]`.
- No parameter → current behavior (all published pages).

## Testing
- Backend tests: each group filters correctly, unknown → 422, no parameter → all; OpenAPI regenerated.

## Acceptance criteria
- [x] Filter works and is tested; `docs/features/prose.md` updated.

## Rollback
Revert.
