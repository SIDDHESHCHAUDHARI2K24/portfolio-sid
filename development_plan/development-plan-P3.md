# Development Plan — Phase 3: Integration, Discoverability & Launch

**Document 3 of 3, Part 4** · Companions: `tech-stack-analysis.md`, `dependency-map.md`, `development-plan-P0.md`, `development-plan-P1.md`, `development-plan-P2.md`
**Status:** Draft for approval
**Feature IDs:** F21 (overview completion), F11 (SEO), F27 (analytics), F28 (re-skin)

---

## Phase Overview

**Goal:** Converge the six Phase 2 tracks into a coherent product, make it discoverable by the AI recruiting tools that motivated the Next.js decision, apply the real design, and launch.

**Entry criteria:** Phase 2 exit checklist complete — critically, every content feature has registered its tile. If tiles are missing, P3.T1 becomes the big-bang integration that `dependency-map.md` §8 exists to prevent.

**Exit criteria:**
- Overview renders correct tiles per audience with correct empty-state behaviour
- JSON-LD, sitemap and canonical tags verified against live pages
- Real design applied; no hardcoded colours anywhere
- WCAG AA met, including dimmed content
- Site live on the custom domain with Access enabled and content authored

**Estimated effort:** 8–12 days (28 sub-tasks). Low parallelism — this phase is convergence.

| Task | Focus | Effort | Risk |
|---|---|---|---|
| P3.T1 | Overview completion | M / 1–2 days | Low (if tiles landed) |
| P3.T2 | SEO & discoverability | L / 2–3 days | **High** |
| P3.T3 | Crawler analytics | M / 1 day | Low |
| P3.T4 | Design pass & re-skin | L / 2–3 days | Medium |
| P3.T5 | Accessibility & performance | M / 1–2 days | Medium |
| P3.T6 | Launch readiness | L / 2 days | **High** |

---

## The Decision That Should Be Made First

**Do not let Google index the Railway hostname.**

If the site goes public on `*.up.railway.app` before the custom domain is live, those URLs get indexed. Migrating later means 301 redirects, split authority, a duplicate-content window, and a re-crawl cycle you don't control — all against the one goal that shaped this architecture.

Ship with `noindex` until the domain is active. Everything else works normally; only indexing is suppressed. P3.T6.S1 flips it.

---

## Task P3.T1: Overview Completion

**Feature:** F21 · **Effort:** M / 1–2 days · **Dependencies:** all Phase 2 tracks · **Risk:** Low

Small because Phase 1 established the tile contract and each Phase 2 track contributed its own tile. What remains is arrangement, not integration.

### P3.T1.S1: Define per-audience tile arrangement

**Description:** Set which tiles each audience sees and in what order, from your operating description.

**Implementation Hints:** Configuration, not code — a `tileArrangement` map from audience to ordered tile IDs, so reordering doesn't require touching components. Per your walkthrough:

| Audience | Tiles (after Contact) |
|---|---|
| Recruiters | Timeline, Projects, Skills, Certifications, Tech Rabbithole, How I Use AI, Work Views |
| Techies | Timeline, Projects, Skills, Certifications, How I Use AI, Tech Rabbithole, Projects I Want To Work On |
| Investors | Timeline, Investment Thesis, Dealflow, Tech Rabbithole, How I Use AI, Certifications |
| Founders | Timeline, Investor Intro, VC for Founders, How I Use AI, Tech Rabbithole, Certifications |
| Personal | Timeline, Books, Anime & Manhwa, Hobbies |
| Default | All tiles, professional first |

Contact sits directly below the main tile for every audience. The default arrangement is what crawlers receive, so it must be complete rather than a subset.

**Dependencies:** all Phase 2 tile registrations
**Effort:** M / 4 hrs
**Risk Flags:** Personal deliberately excludes Projects, Skills and Certifications. That is intended, not an omission.
**Acceptance Criteria:**
- Each audience shows its specified tiles in order
- Default shows everything
- Switching audience re-arranges without navigation

### P3.T1.S2: Implement latest-content selection and pinning

**Description:** Populate each tile's summary with the most recent published item, with a manual override.

**Implementation Hints:** Default to most-recent by date. Add an `is_pinned` boolean to publishable models so a specific item can be forced into its tile regardless of recency — you will want this for a project that represents you better than whatever you touched last. Pin wins; recency is the fallback.

