# TD-36: Launch — Cutover, Access, Sentry, Restore Drill, Journeys, Content

**Phase:** P3 · **Wave:** 8 · **Executor:** paired (user + agent) · **Effort:** L (2 days + content authoring 1 day+)
**Source:** development-plan-P3.md → P3.T6 (S1–S6)
**Depends on:** TD-31, TD-32, TD-33, TD-34, TD-35 (all) · **Blocks:** GATE-P3

## Purpose
The highest-consequence sequencing in the project. Verify before indexing,
not after. Order is load-bearing: domain → TLS → indexing; Access only after
single-hostname coverage is confirmed; content last, because authoring is
where the design meets reality.

## Paths
- Infra: Cloudflare DNS/Tunnel/Access, R2 custom domain, Railway env vars, Google Search Console, Sentry
- Modify: `NEXT_PUBLIC_INDEXABLE`, `CF_ACCESS_ENABLED`, Playwright journey suite
- Create: `docs/` restore procedure, `development_plan/handoff/restore-procedure.md`

## Steps
1. **P3.T6.S1 — cutover + indexing.** Point `siddhesh-chaudhari.com` (frontend), `admin.siddhesh-chaudhari.com`, and `media.siddhesh-chaudhari.com` (R2) at the services; verify TLS on all three. **Only after every route serves correctly on the custom domain**: flip `NEXT_PUBLIC_INDEXABLE` (noindex has shipped since TD-04) and submit the sitemap to Google Search Console. If anything was indexed on the Railway hostname, add 301 redirects to the domain equivalents — the Railway hostname must never be indexed.
2. **P3.T6.S2 — Cloudflare Access.** Before flipping `CF_ACCESS_ENABLED`, confirm the Access application covers **both** the admin SPA and `/api/*` on the single hostname — a split configuration redirects CORS preflights to the login page and fails, presenting as a CORS bug (tech-stack-analysis.md §6.2). Test admin login end to end through Access; confirm the API rejects requests lacking a valid assertion. **Retain the env-var rollback until verified** — misconfiguration here locks you out of your own portal.
3. **P3.T6.S3 — Sentry.** Free tier on both FastAPI and Next.js. Alert specifically on the quiet failures: revalidation webhook errors (content appears stale), Resend failures (form notifications stop), and cover-fetch errors — not on raw error volume. Prove it with a deliberate revalidation failure.
4. **P3.T6.S4 — backup restore drill.** Confirm Railway's Postgres backup policy; if it isn't automatic, add the weekly `pg_dump` cron to R2. **Then actually restore a backup into a scratch database** — all content lives here and nowhere else, and an untested backup is a belief, not a backup. Document the procedure in `docs/` and `development_plan/handoff/restore-procedure.md`.
5. **P3.T6.S5 — Playwright critical journeys.** First visit → intro → select category → overview → timeline → filter → project → cross-link to timeline entry. Returning visit skips the intro. Category switch via HUD re-highlights without navigation. Admin: login with password and OTP → create a draft → publish → verify it appears publicly. Form submission with Turnstile. All journeys run in CI against the production build.
6. **P3.T6.S6 — content authoring (USER executes).** Paired step, run against `development_plan/handoff/content-authoring-checklist.md`: six `OverviewIntro` rows including default; full timeline; projects with attachments; skills with icons; certifications; both resume PDFs; the audience-tag mapping matrix configured with real tags; at least a few posts per collection; prose pages for Hobbies, Work Views, and Investor Intro; books and anime. **Budget time to act on the content-model gaps this surfaces** — a field that's too short, a section that doesn't fit, a tag vocabulary that doesn't carve the content the way you think about it. No fixture testing finds these.

## Tests
- TLS + route pass over HTTPS on all three hostnames before any indexing change
- Access: browser login works e2e; `curl` without assertion is rejected on SPA and `/api/*`
- Sentry: deliberate revalidation failure raises the configured alert
- Restore: scratch DB restored from backup, row counts spot-checked
- `npx playwright test` green in CI against the production build

## Acceptance Criteria
- [ ] All routes serve over HTTPS on the custom domain; `noindex` removed only after full verification; sitemap submitted
- [ ] Admin reachable only through Access; API rejects direct requests; login works end to end; env-var rollback retained until verified
- [ ] Sentry capturing from both services; a deliberate revalidation failure raises an alert
- [ ] Backups confirmed running; test restore into a scratch database succeeded; procedure documented
- [ ] All critical journeys pass in CI against the production build
- [ ] Every page has real content; no tile is empty for its intended audience; the default view is complete for crawlers

## Verify
`curl -sI https://siddhesh-chaudhari.com/ && curl -sI https://admin.siddhesh-chaudhari.com/ && curl -sI https://media.siddhesh-chaudhari.com/ && npx playwright test` — plus GSC sitemap status and the Sentry alert test.

## Commit
`chore(launch): domain cutover, Access enabled, Sentry, restore drill, critical journeys`

## Invariants
- Verify before indexing, never after; the Railway hostname is never indexed
- Access rollback path (env var) is retained until end-to-end verification passes
- The restore drill is mandatory — this is the one genuinely unrecoverable failure
- Content authoring is user-executed; a site with placeholder content isn't launched
