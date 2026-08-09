# TD-34: Design Pass & Re-skin — Stitch Tokens, Leak Audit, Visual Regression

**Phase:** P3 · **Wave:** 8 · **Executor:** agent · **Effort:** L (2–3 days)
**Source:** development-plan-P3.md → P3.T4 (S1–S4)
**Depends on:** TD-31 · **Blocks:** TD-35

## Purpose
The "UI last" strategy pays off here — or reveals that tokens leaked. Apply
the real design purely through token values. This sub-task's actual duration
is determined by the discipline exercised in Phase 2, not by anything done
here: every component edit required is a leak whose honest cost lands here.

## Paths
- Modify: `globals.css` in both apps (CSS custom properties only)
- Update: `docs/DESIGN.md` (Stitch export)
- Create: Playwright screenshot suite — mobile/tablet/desktop per page
- Audit targets: all component code in `frontend/` and `admin/`

## Steps
1. **P3.T4.S1 — full Stitch design.** Generate the complete screen set against actual pages, not imagined ones — overview per audience, timeline, projects list and detail, skills, certifications, collections, prose, contact, and the intro-to-selector sequence. Export the updated `docs/DESIGN.md`. **Take the tokens, not the HTML** — Stitch emits HTML and Tailwind; refactoring that into existing components would discard working code to gain a stylesheet.
2. **P3.T4.S2 — token swap + leak audit.** Update CSS custom properties in `globals.css` for both apps. The audit is the real test: grep all components for hex literals, `rgb(`, and Tailwind default palette classes (`bg-slate-800`, `text-gray-400`, …). Every hit is a Phase 2 leak — convert it to a token. If the site re-skins cleanly from a token swap alone, the strategy worked.
3. **P3.T4.S3 — visual regression protection.** Capture Playwright screenshots of every page at mobile, tablet, and desktop widths **before** starting. Refine page by page, comparing after each — layout changes late in a project break things far from where you're looking, and screenshots are what surface that.
4. **P3.T4.S4 — intro + HUD polish.** Retune against the final palette (with P2 Track F): the six squares must read clearly against the new background and morph convincingly into the restyled tiles. Recheck timing — perceived speed changes with contrast, and a sequence that felt right in greyscale may feel slow or abrupt now. HUD must remain legible over every page background.

## Tests
- Audit greps return zero hits in component code after conversion (see Verify)
- Screenshot suite: every page × 3 breakpoints, diffs reviewed one by one
- Manual intro/HUD pass on every page background in the final palette

## Acceptance Criteria
- [ ] `docs/DESIGN.md` updated with the full token set; no Stitch HTML imported
- [ ] Site re-skins from token values alone; zero hex literals, `rgb(`, or default-palette classes in component code; both apps consistent
- [ ] Every page matches the design at all three breakpoints; regression suite passes with reviewed diffs
- [ ] Morph reads cleanly in the final palette; HUD legible on every page; total duration still ~3s

## Verify
```
grep -rEn '#[0-9a-fA-F]{3,8}\b|rgba?\(' frontend/src admin/src   # expect: only globals.css token definitions
grep -rEn '(bg|text|border|ring)-(slate|gray|zinc|neutral|stone|red|orange|amber|yellow|lime|green|emerald|teal|cyan|sky|blue|indigo|violet|purple|fuchsia|pink|rose)-' frontend/src admin/src   # expect: no hits
npx playwright test visual
```

## Commit
`feat(design): full re-skin via token swap, leak audit, visual regression baseline`

## Invariants
- Tokens, not HTML — Stitch output is a token source only, never imported markup
- A re-skin requiring component edits means leaks; each one is converted, not worked around
- Screenshots are captured BEFORE changes, never reconstructed after
- No hardcoded colours anywhere when this card closes — the exit criterion follows into GATE-P3
