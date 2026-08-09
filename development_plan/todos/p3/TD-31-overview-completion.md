# TD-31: Overview Completion — Arrangement, Pinning, Empty States, Hero

**Phase:** P3 · **Wave:** 8 · **Executor:** agent · **Effort:** M (1–2 days)
**Source:** development-plan-P3.md → P3.T1 (S1–S4)
**Depends on:** GATE-P2 · **Blocks:** TD-32, TD-34

## Purpose
Converge the six Phase 2 tracks into a coherent overview. Small because
Phase 1 established the tile contract and each Phase 2 track contributed its
own tile — what remains is arrangement, not integration. If tiles are
missing at this point, that is the big-bang failure dependency-map.md §8
exists to prevent; stop and re-gate instead.

## Paths
- Create: `frontend/src/config/tileArrangement.ts` (audience → ordered tile IDs)
- Modify: overview grid, tile summary selectors, `OverviewIntro` (frontend)
- Modify: publishable mixin in `backend/app/` + one Alembic migration (`is_pinned`)

## Steps
1. **P3.T1.S1 — per-audience arrangement.** Configuration, not code: a `tileArrangement` map from audience to ordered tile IDs, so reordering never touches components.

   | Audience | Tiles (after Contact) |
   |---|---|
   | Recruiters | Timeline, Projects, Skills, Certifications, Tech Rabbithole, How I Use AI, Work Views |
   | Techies | Timeline, Projects, Skills, Certifications, How I Use AI, Tech Rabbithole, Projects I Want To Work On |
   | Investors | Timeline, Investment Thesis, Dealflow, Tech Rabbithole, How I Use AI, Certifications |
   | Founders | Timeline, Investor Intro, VC for Founders, How I Use AI, Tech Rabbithole, Certifications |
   | Personal | Timeline, Books, Anime & Manhwa, Hobbies |
   | Default | All tiles, professional first |

   - Contact sits directly below the main tile for **every** audience
   - Default is what crawlers receive → it must be **complete**, never a subset
   - Personal deliberately excludes Projects, Skills, Certifications — intended, not an omission
2. **P3.T1.S2 — latest-content selection + pinning.** Alembic migration adds `is_pinned` boolean (default false) to every publishable model. Tile summary = pinned item if one exists, else most recent published by date. Pin wins; recency is the fallback.
3. **P3.T1.S3 — empty-state verification.** Unpublish everything in each content type in turn. The tile must disappear entirely — omission, not dimming — and the grid must reflow without gaps. An empty tile linking to an empty page reads as a broken site, not an unfinished section. This is where a Phase 2 track that skipped its `isEmpty` check surfaces.
4. **P3.T1.S4 — hero image.** Complete the per-audience `hero_image_key` left nullable in P1.T7.S3: serve from R2 via `next/image` with `priority` (above the fold, largest-contentful-paint candidate). Provide a sensible fallback when unset — a missing image never leaves a hole.

## Tests
- Vitest: arrangement map returns the exact ordered tile IDs per audience; default = full tile set; Contact directly below main tile in every arrangement
- Vitest: summary selector — pinned item beats newer item; unpinning restores recency
- pytest: migration up/down clean; `is_pinned` defaults false on all publishable models
- Playwright: switching audience re-arranges the grid without navigation
- Empty-state matrix: for each content type, unpublish-all → tile omitted, grid reflows, zero dead links

## Acceptance Criteria
- [ ] Each audience shows its specified tiles in the table's order; Contact below the main tile for every audience
- [ ] Default shows everything, professional first
- [ ] Switching audience re-arranges without navigation
- [ ] Tiles show latest item; pinning overrides; unpinning restores recency
- [ ] Every tile omitted when empty; grid reflows cleanly; no dead links
- [ ] Hero renders per audience; absent image degrades gracefully; LCP not regressed

## Verify
`npm run test --workspace frontend && uv run pytest && uv run alembic upgrade head && uv run alembic downgrade -1 && uv run alembic upgrade head && npx playwright test overview`

## Commit
`feat(overview): per-audience tile arrangement, pinning, empty states, hero image`

## Invariants
- Arrangement is configuration; reordering never touches component code
- Default arrangement is complete — crawlers must receive everything
- Empty tile = omitted entirely; never dimmed, never linking to an empty page
- Pin wins; recency is only the fallback
