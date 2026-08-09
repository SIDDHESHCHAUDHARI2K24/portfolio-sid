# TD-21: Frontend Shell & Contract Tooling — Typegen, Category Cookie, Relevance Parity, Fetch Layer

**Phase:** P1 · **Wave:** 6 · **Executor:** agent · **Effort:** L (2 days)
**Source:** development-plan-P1.md → P1.T6 (S1–S4)
**Depends on:** TD-20, TD-19 · **Blocks:** TD-22, TD-24

## Purpose
Establish the client half of the phase's architectural decision: statically
cached pages with client-side personalisation, generated API types in both
apps, and the parity guarantee between the two relevance implementations.

## Paths
- Create: `frontend/src/lib/api.ts`, `frontend/src/lib/cacheTags.ts`, `frontend/src/lib/relevance.ts`, `frontend/src/components/CategoryProvider.tsx`, shared parity fixture (consumed by backend pytest + frontend vitest), backend `scripts/export_openapi.py` + committed `openapi.json`
- Modify: `frontend/package.json`, `admin/package.json` (openapi scripts), frontend root layout

## Steps
1. Backend script exports `openapi.json` to a **committed file**; `openapi-typescript` generates types into `frontend/` and `admin/` via `npm run openapi:generate` in each app — generating from a file means the CI drift check needs no live backend; no hand-written API response types remain anywhere
2. Cookie `portfolio_category`: one year, `SameSite=Lax`, **not** `HttpOnly` — the client must read it. `CategoryProvider` client component in the root layout reads it on mount and exposes `{category, setCategory, clear}`; `?for=recruiters` acts as an override that also writes the cookie, giving shareable pre-filtered links
3. `lib/relevance.ts` mirrors `is_relevant` exactly (same inputs, same boolean); a shared fixture asserts identical output for identical inputs across the Python and TypeScript implementations — drift surfaces as a failing test, not as a page highlighting the wrong things; highlight must apply within one frame of hydration
4. `lib/api.ts`: fetch wrapper with `next: { tags: [CACHE_TAGS.timeline], revalidate: 3600 }`; tag constants live in `lib/cacheTags.ts` — one source shared with the backend constants from TD-19, never string literals typed in two places
5. Build-output check: assert `next build` reports content routes as static. Reading a cookie server-side works perfectly in development and silently disables static generation everywhere — the check is mandatory, not optional

## Tests
- Parity fixture passes on both implementations (identical inputs → identical outputs) — includes the `DEFAULT` sentinel, override-only, and empty-map cases from TD-18
- `?for=` sets the category and writes the cookie; category persists across sessions and navigation
- Typegen drift: changing a Pydantic schema without regenerating fails CI
- `lib/api.ts` fetch carries the correct tag constants and `revalidate: 3600`

## Acceptance Criteria
- [ ] Types generate into both apps; no hand-written API response types remain
- [ ] No `cookies()` call in any content server component
- [ ] `next build` reports content routes as static, not dynamic
- [ ] Parity fixture passes on both implementations
- [ ] Admin edit surfaces publicly within seconds (tags match end-to-end)

## Verify
`npm run openapi:generate && npm run build` in `frontend/` and `admin/` · `grep -rn "cookies()" frontend/src/app` → no hits on content routes · parity: `uv run pytest -q -k parity` + `npm test -- relevance` in `frontend/`

## Commit
`feat(frontend): openapi typegen, category cookie+provider, relevance.ts parity, tagged fetch layer`

## Notes
- `openapi.json` is committed so the drift check and typegen need no live backend — regenerate and commit it whenever a Pydantic schema changes
- The admin SPA consumes the same generated types; keep both apps' generated output in one commit with the schema change

## Invariants
- Calling `cookies()` in a Next.js server component opts the route into dynamic rendering and kills ISR. Therefore highlight/dim and tile filtering are CLIENT-side: every content page ships the full dataset + `audience_tag_map` as one statically cached default variant; the build-output check asserts content routes stay static
- The relevance resolver has two implementations (Python `core/relevance.py` + TS `lib/relevance.ts`), both pure; the shared fixture asserts identical outputs
- Revalidation tags are shared constants — a tag typo produces a site that appears to work but never updates
- Generated types are the only API types; a hand-written response type is a drift bug waiting to happen
