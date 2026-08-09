# GATE-P3: Phase 3 Exit Gate — Launch

**Phase:** P3 · **Wave:** 8 · **Executor:** paired · **On pass:** LAUNCH
**Source:** development-plan-P3.md → Exit Checklist (copied verbatim)

Walk this gate only when every acceptance criterion on TD-31..TD-36 is met.
Evidence before claims — each item carries the command or artifact that proves it.

## Prerequisites
- All acceptance criteria on TD-31, TD-32, TD-33, TD-34, TD-35, TD-36 checked with evidence attached
- GATE-P2 passed — Phase 3 is convergence; a skipped gate upstream compounds here
- `$FRONTEND_URL` below is the deployed frontend; launch items are verified against `https://siddhesh-chaudhari.com`

## Exit Checklist

- [ ] Overview renders correct tiles per audience; empty tiles omitted; default complete
  - Verify: `npx playwright test overview` + manual pass over all six audiences (including empty-state matrix from TD-31)
- [ ] `Person` JSON-LD generated from live data and passing Rich Results Test
  - Verify: `curl -s "$FRONTEND_URL/" | grep 'application/ld+json'` returns the Person block; Google Rich Results Test reports no errors
- [ ] Sitemap and robots correct; AI crawlers explicitly allowed
  - Verify: `curl -s "$FRONTEND_URL/robots.txt"` shows GPTBot, ClaudeBot, PerplexityBot, CCBot, Google-Extended allowed plus the sitemap pointer; `curl -s "$FRONTEND_URL/sitemap.xml"` lists every published page, bare paths only
- [ ] `curl` suite passes on every public route, running in CI
  - Verify: `bash scripts/check_ssr.sh` exits 0; CI workflow shows the job required
- [ ] `next build` reports content routes static
  - Verify: `npm run build --workspace frontend` — every content route marked static in build output
- [ ] Site re-skinned; zero hardcoded colours
  - Verify: TD-34 audit greps (hex literals, `rgb(`, default Tailwind palette classes) return zero hits in component code
- [ ] WCAG AA met including dimmed content; keyboard traversal complete
  - Verify: composited contrast measurements ≥ 4.5:1 including dimmed entries; full keyboard traversal pass recorded (TD-35)
- [ ] Lighthouse ≥ 90; LCP under 2.5s
  - Verify: Lighthouse reports for `/`, timeline, projects list and detail
- [ ] Live on the custom domain; `noindex` removed; sitemap submitted
  - Verify: `curl -sI https://siddhesh-chaudhari.com/` → 200 with no `noindex` (header or meta); GSC shows the submitted sitemap
- [ ] Cloudflare Access enabled and verified
  - Verify: unauthenticated request to `https://admin.siddhesh-chaudhari.com/` redirects to Access login; `/api/*` rejects assertion-less requests; login works end to end
- [ ] Sentry capturing from both services
  - Verify: deliberate revalidation failure raises the configured alert
- [ ] Backup restore tested and documented
  - Verify: scratch-database restore succeeded; procedure present in `docs/` and `development_plan/handoff/restore-procedure.md`
- [ ] Playwright critical journeys green
  - Verify: `npx playwright test` green in CI against the production build
- [ ] Real content authored across every page
  - Verify: `development_plan/handoff/content-authoring-checklist.md` fully checked; default view complete for crawlers

## After the gate

Phase 4 — Deep Agent Voice System (F29) — is deferred by design and scoped only after launch. OpenClaw is prohibited. `backend/app/features/agent/` is reserved for it; the decorative HUD percentage counter becomes a genuine connection-status indicator when it lands.

LAUNCH
