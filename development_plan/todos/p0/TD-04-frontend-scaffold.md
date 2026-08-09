# TD-04: Next.js Scaffold + Overlay Invariant + noindex Default

**Phase:** P0 · **Wave:** 1 · **Executor:** agent · **Effort:** L (1 day)
**Source:** development-plan-P0.md → P0.T3.S5 (+ P3 noindex decision pulled forward)
**Depends on:** TD-00 · **Blocks:** TD-11, TD-14, TD-19, TD-21

## Purpose
App Router skeleton that bakes in the three highest-consequence frontend
decisions: overlay-not-replacement composition, cookie-based category state,
and noindex-until-launch. All are invisible in normal browser testing —
verify with curl, not with eyes.

## Paths
- Create: `frontend/` (create-next-app), repo-level `scripts/check_ssr.sh`
- Modify: `frontend/next.config.ts`, `frontend/app/layout.tsx`, `frontend/app/page.tsx`, `docs/conventions.md`

## Steps
1. `npx create-next-app@latest frontend --typescript --tailwind --eslint --app --use-npm`
2. `next.config.ts`: set `output: 'standalone'`; add `images.remotePatterns` entry for `media.siddhesh-chaudhari.com` (R2 custom domain, provisioned in TD-M2)
3. `npm i react-markdown remark-gfm rehype-sanitize framer-motion`
4. `npx shadcn@latest init` (default tokens now; real mapping in TD-11)
5. Homepage: server-rendered full default overview in `app/page.tsx`; state the overlay invariant in `docs/conventions.md` — the intro and selector will compose as overlays ABOVE the overview, never `showIntro ? <Intro/> : <Overview/>`, which would serve crawlers an animation instead of a portfolio
6. Category state: cookie, not localStorage. The cookie is readable server-side, BUT content pages must never call `cookies()` — read it only in a dedicated layout/wrapper so content RSCs stay cacheable
7. `NEXT_PUBLIC_INDEXABLE` defaults to `false`; root metadata emits `robots: { index: false, follow: false }` unless it is `'true'` (launch flips it in P3/TD-32)
8. Create `scripts/check_ssr.sh`: curls a URL and asserts the response HTML contains the content marker without JS execution; exits non-zero otherwise
9. `npm run build` — confirm `.next/standalone` output exists

## Tests
- `bash scripts/check_ssr.sh http://localhost:3000` passes against the running app
- Category cookie set by a client is readable in the wrapper server component, and `cookies()` appears in no content page
- Response HTML carries the noindex robots meta while NEXT_PUBLIC_INDEXABLE is unset/false

## Acceptance Criteria
- [ ] `curl` against `/` returns HTML containing page content, with no JS execution
- [ ] `next build` produces standalone output
- [ ] Category cookie readable server-side; zero `cookies()` calls in content pages
- [ ] noindex robots metadata active by default; `scripts/check_ssr.sh` introduced and passing

## Verify
`cd frontend && npm run build && bash ../scripts/check_ssr.sh http://localhost:3000`

## Commit
`feat(frontend): Next.js scaffold — standalone, overlay invariant, noindex default`

## Invariants
- Overlay-not-replacement: crawlers must receive the portfolio, not an animation
- Cookie-not-localStorage for category; `cookies()` banned from content RSCs
- noindex until launch; timestamps UTC; no hardcoded colours (TD-11)
