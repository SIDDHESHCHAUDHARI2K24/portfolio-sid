# TD-22: Timeline Public Experience — Page, Filter Chips, OverviewIntro, Tile Contract, HUD

**Phase:** P1 · **Wave:** 6 · **Executor:** agent · **Effort:** XL (3–4 days)
**Source:** development-plan-P1.md → P1.T7 (S1–S5)
**Depends on:** TD-21 · **Blocks:** TD-24, TD-30

## Purpose
The public face of the spine: the timeline page with client-side
highlight/dim, filter chips, the per-audience overview intro, the tile
contract Phase 2 reuses, and the persistent HUD. Per dependency-map §8 the
tile contract lands here rather than in Phase 3, turning F21's ten hard
dependencies into soft ones.

## Paths
- Create: `frontend/src/app/timeline/page.tsx` + timeline client components, filter chips, `frontend/src/components/hud/`, `frontend/src/components/tiles/`, `backend/app/features/overview/` (models, repository, seed migration)
- Modify: frontend root layout (HUD mount), `docs/conventions.md` (tile contract)

## Steps
1. `app/timeline/page.tsx` as an RSC fetches entries + tag map via the tagged fetch layer and passes both to a client component that applies relevance; vertical chronological layout, education and experience interleaved by date with visual distinction by kind; markdown summaries via `react-markdown` with `rehype-sanitize`; dimmed entries drop opacity and visual weight but remain fully readable and selectable — everyone sees everything, only emphasis changes
2. Filter chips: client-side filtering over already-loaded data — no refetch; multi-select with OR semantics within the set; state reflected in the URL (`?tags=education,consulting`) for shareability, `rel="canonical"` stays the bare path; visually distinct from audience highlighting — the two axes must not be confused
3. `OverviewIntro` feature slice: `audience` (unique, including a `default` row — enforce its existence at the database level or in the seed), `headline`, `body` (markdown), `hero_image_key`, `cta_label`, `cta_url`; seed all six rows in a migration so the page is never empty. Server-render the `default` row into the HTML, ship all six rows in the payload, swap client-side on hydration when a cookie exists
4. Tile contract: `Tile` interface `{id, title, summary, href, audiences, priority, isEmpty}`; grid layout — `OverviewIntro` full-width at top, tiles below; **omission, not dimming** — a tile irrelevant to the current audience is absent (`isEmpty`), unlike timeline entries which dim; document the contract in `docs/conventions.md` with a worked example; each Phase 2 feature contributes its tile as the final sub-task of its own track
5. HUD: fixed bottom-right, mounted in the root layout so it persists across navigation; compact category selector plus scroll percentage; switching is **instant — no animation, no navigation** — it updates context, which re-runs client-side relevance; "show everything" reset returns to the default view; the audio control mounts here in Phase 2 — leave the slot; the intro animation plays once per session and must never replay on switch — guard it explicitly

## Tests
- `curl /timeline` returns all entries in server HTML (default variant)
- `curl /` returns the default headline and body; six intro rows present after migration
- Category switch re-highlights with no navigation; returning visitors see their audience variant after hydration
- Chips filter instantly; URL reflects selection; canonical stays bare; clearing restores all entries
- Timeline tile renders with latest-entry summary; disappears entirely when no published entries exist
- Dimmed text meets WCAG AA contrast

## Acceptance Criteria
- [ ] `curl` returns all entries; switching category changes highlighting with no navigation
- [ ] Dimmed entries remain AA-readable
- [ ] Six intro rows seeded; `default` row enforced; `curl /` returns default copy
- [ ] Tile contract documented in conventions with a worked example
- [ ] Tile disappears when empty; HUD persists, switches instantly, resets to default, intro never replays

## Verify
`curl -s localhost:3000/timeline | grep -c "<article"` · `curl -s localhost:3000/ | grep -i "<h1"` · `npm run build` → content routes static

## Commit
`feat(frontend): timeline page, filter chips, overview intro, tile contract, hud`

## Invariants
- Server HTML always carries the full dataset in the default variant — personalisation is a client layer over the static cache; crawlers and first-time visitors see correct content immediately
- Omission, not dimming, for tiles; dimming, never hiding, for entries
- A missing `default` OverviewIntro row means an empty header for crawlers — its existence is enforced, not hoped for
- HUD switching never navigates or animates; intro plays once per session
