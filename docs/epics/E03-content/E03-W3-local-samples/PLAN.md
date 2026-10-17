# E03-W3 Local Samples Implementation Plan

**Goal:** One command fills every content type locally with realistic samples, real covers and native articles.
**Spec:** `SPEC.md`. **Scope:** `backend/scripts/seed_demo.py` only (no app code changes).

## Decisions
1. Collection samples use real titles; the marker is `[sample-demo]` appended to `note` (no title prefix, so cover lookups match).
2. Old rows (`Sample — …`, `Sample Anime — …`) carry the same marker but are no longer in the list: seed deletes marked collection rows not in `COLLECTION` (migration of old data).
3. Covers: `covers.fetch_and_store_cover` with the configured storage adapter and one `httpx.AsyncClient`, only for marked items without `cover_key` (never re-fetched), 0.5 s pause for Jikan's rate limit. A failed or unreachable lookup is listed in the summary, never fatal. `--no-covers` skips the network.
4. Native posts: `platform=internal`, slugs `sample-…`, upserted by slug, one per collection, bodies of ~300 words (headings, list, fenced code, link), existing topic tags.
5. Refresh: `--revalidate-url` plus `REVALIDATION_SECRET` env POSTs `/api/revalidate` for `certifications, collections, posts, prose, thesis`; otherwise the curl is printed.
6. `--remove` deletes marked collection rows, `Sample —` titles, and `sample-` slugs (posts, prose). Cover files stay (content-hashed).
7. Guard unchanged (development/local + localhost DB).

## Steps
- [x] Replace the collection list and add `NATIVE_POSTS`.
- [x] Add stale-row cleanup, cover fill, summary, revalidate, argparse flags.
- [x] `ruff check`, `ruff format`, `mypy scripts/seed_demo.py`.
- [x] Run twice against a copy DB (`portfolio_e03_demo`): identical counts, no re-fetch.
- [x] Guard checks: `ENVIRONMENT=production` and a non-localhost DB are refused.
- [x] Preview stack (backend 24785, frontend 24735, admin 24755): themed pages, `/writing/sample-…` and covers verified.