**Dependencies:** P3.T1.S1
**Effort:** M / 3 hrs
**Acceptance Criteria:** Tiles show latest item; pinning overrides; unpinning restores recency.

### P3.T1.S3: Verify empty-state behaviour

**Description:** Confirm every tile disappears entirely when its feature has no published content — omission, not dimming.

**Implementation Hints:** Test by unpublishing everything in each content type in turn. Grid must reflow without gaps. This is where a Phase 2 track that skipped the `isEmpty` check will surface.

**Dependencies:** P3.T1.S1
**Effort:** S / 2 hrs
**Risk Flags:** An empty tile linking to an empty page is worse than no tile — it reads as a broken site rather than an unfinished section.
**Acceptance Criteria:** Every tile omitted when empty; grid reflows cleanly; no dead links.

### P3.T1.S4: Add hero image support to OverviewIntro

**Description:** Complete the per-audience hero image left as a nullable field in P1.

**Implementation Hints:** `hero_image_key` served from R2 via `next/image` with `priority` set — it is above the fold and the largest contentful paint candidate. Provide a sensible fallback when unset so a missing image never leaves a hole.

**Dependencies:** P1.T7.S3
**Effort:** S / 2 hrs
**Acceptance Criteria:** Hero renders per audience; absent image degrades gracefully; LCP not regressed.

---

## Task P3.T2: SEO & Discoverability

**Feature:** F11 · **Effort:** L / 2–3 days · **Dependencies:** P3.T1 · **Risk:** High

The payoff for every architectural constraint accepted since the Next.js decision.

### P3.T2.S1: Generate the Person JSON-LD from live data

**Description:** Emit `schema.org/Person` structured data on `/`, generated from the database rather than hardcoded.

**Implementation Hints:** This is the single most machine-readable artifact on the site and what AI recruiting tools parse first. Generate it server-side from real content so it never drifts from the site:

- `name`, `jobTitle`, `url`, `email` (plain, matching the contact tile), `image`
- `sameAs`: LinkedIn, GitHub, and any other profiles
- `alumniOf`: derived from `TimelineEntry` rows where `kind = EDUCATION`
- `worksFor`: derived from the current experience (null `end_date`)
- `knowsAbout`: derived from published Skills
- `hasCredential`: derived from published Certifications

A hardcoded JSON-LD block goes stale the first time you add a certification. Derived structured data stays true by construction.

**Dependencies:** P3.T1
**Effort:** M / 4 hrs
**Risk Flags:** Validate against Google's Rich Results Test. Malformed JSON-LD is ignored silently — you get no error, just no benefit.
**Acceptance Criteria:**
- `curl` on `/` returns valid `Person` JSON-LD
- Adding a certification changes `hasCredential` after revalidation
- Passes the Rich Results Test with no errors

### P3.T2.S2: Build sitemap and robots

**Description:** Generate `sitemap.xml` from published content and serve `robots.txt`.

**Implementation Hints:** Next.js `app/sitemap.ts` querying every publishable model for published entries, emitting `lastModified` from `updated_at`. Only canonical bare paths — never `?for=` variants. Tag the sitemap fetch so publishing content refreshes it. `app/robots.ts` allowing all crawlers and pointing at the sitemap. Explicitly allow GPTBot, ClaudeBot, PerplexityBot, CCBot and Google-Extended — several are blocked by default in common configurations, which would defeat the entire goal.

**Dependencies:** P3.T2.S1
**Effort:** M / 3 hrs
**Risk Flags:** A copied robots.txt that blocks AI crawlers is a plausible and self-defeating mistake here.
**Acceptance Criteria:**
- Sitemap lists all published pages with accurate `lastModified`
- Publishing content updates the sitemap
- AI crawler user-agents explicitly allowed

### P3.T2.S3: Set canonical tags and per-page metadata

**Description:** Ensure every page declares a canonical bare URL and carries meaningful metadata.

**Implementation Hints:** `generateMetadata` per route with distinct title and description — derived from content, not templated, since identical descriptions across pages are treated as low quality. Canonical always the bare path, so `?for=recruiters` and `?tags=education` consolidate to one URL. Open Graph and Twitter cards for link previews. Detail pages (projects, prose) derive description from their summary.

