# TD-30: Track F — Intro Sequence + Ambient Audio

**Phase:** P2 · **Wave:** 7 · **Executor:** agent · **Effort:** L (4–5 days)
**Source:** development-plan-P2.md → Track F: F.T1–F.T4
**Depends on:** F.T1: TD-11 (early start during Wave 6); F.T2: F.T1; F.T3/F.T4: TD-22 · **Blocks:** GATE-P2

## Purpose
The most novel work in the project, with no dependency on any content model — only the app
shell. F.T1 can start early during Wave 6 once design tokens (TD-11) land. Track F carries no
migrations: audio tracks come from static config.

## Paths
- Create: intro component (Framer Motion), layout morph wiring, session/reduced-motion guards, audio player in root layout + HUD controls
- Modify: root layout, OverviewIntro shell from TD-22

## Steps
1. **F.T1 Intro port.** Rebuild the supplied HTML animation as a React component: six
   adjectives accumulating at ~0.45s intervals — all six visible at the final frame; six
   squares fill in step and end as a 2×3 mini-grid that becomes the selector; ~3s total (the
   source ran 4.67s). Port corrections: `useEffect` not `window.onload` (it does not fire
   reliably in Next.js); compiled Tailwind, no `cdn.tailwindcss.com`; scope `overflow: hidden`
   to the intro's lifetime, never globally; relabel the "Status" counter — it measures nothing
   today and becomes a genuine connection indicator when the voice agent lands in Phase 4.
2. **F.T2 Morph.** Framer Motion `layoutId` shared layout animation linking each loader square
   to its corresponding category tile — one continuous motion, no cut, no second animation.
   Keep both states mounted through the transition; animate opacity and layout rather than
   mounting/unmounting (where shared layout animations get fragile). Tile grid responsive on
   all breakpoints — no separate mobile pattern.
3. **F.T3 Guards + overlay invariant.** `sessionStorage` flag on mount → skip straight to the
   selector. `useReducedMotion` → skip entirely (a 3s forced animation with no escape is a
   vestibular accessibility failure). Click and Escape skip. OVERLAY INVARIANT: the intro
   renders as an overlay above already-server-rendered content — never
   `showIntro ? <Intro/> : <Overview/>`; that conditional serves crawlers an animation instead
   of a portfolio. It looks identical in a browser either way — verify with `curl`, not eyes.
4. **F.T4 Ambient audio.** A single `<audio>` element in the root layout — the App Router
   preserves it across client navigation. Tracks stored in R2, listed from static config. HUD
   controls: play/pause, volume, track switch. Persist state (track, volume, playing) to
   `sessionStorage`; on a full page load restore the state but do NOT auto-resume — browsers
   block autoplay without a fresh gesture, and attempting yields a caught promise rejection
   plus a UI that claims to be playing in silence. Off by default on first visit.
5. Register tile (Track F adds no content tiles — confirm the TD-22 tile contract intact) →
   run `scripts/regen_migration.sh "intro+audio"` (guard no-op: no migrations expected from
   static audio config; it asserts the single head) → pass `scripts/check_registries.py` →
   rebase on latest main before opening the PR.

## Tests
- Six words accumulate and remain visible at the final frame; six squares end as a 2×3 grid
- Total duration ~3s; no global style leakage after unmount
- Squares morph into tiles in one continuous motion, no visible cut; grid responsive
- Returning visitors within a session skip; `prefers-reduced-motion` skips; click/Escape skip
- Category switching never replays the intro
- Audio continues across client-side navigation; full reload restores track and volume without auto-resuming; off by default
- `curl` on `/` returns full overview content WITH the intro enabled

## Acceptance Criteria
- [ ] F.T1–F.T4 acceptance criteria above all green
- [ ] Overlay invariant verified with `curl` (rated Critical in the P0 risk register)
- [ ] No migrations introduced by this branch
- [ ] Registry check passes

## Verify
`curl -s localhost:3000/ && (cd backend && uv run alembic heads) && uv run scripts/check_registries.py`

## Commit
`feat(intro,audio): framer-motion intro, layout morph, session guards, ambient audio`

## Invariants
- Intro is an overlay above SSR content; never a conditional swap
- Audio off by default; restore state without auto-resume
- No `window.onload`, no CDN Tailwind, no global `overflow: hidden`
- Tile contract + regen + registry check verified before PR
