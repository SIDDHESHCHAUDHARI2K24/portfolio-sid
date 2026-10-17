# E03-W1 — Collection covers

**Epic:** E03 Content · **Ticket:** E03-W1 · **Status:** Draft · **Depends on:** none

## Purpose
Covers never appear: they are fetched only on a manual admin click (EPIC F1), and the frontend builds their URL from an unset `NEXT_PUBLIC_R2_PUBLIC_URL` (F2).

## Goal
Every collection item with a stored cover shows it, locally and in production, and new items get a cover without a manual step.

## Reference files
- `backend/app/features/collections/{schemas,service,covers}.py`, `endpoints/router.py`, `tests/`
- `backend/app/core/storage.py` (`public_url`, `media_base_url`)
- `backend/app/features/certifications/service.py` (how `file_url` is built — follow the same pattern)
- `frontend/app/books/BooksClient.tsx`, `frontend/app/anime-manga/AnimeMangaClient.tsx`, `frontend/components/tiles/TileGrid.tsx`
- `admin/src/routes/collections/CollectionsForm.tsx`
- `backend/openapi.json`, `admin/src/api.d.ts`, `frontend/src/api.d.ts` (regenerate)
- `docs/features/collections.md`

## Functionality
- **`cover_url`:** `CollectionItemPublic` and `CollectionItemAdmin` gain `cover_url: str | None`, built server-side as `get_storage().get_url(cover_key)` (same as certifications `file_url`, `certifications/service.py:30`). `cover_key` stays for admin use.
- **Frontend:** books, anime-manga and tiles render `cover_url`; remove `NEXT_PUBLIC_R2_PUBLIC_URL` from cover rendering (audio config is out of scope).
- **Lookup on save:** on admin create, and on update when the result has no `cover_key`, call the existing `covers.fetch_and_store_cover(title, kind)`. `found` sets `cover_key`; `no_match` or `failed` saves without a cover. The manual "Look up cover" button stays for re-fetching.
- **Admin:** after save, show cover status (found / not found) from the response; no new controls.

## Edge cases
- Lookup timeout or network error → item saves, no cover, no 5xx; logged at INFO (no URLs with secrets).
- An existing `cover_key` is never overwritten automatically, even if the title changes.
- An explicit `cover_key: null` in an update clears the cover and must not immediately re-fetch it in the same request.
- Negative cache (TTL 300 s) still applies, so repeated saves of an unmatched title don't hammer Open Library or Jikan.
- `media_base_url` unset → `cover_url` uses the same fallback as certifications; it never returns `undefined`.
- Tests never hit the network (mock `covers`).

## Testing
- Backend: `cover_url` present when `cover_key` is set and null otherwise; create triggers one lookup; update with an existing cover doesn't; `failed`/`no_match` save without error; explicit clear doesn't re-fetch.
- Frontend: `npm run lint && npm test && npm run build`; local `/books` and `/anime-manga` show images for seeded covers (W3).
- Admin: `npm run lint && npm run build`; the react-doctor skill on the changed form.

## Acceptance criteria
- [ ] EPIC criteria 1 and 2 hold.
- [ ] OpenAPI and both `api.d.ts` files regenerated.
- [ ] `docs/features/collections.md` describes lookup-on-save and `cover_url`.

## Rollback
Revert and redeploy. No schema change.