**Dependencies:** P3.T2.S2
**Effort:** M / 4 hrs
**Acceptance Criteria:** Every page has a unique title and description; canonical is always bare; OG tags render correct previews.

### P3.T2.S4: Add content-type structured data

**Description:** Emit appropriate schema on detail pages beyond the homepage `Person`.

**Implementation Hints:** `CreativeWork` or `SoftwareSourceCode` for projects; `BlogPosting` for prose pages with `datePublished` and `author` referencing the `Person`. Do not over-mark — invalid or spammy structured data is worse than none.

**Dependencies:** P3.T2.S3
**Effort:** M / 3 hrs
**Acceptance Criteria:** Detail pages emit valid schema; all pass the Rich Results Test.

### P3.T2.S5: Publish llms.txt

**Description:** Add an `llms.txt` giving LLM crawlers a markdown map of the site.

**Implementation Hints:** A route handler generating markdown from published content: who you are, what each section contains, links to both resume PDFs. Be honest about status — `llmstxt.org` is an **emerging convention with uncertain adoption**, not a standard, and no major crawler has committed to honouring it. It costs perhaps two hours and it targets your stated goal directly, which makes it a reasonable bet; it is not a substitute for the JSON-LD and server-rendered HTML that actually do the work.

**Dependencies:** P3.T2.S1
**Effort:** S / 2 hrs
**Acceptance Criteria:** `/llms.txt` returns generated markdown reflecting current content.

### P3.T2.S6: Verify server rendering across every route

**Description:** Confirm the invariant that has been carried since Phase 0 actually holds in production.

**Implementation Hints:** Script a `curl` pass over every public route asserting that expected content appears in raw HTML with no JavaScript execution. Add it to CI so a later change cannot silently regress it. Also confirm `next build` still reports content routes as static — a `cookies()` call added anywhere in Phase 2 would have quietly turned them dynamic.

**Dependencies:** P3.T2.S3
**Effort:** M / 3 hrs
**Risk Flags:** This is the check that catches an SEO regression introduced any time in the previous three phases. It is invisible in a browser.
**Acceptance Criteria:**
- Every public route returns content-bearing HTML to `curl`
- `next build` reports content routes static
- Both assertions run in CI

---

## Task P3.T3: Crawler Analytics

**Feature:** F27 · **Effort:** M / 1 day · **Dependencies:** P3.T2 · **Risk:** Low

### P3.T3.S1: Install the Cloudflare Web Analytics beacon

**Description:** Add the beacon to the root layout for traffic and verified-bot reporting.

**Implementation Hints:** Script tag in `app/layout.tsx` using the token from P0.T1.S5. Privacy-preserving, no cookies, no consent banner required — which is why it was chosen over alternatives that would have forced one.

**Dependencies:** P0.T1.S5
**Effort:** XS / 1 hr
**Acceptance Criteria:** Pageviews and bot traffic appear in the Cloudflare dashboard.

### P3.T3.S2: Log origin requests by user agent

**Description:** Record user-agent and path for requests reaching the origin, so you can see *which* AI crawler read *what*.

**Implementation Hints:** FastAPI middleware writing `user_agent`, `path`, `ip_hash`, `timestamp` to a `CrawlerHit` table. **Hash the IP** — you have no reason to store raw visitor IPs and every reason not to. Match against known agents: GPTBot, ClaudeBot, PerplexityBot, CCBot, Google-Extended, Bytespider. Write asynchronously so logging never blocks a response, and add a retention job pruning rows beyond 90 days.

**Dependencies:** P1.T1.S4
**Effort:** M / 3 hrs
**Risk Flags:** **This undercounts by design** (gap G9). Edge-cached responses never reach the origin, and static pages are exactly what crawlers fetch most. Treat it as "which crawlers have visited" rather than "how many times" — the ratio is not meaningful.
**Acceptance Criteria:** Hits recorded with hashed IPs; known agents classified; logging never blocks a response.

### P3.T3.S3: Build the admin analytics panel

**Description:** Surface crawler activity in the admin dashboard.

**Implementation Hints:** Table of recent hits filterable by agent, plus a count-by-agent-per-week summary. State the undercount caveat **in the UI**, not only in documentation — otherwise you will eventually misread the numbers as traffic.

