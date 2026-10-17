# E03-W3 — Local samples: covers and native articles

**Epic:** E03 Content · **Ticket:** E03-W3 · **Status:** Done (local) · **Depends on:** E03-W1, E03-W2

## Purpose
The owner reviews UI and admin locally. Collections have no covers and there are no native articles to look at (user request, 2026-10-17).

## Goal
One command fills every content type locally with realistic, clearly marked samples, including real covers and native articles.

## Reference files
- `backend/scripts/seed_demo.py` (created 2026-10-17, untracked in the main checkout; bring it into this branch)
- `backend/app/features/collections/covers.py`, `backend/app/features/posts/`
- `frontend/app/api/revalidate/` (cache refresh after seeding)

## Functionality
- **Commit `seed_demo.py`:** keep the guard (local only: `ENVIRONMENT` development/local and DB host localhost), idempotency, and `--remove`.
- **Collections:** use real, well-known titles so lookups match, e.g. books *Zero to One*, *The Mom Test*, *Designing Data-Intensive Applications*; anime *Frieren*, *Steins;Gate*, *Haikyuu!!*; manhwa *Solo Leveling*, *Omniscient Reader*, *Tower of God*. Mark samples via the item's note/section field ("Sample"), not the title, so lookups match.
- **Covers:** run `covers.fetch_and_store_cover` for each collection sample; `--no-covers` skips network access.
- **Native articles:** 3 internal posts, one per collection, with ~300-word markdown bodies (headings, a list, a code block, a link), slugs `sample-…`, published, and audience tags.
- **Refresh:** after seeding, call the frontend revalidate route for all touched tags when `REVALIDATION_SECRET` and the frontend URL are configured; otherwise print the command.

## Edge cases
- Offline or a failed lookup → the item is seeded without a cover; the summary lists which items failed.
- Rerun → no duplicates; existing covers are not re-fetched.
- `--remove` deletes only sample rows (matched by the sample marker or `sample-` slug) and leaves stored cover files (content-hashed; harmless).
- The guard blocks any non-local DB, including a production URL in the shell.

## Testing
- Run twice locally: identical counts; `/books` and `/anime-manga` show covers; three `/writing/sample-…` pages render.
- `uv run ruff check scripts/seed_demo.py` and mypy pass.
- The guard refuses `ENVIRONMENT=production` and a non-localhost DB (quick manual check).

## Acceptance criteria
- [x] EPIC criterion 6 holds (book covers and native articles verified locally).
- [x] The script is committed; usage is in its docstring (`LOCAL.md` untouched, awaiting approval).
- [ ] Anime/manhwa covers: Jikan (api.jikan.moe) was unreachable from the dev network on 2026-10-17; rerun the seed where it is reachable.

## Rollback
`uv run python scripts/seed_demo.py --remove`.
