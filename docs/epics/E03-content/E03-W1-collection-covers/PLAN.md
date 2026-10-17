# E03-W1 Collection covers Implementation Plan

> **For agentic workers:** use superpowers:executing-plans. Steps use checkbox syntax.

**Goal:** Collection items expose a server-built `cover_url`, the frontend renders it, and admin create/update fetches a cover automatically.

**Architecture:** `_item_to_dict` adds `cover_url = get_storage().get_url(cover_key)` (certifications pattern). `service.create_dict`/`update_dict` call a new best-effort helper `_auto_cover(title, kind) -> str | None` that wraps `fetch_and_store_cover` and swallows every exception. Frontend replaces `NEXT_PUBLIC_R2_PUBLIC_URL` composition with `item.cover_url`.

**Tech Stack:** FastAPI, SQLAlchemy async, pytest, Next.js, Vite admin, openapi-typescript.

**Spec:** `docs/epics/E03-content/E03-W1-collection-covers/SPEC.md`

## Global Constraints
- Tests never hit the network: mock `app.features.collections.service.fetch_and_store_cover`.
- Negative cache TTL 300 s stays in `covers.py` (untouched).
- `cover_key` remains in both schemas. No schema/migration change.
- Audio config (`NEXT_PUBLIC_R2_PUBLIC_URL` in `audioConfig.ts`) is out of scope.

## Decisions (small gaps)
1. Lookup runs in the service (not router) so create and update share it; it builds `get_storage()` and an `httpx.AsyncClient(timeout=20)` itself. Failure/exception -> INFO log, no cover.
2. Create with an explicit non-null `cover_key` skips lookup (never overwrite).
3. Update looks up only when `cover_key` is not in `model_fields_set` and the stored item has no `cover_key`; lookup uses the post-update title/kind. Explicit `cover_key: null` clears and does not re-fetch.
4. Tiles (`BooksTile`, `AnimeMangaTile`) render no covers (summary text only); `TileGrid` uses `hero_image_key`, unrelated. Nothing to change there; only `BooksClient` and `AnimeMangaClient` (3 call sites).
5. Admin cover status: after a successful save, navigate to the list with router state `{coverNotice}` ("Cover found." / "No cover found.") derived from the response `cover_url`; list renders it as a one-line message. No new controls. Skipped if lookup was not attempted (cover already set) -> "Cover found." is still accurate since `cover_url` is present.
6. Admin payload only sends `cover_key` when non-empty on create (empty string field becomes `null` today; on create null is "unset" so lookup runs). On edit, an emptied field sends explicit null = clear (spec semantics).

## Review Focus
- Lookup raising (timeout/network) -> still 201/200, no cover (T1 test).
- Title change on item with cover -> cover unchanged (T1 test).
- `media_base_url` unset -> `cover_url` is `/media/<key>`, never None when key set (T1 test).
- Repeated unmatched saves -> negative cache respected: covered by existing `covers` logic; test that `no_match` result saves fine.

## Task 1: Backend `cover_url` and lookup-on-save
**Files:** Modify `backend/app/features/collections/schemas.py`, `service.py`; Test `backend/app/features/collections/tests/test_collections.py` (add autouse fixture `_no_network_covers` mocking `service.fetch_and_store_cover` to return `CoverResult("no_match")` and counting calls; new tests below).

**Interfaces:** Produces `CollectionItemPublic.cover_url: str | None`; `async def _auto_cover(title: str, kind: str) -> str | None` in service.

- [ ] Write failing tests (each maps to a spec edge case):
  - `test_cover_url_present_when_key_set` (create with `cover_key="x.jpg"`: `cover_url` endswith `/media/x.jpg`or contains `x.jpg`; admin + public) and `test_cover_url_null_without_key`.
  - `test_create_triggers_one_lookup_and_sets_cover` (mock returns found `book-abc.jpg`; 1 call; `cover_key` set).
  - `test_create_with_explicit_cover_skips_lookup` (0 calls).
  - `test_update_with_existing_cover_does_not_lookup` incl. title change; cover_key unchanged.
  - `test_update_without_cover_triggers_lookup`.
  - `test_lookup_failed_and_no_match_save_without_cover` (parametrize `failed`, `no_match`).
  - `test_lookup_exception_saves_without_5xx` (mock raises `httpx.ConnectTimeout`).
  - `test_explicit_null_cover_clears_without_refetch` (0 calls after PATCH `cover_key: null`).
- [ ] Run `pytest app/features/collections -q`: new tests FAIL.
- [ ] Implement schema field, `_item_to_dict` `cover_url`, `_auto_cover`, wire into create_dict/update_dict per Decisions 2-3.
- [ ] Run pytest, `ruff check .`, `mypy app`: pass.
- [ ] Commit `feat(collections): cover_url and lookup on save (E03-W1)`.

## Task 2: OpenAPI + types
- [ ] `uv run python scripts/export_openapi.py`; `npm ci && npm run openapi:generate` in `admin/` and `frontend/`; confirm `cover_url` in both `api.d.ts`.

## Task 3: Frontend render `cover_url`
**Files:** Modify `frontend/app/books/BooksClient.tsx`, `frontend/app/anime-manga/AnimeMangaClient.tsx`.
- [ ] Replace `item.cover_key` condition/`src` with `item.cover_url`. Verify `grep -rn "R2_PUBLIC_URL" frontend/app` empty.
- [ ] `npm run lint && npm test && npm run build`.

## Task 4: Admin cover status
**Files:** Modify `admin/src/routes/collections/CollectionsForm.tsx` (add `cover_url` to Item type; create/update onSuccess navigate with state), `CollectionsList.tsx` (show notice via `useLocation().state`).
- [ ] Implement per Decision 5/6; `npm run lint && npm run build`; run react-doctor on changed files.

## Task 5: Docs, spec, commit
- [ ] Update `docs/features/collections.md` (API table, lookup-on-save flow, `cover_url`, invariants); tick spec checkboxes, Status "Done (local)"; commit.