**Dependencies:** P3.T3.S2
**Effort:** M / 3 hrs
**Acceptance Criteria:** Panel lists hits, filters by agent, and displays the undercount caveat.

---

## Task P3.T4: Design Pass & Re-skin

**Feature:** F28 · **Effort:** L / 2–3 days · **Dependencies:** P3.T1 · **Risk:** Medium

The "UI last" strategy pays off here — or reveals that tokens leaked.

### P3.T4.S1: Generate the full design in Stitch

**Description:** Produce the complete screen set now that every page exists and its real content is known.

**Implementation Hints:** Generate against actual pages rather than imagined ones — overview per audience, timeline, projects list and detail, skills, certifications, collections, prose, contact, and the intro-to-selector sequence. Export the updated `DESIGN.md`. **Take the tokens, not the HTML.** Stitch emits HTML and Tailwind; refactoring that into your existing components would discard working code to gain a stylesheet.

**Dependencies:** P0.T5.S1
**Effort:** M / 4 hrs
**Acceptance Criteria:** `docs/DESIGN.md` updated with the full token set; no Stitch HTML imported.

### P3.T4.S2: Swap tokens and audit for leakage

**Description:** Update the token values and verify the site re-skins without touching component code.

**Implementation Hints:** Update CSS custom properties in `globals.css` for both apps. **The audit is the real test:** grep for hex literals, `rgb(`, and Tailwind's default palette classes (`bg-slate-800`, `text-gray-400`) across all components. Every hit is a Phase 2 leak that must be converted to a token. If the site re-skins cleanly from a token swap alone, the strategy worked. If dozens of components need edits, that is the honest cost of the leaks and it lands here.

**Dependencies:** P3.T4.S1
**Effort:** M / 4 hrs
**Risk Flags:** This sub-task's actual duration is determined by discipline exercised in Phase 2, not by anything done here.
**Acceptance Criteria:**
- Site re-skins from token values alone
- Zero hex literals or default-palette classes in component code
- Both apps consistent

### P3.T4.S3: Apply layout refinements with visual regression protection

**Description:** Make the layout and spacing changes the new design implies, without silently breaking responsive behaviour.

**Implementation Hints:** Capture Playwright screenshots of every page at mobile, tablet and desktop widths **before** starting. Refine page by page, comparing after each. Layout changes late in a project break things far from where you're looking; screenshots are what surface that.

**Dependencies:** P3.T4.S2
**Effort:** L / 1–2 days
**Acceptance Criteria:** Every page matches the design at all three breakpoints; regression suite passes with reviewed diffs.

### P3.T4.S4: Polish the intro and HUD against the final palette

**Description:** Retune the animation now that real colours exist.

**Implementation Hints:** The six squares must read clearly against the new background and morph convincingly into the restyled tiles. Recheck timing — perceived speed changes with contrast, and a sequence that felt right in greyscale may feel slow or abrupt now. HUD must remain legible over every page background.

**Dependencies:** P3.T4.S3, P2 Track F
**Effort:** M / 3 hrs
**Acceptance Criteria:** Morph reads cleanly in the final palette; HUD legible on every page; total duration still ~3s.

---

## Task P3.T5: Accessibility & Performance

**Effort:** M / 1–2 days · **Dependencies:** P3.T4 · **Risk:** Medium

### P3.T5.S1: Audit contrast, including dimmed content

**Description:** Verify WCAG AA across the final palette, with particular attention to dimmed entries.

**Implementation Hints:** Dimmed timeline and project entries are the specific risk — they are deliberately de-emphasised but remain content people may want to read, and reduced opacity against a dark background degrades contrast fast. Measure the *composited* result, not the token value. If AA can't be met at the intended opacity, dim via desaturation or scale rather than pushing opacity lower.

**Dependencies:** P3.T4.S2
**Effort:** M / 3 hrs
**Risk Flags:** Flagged since Phase 1. The final palette is when it becomes measurable.
**Acceptance Criteria:** All text meets AA, dimmed included; interactive elements meet non-text contrast.

### P3.T5.S2: Verify keyboard and screen reader navigation

**Description:** Confirm the site is usable without a mouse.

