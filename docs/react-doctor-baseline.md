# React Doctor Baseline

**Date:** 2026-08-28 · **Tool:** `react-doctor@0.9.12` · **Command:**
`npx react-doctor@latest . --no-telemetry` (frontend + admin separately)
**Scope:** `frontend/` (Next.js App Router) and `admin/` (Vite + React) only.
Backend is **excluded by design** — its quality is `ruff`/`mypy`'s job (CI,
conventions invariant #14).

This document is the clean starting point for diff-scoped mode. The CI Action
(`.github/workflows/react-doctor.yml`) posts a summary comment + inline review
comments on every PR but is **advisory** by default; `doctor.config.ts` sets
`blocking: "error"` so a PR that *introduces* a new error-severity finding fails.

## Summary

| App | Files scanned | Total issues | Errors (blocking) | Warnings |
|---|---|---|---|---|
| `frontend/` | 80 | 35 | **0** | 35 |
| `admin/` | 49 | 35 | **0** | 35 |

**0 blocking errors on the committed tree** — the gate is green today.

### `frontend/` categories

- Security: 5 warnings
- Bugs: 15 warnings
- Maintainability: 7 warnings
- Performance: 7 warnings
- Accessibility: 1 warning

### `admin/` categories

- Bugs: 4 warnings
- Accessibility: 12 warnings
- Performance: 12 warnings
- Maintainability: 7 warnings

## Representative findings (warnings — backlog, not day-one failures)

Frontend:

- `unsafe-json-in-html` ×4 — `app/[slug]/page.tsx:57`, `app/contact/page.tsx:57`,
  `app/page.tsx:88`, `app/projects/[slug]/page.tsx:55` (JSON-LD via
  `dangerouslySetInnerHTML` — acceptable for structured data, revisit if user input)
- `nextjs-no-img-element` ×5 — `AnimeMangaClient.tsx`, `BooksClient.tsx`,
  `SkillIcon.tsx` (plain `<img>`; migrate to `next/image` over time)
- `no-array-index-as-key` — `components/timeline/TimelineClient.tsx:153`
- `no-async-event-handler-without-reentry-guard` ×2 — `ContactForm.tsx:72`,
  `DealflowForm.tsx:80`
- `nextjs-image-missing-sizes` — `components/tiles/TileGrid.tsx:53`

Admin:

- `control-has-associated-label` ×8 — `TagSelect.tsx`, `TagMapMatrix.tsx`
- `no-array-index-as-key` ×2 — `CrawlerHits.tsx:108`, `login-verify.tsx:125`
- `query-mutation-missing-invalidation` — `AdminLayout.tsx:50`
- `no-static-element-interactions` / `click-events-have-key-events` —
  `AdminLayout.tsx:61`

## How to reproduce

```bash
cd frontend && npx react-doctor@latest . --no-telemetry
cd admin   && npx react-doctor@latest . --no-telemetry
# single-file diff before/after a change:
npx react-doctor@latest --scope changed --base main --verbose
```

## Updating this baseline

Re-run the audit after a meaningful cleanup batch and replace the counts/table
above. The PR Action keeps the running trend; this file is the human-readable
snapshot the gate was seeded from.
