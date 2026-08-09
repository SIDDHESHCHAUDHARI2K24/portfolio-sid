# TD-35: Accessibility & Performance — AA, Keyboard/SR, CWV, react-doctor

**Phase:** P3 · **Wave:** 8 · **Executor:** agent · **Effort:** M (1–2 days)
**Source:** development-plan-P3.md → P3.T5 (S1–S4)
**Depends on:** TD-34 · **Blocks:** TD-36

## Purpose
Measure, don't assume. WCAG AA against the final palette with dimmed content
as the known risk — flagged since Phase 1, measurable only now that the real
palette exists — full keyboard and screen-reader traversal, payload and Core
Web Vitals budgets confirmed, and the first full-codebase react-doctor pass
since CI went diff-scoped.

## Paths
- Modify: dimmed-entry styling, intro/HUD components, filter chips (frontend)
- Measure: every content page payload, Lighthouse on main routes
- Audit: `frontend/` and `admin/` via react-doctor; deferred findings → `docs/`

## Steps
1. **P3.T5.S1 — contrast, including dimmed content.** Dimmed timeline and project entries are the specific risk — deliberately de-emphasised but still content people read, and reduced opacity against a dark background degrades contrast fast. Measure the *composited* result, not the token value. If AA can't be met at the intended opacity, dim via desaturation or scale rather than pushing opacity lower. Check non-text contrast for interactive elements too.
2. **P3.T5.S2 — keyboard + screen reader.** Tab order through intro, selector, HUD, tiles, and filter chips. Intro must be skippable by keyboard. HUD category switching must be reachable and announce changes via a live region — a silent re-render tells a screen reader user nothing happened. Filter chips need proper `aria-pressed`. Visible focus throughout.
3. **P3.T5.S3 — payload budget + Core Web Vitals.** Because relevance resolves client-side, every content page ships its **full dataset plus the tag map** — the right call for caching, but the payload grows with content. Measure per page; anything over roughly 200KB of JSON gets paginated or field-trimmed — **do not revert the architecture**. Lighthouse ≥ 90 on main routes; LCP under 2.5s; confirm the intro sequence is **not** the largest contentful paint element for first-time visitors. Images served through `next/image` from R2; fonts preloaded with `font-display: swap`; no render-blocking resources.
4. **P3.T5.S4 — react-doctor full audit.** `npx react-doctor@latest` across `frontend/` and `admin/` — the first full-codebase view since TD-14/P0.T6.S5 made CI diff-scoped. Triage by severity: fix security and performance findings, log the rest in `docs/`.

## Tests
- Composited contrast measurements for all text, dimmed entries included (≥ 4.5:1)
- Full keyboard traversal pass recorded; intro skippable by keyboard; live-region announcements verified with a screen reader or axe-core audit
- axe-core scan across all public routes; filter chips expose correct `aria-pressed` state
- Per-page JSON payload sizes measured against the ~200KB budget
- Lighthouse runs captured for main routes; LCP element identified and asserted not to be the intro
- react-doctor report archived in `docs/` with triage decisions

## Acceptance Criteria
- [ ] All text meets AA, dimmed included; interactive elements meet non-text contrast
- [ ] Full keyboard traversal; visible focus throughout; category changes announced
- [ ] Lighthouse performance ≥ 90 on main routes; no page ships an unreasonable JSON payload; LCP under 2.5s
- [ ] No high-severity react-doctor findings remain; deferred items logged in `docs/`

## Verify
`npx react-doctor@latest` in `frontend/` and `admin/`; Lighthouse on `/`, timeline, projects list+detail; payload check via `curl` of each page's embedded/JSON data; keyboard pass with focus visible on every interactive element.

## Commit
`fix(a11y,perf): WCAG AA incl. dimmed content, keyboard/SR navigation, CWV budgets, react-doctor clean`

## Invariants
- Contrast is measured on composited values, never on raw token values
- Dimming that can't meet AA is re-expressed via desaturation or scale — never by pushing opacity lower
- Client-side relevance architecture stays; oversized payloads are fixed by pagination/trimming, not by reverting
- The intro sequence must not be the LCP element
- Any styling fix here goes through design tokens — no new hardcoded colours may be reintroduced after TD-34
- Deferred findings are logged, never silently dropped