**Implementation Hints:** Tab order through intro, selector, HUD, tiles and filter chips. Intro must be skippable by keyboard. HUD category switching must be reachable and announce changes via a live region — a silent re-render tells a screen reader user nothing happened. Filter chips need proper `aria-pressed`.

**Dependencies:** P3.T5.S1
**Effort:** M / 3 hrs
**Acceptance Criteria:** Full keyboard traversal; visible focus throughout; category changes announced.

### P3.T5.S3: Check payload budget and Core Web Vitals

**Description:** Measure the cost of the client-side relevance decision made in Phase 1.

**Implementation Hints:** Because relevance resolves client-side, every content page ships its **full dataset** plus the tag map. That was the right call for caching, and the payload grows with content. Measure it now: at portfolio scale it should be trivially small, but confirm rather than assume — and if any page exceeds roughly 200KB of JSON, paginate or trim fields rather than reverting the architecture.

Run Lighthouse on the main routes. Verify images are served through `next/image` from R2, fonts are preloaded with `font-display: swap`, and no render-blocking resources remain.

**Dependencies:** P3.T4.S3
**Effort:** M / 3 hrs
**Risk Flags:** The intro sequence sits directly on the LCP path for first-time visitors. Confirm it isn't the largest contentful paint element.
**Acceptance Criteria:** Lighthouse performance ≥ 90 on main routes; no page ships an unreasonable JSON payload; LCP under 2.5s.

### P3.T5.S4: Run a full react-doctor audit

**Description:** Clear accumulated findings now that both frontends are complete.

**Implementation Hints:** `npx react-doctor@latest` across `frontend/` and `admin/`. CI has been reporting only diff-scoped issues since P0.T6.S5, so this is the first full-codebase view. Triage by severity; fix security and performance findings, log the rest.

**Dependencies:** P3.T4.S3
**Effort:** M / 3 hrs
**Acceptance Criteria:** No high-severity findings remain; deferred items logged in `docs/`.

---

## Task P3.T6: Launch Readiness

**Effort:** L / 2 days · **Dependencies:** all · **Risk:** High

### P3.T6.S1: Cut over to the custom domain and enable indexing

**Description:** Point the domain at the services, then remove `noindex`.

**Implementation Hints:** Custom domains for the frontend and the admin hostname; R2 custom domain for media. Verify TLS. **Only after every route serves correctly on the real domain**, remove `noindex` and submit the sitemap to Google Search Console. Ordering matters: enabling indexing before the domain works risks indexing a broken state.

If anything was indexed on the Railway hostname, add 301 redirects to the domain equivalents.

**Dependencies:** P3.T2, P0.T1.S2
**Effort:** M / 3 hrs
**Risk Flags:** The highest-consequence sequencing step in the project. Verify before indexing, not after.
**Acceptance Criteria:** All routes serve over HTTPS on the custom domain; `noindex` removed; sitemap submitted.

### P3.T6.S2: Enable Cloudflare Access

**Description:** Flip `CF_ACCESS_ENABLED` to restore the network gate built in Phase 1.

**Implementation Hints:** Confirm the Access application covers **both** the admin SPA and `/api/*` on one hostname before enabling — a split configuration causes CORS preflights to be redirected to the login page and fail, presenting as a CORS bug (`tech-stack-analysis.md` §6.2). Test admin login end to end through Access, then confirm the API rejects requests lacking a valid assertion.

**Dependencies:** P3.T6.S1, P1.T2.S6
**Effort:** M / 3 hrs
**Risk Flags:** Misconfiguration here locks you out of your own portal. Keep a rollback path — the env var — until it's verified working.
**Acceptance Criteria:** Admin reachable only through Access; API rejects direct requests; login works end to end.

### P3.T6.S3: Wire error tracking

**Description:** Close gap G11 so silent failures surface.

**Implementation Hints:** Sentry free tier on both FastAPI and Next.js. The failures that most need visibility are the quiet ones: revalidation webhook errors (content appears stale), Resend failures (form notifications stop), and cover-fetch errors. Alert on those specifically rather than on error volume.

**Dependencies:** P3.T6.S1
**Effort:** M / 3 hrs
**Acceptance Criteria:** Errors captured from both services; a deliberate revalidation failure raises an alert.

