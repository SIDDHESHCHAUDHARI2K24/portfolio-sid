# TD-28: Track D — Collections + Prose Pages

**Phase:** P2 · **Wave:** 7 · **Executor:** agent · **Effort:** L (5–6 days)
**Source:** development-plan-P2.md → Track D: D.T1–D.T5
**Depends on:** TD-24 · **Blocks:** GATE-P2

## Purpose
Carries the only third-party integration in Phase 2: the cover pipeline. Download once, store
in R2, never hotlink. ProsePages deliver the Investor Intro with no new backend work.

## Paths
- Create: `backend/app/features/collections/{models,...,covers}.py`, `backend/app/features/prose/...` + tests
- Create: books page, anime & manhwa page, prose `[slug]` route
- Modify (per TD-24 protocol): the five shared contention files

## Steps
1. **D.T1 CollectionItem.** `title`, `creator` (author or studio), `kind` (BOOK/ANIME/MANHWA),
   `section` (Tech/Business/Personal Development — books only; unused for anime/manhwa),
   `cover_key`, `external_id`, `external_source` (OPEN_LIBRARY/JIKAN/MANUAL), `status`
   (READING/COMPLETED/WANT_TO_READ), `note`, `sort_order`. NO topic tags — this is
   Personal-audience content and needs no relevance resolution.
2. **D.T2 Cover pipeline** (`features/collections/covers.py`, runs on admin save). Books:
   Open Library search by title, then `covers.openlibrary.org/b/id/{cover_id}-L.jpg`. Anime
   and manga: Jikan `/v4/anime?q=` and `/v4/manga?q=`, top match. Download once and store in
   R2 with a content-hashed key via `StorageAdapter` — never hotlink: serving from these hosts
   makes every page view depend on a third party, and Jikan is an unofficial MAL wrapper with
   no uptime guarantee. Validate content-type and cap size before writing — an endpoint
   returning HTML must fail loudly, not store a 404 page as a cover. Return a structured
   result: found-and-stored / no-match / lookup-failed. Manual upload is a NORMAL path
   (manhwa coverage is thin; Korean titles frequently miss), not an error state. Cache
   negative lookups briefly so re-saving an unmatched item doesn't re-query per keystroke.
3. **D.T3 Slice + pages.** Books page groups by section; Anime & Manhwa page has two sections.
   Image-tile grids via `next/image` against the R2 domain only (remotePatterns from P0).
   Admin triggers the lookup on title blur, showing the result inline with an upload fallback.
   Render-time check: no page ever requests an image from Open Library or Jikan.
4. **D.T4 ProsePage.** `slug` (unique), `title`, `body` (markdown), `group` enum
   (HOBBIES/WORK_VIEWS/INVESTOR_INTRO), `cta_label`, `cta_url`, `sort_order`, standard
   publishing fields. Render with react-markdown + remark-gfm + rehype-sanitize — sanitisation
   stays even with a single author. `group` is routing, not relevance (same separation as
   `Post.collections`). The Investor Intro is a ProsePage — no new backend; `cta_url` points
   at the Google Form.
5. **D.T5 Tiles.** Books, Anime & Manhwa, Hobbies: Personal only. Investor Intro: Founders.
   All omitted when empty.
6. Register the tiles per the P1 contract → run `scripts/regen_migration.sh "collections+prose"`
   → pass `scripts/check_registries.py` → rebase on latest main before opening the PR.

## Tests
- All three kinds persist with correct sectioning: books section; anime and manhwa do not
- A known book resolves and stores a cover in R2
- Unmatched title returns "no match" and prompts upload; API downtime returns "lookup failed" without blocking the save
- An HTML/error response is never stored as a cover (content-type + size cap enforced)
- No render-time requests to Open Library or Jikan (network panel check)
- All three prose groups render; CTA appears only when both label and URL are set; markdown is sanitised
- `curl` returns full content on every page

## Acceptance Criteria
- [ ] D.T1–D.T5 acceptance criteria above all green
- [ ] Manual upload flows as a first-class path in admin
- [ ] Migration regenerated against latest main; single head
- [ ] Registry check passes

## Verify
`curl -s localhost:3000/books && curl -s localhost:3000/investor-intro && (cd backend && uv run alembic heads) && uv run scripts/check_registries.py`

## Commit
`feat(collections,prose): models, cover pipeline, pages, prose pages, tiles`

## Invariants
- Covers are downloaded once and stored in R2; never hotlinked
- Manual upload is a normal path, not an error state
- Tiles registered + regen run + registry check passed before PR
