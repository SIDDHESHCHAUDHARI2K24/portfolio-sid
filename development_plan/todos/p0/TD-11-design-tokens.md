# TD-11: Design Tokens → Tailwind/shadcn in Both Apps

**Phase:** P0 · **Wave:** 3 · **Executor:** agent · **Effort:** M (3 hrs)
**Source:** development-plan-P0.md → P0.T5.S2
**Depends on:** TD-10, TD-04, TD-05 · **Blocks:** TD-30 (intro sequence), Phase 3 re-skin (TD-34)

## Purpose
Translate docs/DESIGN.md tokens into CSS custom properties consumed by
Tailwind and shadcn in BOTH apps, so every component built in Phases 1 and 2
consumes tokens — making the Phase 3 re-skin a token swap instead of a
rewrite.

## Paths
- Modify: `frontend/app/globals.css`, `frontend/tailwind.config.ts`,
  `admin/src/index.css`, `admin/tailwind.config.ts`, shadcn variable mapping in both apps
- Reference: `docs/DESIGN.md`, `docs/conventions.md`

## Steps
1. Define all DESIGN.md tokens as CSS custom properties in `globals.css` (frontend) and `index.css` (admin) — dark palette only
2. `tailwind.config.ts` `theme.extend` in both apps references `var(--token)` — no literal values in the config
3. Map Stitch's palette onto shadcn's variable names (`--background`, `--foreground`, `--primary`, `--muted`, and friends) — never invent parallel names
4. Add the guard: a lint/review rule forbidding hardcoded hex values in component code (regex scan for `#[0-9a-fA-F]{3,8}` in tsx/css outside the token definition files), recorded in `docs/conventions.md`
5. Render sample shadcn Button/Card components in both apps to prove the dark palette applies
6. Token-swap proof: change one CSS variable value, confirm both apps visibly change, then revert

## Tests
- Both apps render shadcn components in the dark palette
- Hex scan finds colour literals only inside the token definition files
- One-token change visibly affects both apps

## Acceptance Criteria
- [ ] Both apps render shadcn components in the dark palette
- [ ] No hardcoded colour literals in either app outside token definitions
- [ ] Changing one token value visibly changes both apps
- [ ] Hardcoded-hex prohibition recorded as a lint/review rule

## Verify
`git grep -nE "#[0-9a-fA-F]{6}" -- frontend/app admin/src`

## Commit
`feat: design tokens — DESIGN.md mapped to Tailwind/shadcn in both apps`

## Invariants
- shadcn variable names are the mapping target; no parallel token vocabularies
- Any hardcoded colour that slips through becomes manual work in the Phase 3 re-skin — catch at review
- Dark only; light mode deferred unless explicitly requested