### P3.T6.S4: Verify backups and disaster recovery

**Description:** Close gap G12 by proving a restore works, not by assuming it does.

**Implementation Hints:** Confirm Railway's Postgres backup policy; if it isn't automatic, add the weekly `pg_dump` cron to R2. **Then actually restore a backup into a scratch database.** All your content lives here and it exists nowhere else — an untested backup is a belief, not a backup. Document the restore procedure in `docs/`.

**Dependencies:** P0.T2.S1
**Effort:** M / 3 hrs
**Risk Flags:** The one failure in this project that is genuinely unrecoverable.
**Acceptance Criteria:** Backups confirmed running; a test restore succeeded; procedure documented.

### P3.T6.S5: Complete Playwright critical journeys

**Description:** Cover the flows that must never break.

**Implementation Hints:** First visit → intro → select category → overview → timeline → filter → project → cross-link to timeline entry. Returning visit skips the intro. Category switch via HUD re-highlights without navigation. Admin: login with password and OTP → create a draft → publish → verify it appears publicly. Form submission with Turnstile.

**Dependencies:** P3.T5
**Effort:** L / 1 day
**Acceptance Criteria:** All journeys pass in CI against the production build.

### P3.T6.S6: Author the real content

**Description:** Populate the site. Not an afterthought — a site with placeholder content isn't launched.

**Implementation Hints:** Six `OverviewIntro` rows including default; full timeline; projects with attachments; skills with icons; certifications; both resume PDFs; the audience-tag mapping matrix configured with real tags; at least a few posts per collection; prose pages for Hobbies, Work Views and Investor Intro; books and anime.

This will surface content-model gaps that no amount of testing with fixtures would — a field that's too short, a section that doesn't fit, a tag vocabulary that doesn't carve the content the way you actually think about it. Budget time to act on that.

**Dependencies:** P3.T6.S1
**Effort:** L / 1 day+
**Risk Flags:** Consistently underestimated. Authoring is where the design meets reality.
**Acceptance Criteria:** Every page has real content; no tile is empty for its intended audience; the default view is complete for crawlers.

---

## Phase 3 Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Railway hostname indexed before domain cutover | Medium | **High** | `noindex` until P3.T6.S1 |
| robots.txt blocks AI crawlers | Medium | **Critical** | Explicit allow-list in P3.T2.S2 |
| Server-render invariant regressed during Phase 2 | Medium | **Critical** | `curl` suite in P3.T2.S6, added to CI |
| Token leakage makes re-skin a manual slog | Medium | Medium | Audit in P3.T4.S2; cost lands here either way |
| Dimmed content fails AA in the final palette | Medium | Medium | Composited-value measurement in P3.T5.S1 |
| Access misconfiguration locks you out | Low | High | Env-var rollback retained until verified |
| Backups never tested | Medium | **Critical** | Test restore mandated in P3.T6.S4 |
| JSON-LD invalid, silently ignored | Medium | High | Rich Results Test in acceptance criteria |

---

## Exit Checklist

- [ ] Overview renders correct tiles per audience; empty tiles omitted; default complete
- [ ] `Person` JSON-LD generated from live data and passing Rich Results Test
- [ ] Sitemap and robots correct; AI crawlers explicitly allowed
- [ ] `curl` suite passes on every public route, running in CI
- [ ] `next build` reports content routes static
- [ ] Site re-skinned; zero hardcoded colours
- [ ] WCAG AA met including dimmed content; keyboard traversal complete
- [ ] Lighthouse ≥ 90; LCP under 2.5s
- [ ] Live on the custom domain; `noindex` removed; sitemap submitted
- [ ] Cloudflare Access enabled and verified
- [ ] Sentry capturing from both services
- [ ] Backup restore tested and documented
- [ ] Playwright critical journeys green
- [ ] Real content authored across every page

---

## What Remains After Phase 3

**Phase 4 — Deep Agent Voice System (F29).** Deferred by design and scoped only after launch. The groundwork exists: the decorative percentage counter in the HUD becomes a genuine connection-status indicator, and `backend/app/features/agent/` is reserved. Constraint carried from the original document: OpenClaw is not to be used. Architecture (LangGraph or a custom deep agent) and capabilities to be designed once the standard portfolio is fully operational.
