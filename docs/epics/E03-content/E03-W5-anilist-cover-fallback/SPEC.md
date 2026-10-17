# E03-W5 — AniList fallback for anime and manhwa covers

**Epic:** E03 Content · **Ticket:** E03-W5 · **Status:** Done (local) · **Depends on:** E03-W1

## Purpose
Anime and manhwa covers come only from Jikan (`api.jikan.moe`). On 2026-10-17 Jikan timed out (15 s, no response) while AniList answered in 0.2 s, so all 7 anime and manhwa samples saved without covers. Production has the same single point of failure.

## Goal
Anime and manhwa cover lookups still find a cover when Jikan is down or has no match.

## Reference files
- `backend/app/features/collections/covers.py` (lookup sources, validation, negative cache, storage write)
- `backend/app/features/collections/tests/` (cover tests; network mocked)
- `docs/features/collections.md`

## Functionality
- For `anime` and `manhwa`: try Jikan first with a short timeout (5 s); on timeout, error, or no match, query AniList GraphQL `https://graphql.anilist.co` with `Media(search: <title>, type: ANIME|MANGA) { coverImage { extraLarge large } }`. Manhwa maps to `MANGA`. No API key is needed.
- The chosen image goes through the existing download, validation (image content type, 5 MiB cap) and content-hashed storage path, unchanged.
- Books stay on Open Library.
- The negative cache records "no match" only after both sources miss.

## Edge cases
- Both sources time out → `failed` (not `no_match`), so a later save retries.
- AniList returns `null` Media (no match) → `no_match` if Jikan also missed.
- AniList rate limit (HTTP 429) → treated as failure for that call; no retry loop.
- The AniList image host is not in any allow-list of rendered hosts: covers are always served from our storage, so nothing changes on the frontend.
- Tests never hit the network.

## Testing
- Unit (mocked HTTP): Jikan hit → Jikan URL used; Jikan timeout → AniList used; Jikan no match → AniList used; both miss → `no_match`; both error → `failed`; manhwa → `type: MANGA`.
- `uv run ruff check . && uv run mypy app && uv run pytest -q`.
- Local: rerun `seed_demo.py` against `portfolio_e03_demo`; anime and manhwa covers appear on the preview `/anime-manga`.

## Acceptance criteria
- [x] Fallback implemented and tested.
- [x] The 7 anime and manhwa samples get covers locally.
- [x] `docs/features/collections.md` lists both sources and the order.

## Rollback
Revert; lookups return to Jikan only.
