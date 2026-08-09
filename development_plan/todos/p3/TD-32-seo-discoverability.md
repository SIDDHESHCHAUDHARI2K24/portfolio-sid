# TD-32: SEO & Discoverability — JSON-LD, Sitemap/Robots, Canonical, llms.txt, SSR Suite

**Phase:** P3 · **Wave:** 8 · **Executor:** agent · **Effort:** L (2–3 days)
**Source:** development-plan-P3.md → P3.T2 (S1–S6)
**Depends on:** TD-31 · **Blocks:** TD-33, TD-36

## Purpose
The payoff for every architectural constraint accepted since the Next.js
decision: make the site machine-readable to the AI recruiting tools that
motivated this stack. Everything is derived from live data, validated with
real tools, and guarded in CI — silent failures are the risk here.

## Paths
- Create: `frontend/app/sitemap.ts`, `frontend/app/robots.ts`, `frontend/app/llms.txt/route.ts`, Person/content-type JSON-LD modules
- Modify: `generateMetadata` on every route, `scripts/check_ssr.sh`, CI workflow
- Reads: TimelineEntry, experience, Skill, Certification, Resume, Post, Project, ProsePage

## Steps
1. **P3.T2.S1 — Person JSON-LD from live data.** Emit `schema.org/Person` on `/`, generated server-side from the database — **never hardcoded** (a hardcoded block goes stale the first time a certification is added):
   - `name`, `jobTitle`, `url`, `email` (plain, matching the contact tile), `image`
   - `sameAs`: LinkedIn, GitHub, and any other profiles
   - `alumniOf` ← `TimelineEntry` rows where `kind = EDUCATION`
   - `worksFor` ← current experience (null `end_date`)
   - `knowsAbout` ← published Skills · `hasCredential` ← published Certifications
   Validate with Google's Rich Results Test — malformed JSON-LD is ignored silently: no error, just no benefit.
2. **P3.T2.S2 — sitemap + robots.** `app/sitemap.ts` queries every publishable model for published entries, emits `lastModified` from `updated_at`, and lists **canonical bare paths only — never `?for=` variants**; tag the sitemap fetch so publishing content refreshes it. `app/robots.ts` allows all crawlers, points at the sitemap, and **explicitly allows GPTBot, ClaudeBot, PerplexityBot, CCBot, Google-Extended** — several are blocked by common copied configurations, which would defeat the project's core goal.
3. **P3.T2.S3 — canonical + per-page metadata.** `generateMetadata` per route with distinct title and description derived from content — identical templated descriptions are treated as low quality. Canonical is always the bare path, so `?for=recruiters` and `?tags=education` consolidate to one URL. Open Graph + Twitter cards; detail pages derive description from their summary.
4. **P3.T2.S4 — content-type schema.** Projects → `CreativeWork` or `SoftwareSourceCode`; prose → `BlogPosting` with `datePublished` and `author` referencing the Person. Do not over-mark — invalid or spammy structured data is worse than none. Every result passes the Rich Results Test.
5. **P3.T2.S5 — llms.txt.** Route handler generating markdown from published content: who you are, what each section contains, links to **both resume PDFs**. Honest status note included: llmstxt.org is an emerging convention with uncertain adoption, not a standard — a cheap bet targeting the stated goal, not a substitute for the JSON-LD and server-rendered HTML that actually do the work.
6. **P3.T2.S6 — SSR verification.** Extend `scripts/check_ssr.sh` (TD-04 baseline, CI since TD-14) to **every public route**: `curl` each and assert expected content appears in raw HTML with no JavaScript execution. Also assert `next build` still reports content routes as static — a stray `cookies()` added in Phase 2 would have quietly turned them dynamic. Both assertions run in CI.

## Tests
- `curl` on `/` returns valid `Person` JSON-LD; adding a certification changes `hasCredential` after revalidation
- Sitemap lists all published pages with accurate `lastModified`; publishing updates it; no `?for=`/`?tags=` URLs present
- robots.txt contains the explicit five-agent allow-list and the sitemap pointer
- Every page has a unique title and description; canonical is bare on every route
- `/llms.txt` returns generated markdown reflecting current content, including both resume links
- `check_ssr.sh` passes on every public route; `next build` static assertion holds

## Acceptance Criteria
- [ ] Person JSON-LD generated from live data; passes Rich Results Test with no errors
- [ ] Sitemap lists all published pages with accurate `lastModified`; refreshed on publish
- [ ] AI crawler user-agents explicitly allowed in robots.txt
- [ ] Every page has a unique title and description; canonical is always bare; OG tags render correct previews
- [ ] Detail pages emit valid schema; all pass the Rich Results Test
- [ ] `/llms.txt` returns generated markdown reflecting current content
- [ ] Every public route returns content-bearing HTML to `curl`; `next build` reports content routes static; both assertions run in CI

## Verify
`bash scripts/check_ssr.sh && npm run build --workspace frontend && curl -s "$FRONTEND_URL/robots.txt" && curl -s "$FRONTEND_URL/sitemap.xml" && curl -s "$FRONTEND_URL/llms.txt"` — then run Rich Results Test against the deployed URL for `/` and each schema-bearing detail page.

## Commit
`feat(seo): live Person JSON-LD, sitemap/robots with AI allow-list, canonical metadata, llms.txt, full SSR suite in CI`

## Invariants
- JSON-LD is derived from the database, never hardcoded
- Canonical is always the bare path; `?for=` and `?tags=` variants never appear in sitemap or canonical
- GPTBot, ClaudeBot, PerplexityBot, CCBot, Google-Extended stay explicitly allowed
- `NEXT_PUBLIC_INDEXABLE` remains false — noindex ships since TD-04 and only TD-36 flips it, after every route is verified on the custom domain; the Railway hostname must never be indexed
- Server-rendered HTML is the contract; CI catches any regression
