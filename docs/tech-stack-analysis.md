# Tech Stack Analysis — Audience-Segmented Portfolio Platform

**Document 1 of 3** · Companion documents: `dependency-map.md`, `development-plan.md`
**Status:** Draft for approval
**Supersedes:** `Portfolio_Architecture_Document.pdf` §6 (System Constraints)

---

## 1. Purpose

This document validates the chosen stack against the finalized feature set, identifies capabilities no chosen component covers, and logs every assumption made. It is the reference for all technology decisions in the development plan. Where this document conflicts with the original architecture PDF, this document wins — the PDF predates the scope decisions recorded in §7.

---

## 2. Stack Components

### 2.1 Application Layer

| Technology | Role | Notes |
|---|---|---|
| **Next.js (App Router)** | Public frontend — SSR/ISR for crawler-readable HTML, route handlers for on-demand revalidation | Replaces the PDF's Vite SPA. Non-negotiable given the discoverability requirement (§3.1) |
| **React + TypeScript** | Component layer, strict mode | Per constraint |
| **Tailwind CSS** | Styling — consumes design tokens from Stitch `DESIGN.md` | Token indirection is what makes the late re-skin cheap |
| **shadcn/ui** | Component primitives (Radix + Tailwind) | Copy-in, not a dependency — components are owned and restyleable |
| **Framer Motion** | All animation: intro sequence, tile morph, HUD collapse, page transitions | Single animation library. anime.js rejected — Framer covers the full requirement and Stitch emits no animation code either way |
| **Admin SPA (React + Vite)** | Separate build, separate deploy target | Deliberately *not* Next.js — no SEO requirement, no SSR benefit, faster builds |
| **FastAPI** | HTTP API — async handlers, Pydantic v2 validation, auto-generated OpenAPI | Per constraint |
| **uv** | Python dependency and virtualenv management | Per constraint |
| **SQLAlchemy 2.0 (async)** | ORM — `AsyncSession` over asyncpg | 2.0 style (`select()`), not legacy Query API |
| **Alembic** | Schema migrations | Async env via `run_sync` |

### 2.2 Data & Storage

| Technology | Role | Notes |
|---|---|---|
| **PostgreSQL 16** | Primary datastore — all content, tags, form submissions, audit log | Docker Compose locally, Railway Postgres in production |
| **Cloudflare R2** | Production object storage — cert PDFs, project decks, cover images, audio, resumes | Zero egress fees; S3-compatible so dev and prod share one code path |
| **MinIO** | Local development object storage | Same S3 API as R2 — no dev/prod divergence |
| **StorageAdapter** | Internal abstraction over R2/MinIO/local disk | Makes the backend swappable; guards against R2 lock-in |
| **pgbouncer** | **Not used** | Explicitly rejected — see §6.1 |

### 2.3 Infrastructure & Third-Party

| Technology | Role | Notes |
|---|---|---|
| **Railway** | Hosting — Next.js service, FastAPI service, admin service, Postgres, cron | Per constraint |
| **Cloudflare CDN** | Edge caching for the public site | Free plan; unmetered for normal web assets |
| **Cloudflare Tunnel** | Removes public inbound exposure from the admin origin | `cloudflared` as a Railway service |
| **Cloudflare Access** | Identity gate in front of the admin hostname | Free tier covers up to 50 users |
| **Cloudflare Turnstile** | Bot challenge on public forms | Free; replaces reCAPTCHA |
| **Cloudflare Web Analytics** | Traffic and verified-bot reporting | Free; privacy-preserving; no self-hosting |
| **Resend** | Transactional email — admin OTP, form notifications | Free tier: 3,000/month, 100/day. Requires verified domain + SPF/DKIM |
| **Cal.com** | Booking link on the contact page | Free tier permits multiple event types; Calendly's caps at one |
| **Open Library Covers API** | Auto-fetch book cover images at admin save time | Free, no API key |
| **Jikan API** | Auto-fetch anime/manga cover images at admin save time | Free, unauthenticated, ~3 req/sec |
| **Simple Icons** | Brand SVGs for the Skills page | npm package; upload fallback for anything missing |
| **pnpm workspaces** | Monorepo tooling — shared types and UI package across web/admin | Lighter than Turborepo for three packages |

---

## 3. Coverage Assessment

Each finalized feature mapped to the components that deliver it. Features are as agreed in brainstorming, not as written in the PDF.

### 3.1 Discoverability & SEO — *the constraint that shaped the stack*

| Capability | Covered by | Confidence |
|---|---|---|
| Crawler-readable HTML at every URL | Next.js SSR/ISR | High |
| `Person` JSON-LD on `/` | Next.js metadata + inline script | High |
| Canonical category-free URLs | Next.js routing; category held in cookie | High |
| `sitemap.xml` / `robots.txt` | Next.js `sitemap.ts` / `robots.ts` conventions | High |
| Resume PDFs reachable and parseable by AI crawlers | R2 public bucket + linked from `/` | High |
| Verified-bot visibility | Cloudflare Web Analytics | Medium — see gap G9 |

**The load-bearing constraint:** the intro animation and the category selector must render as *overlays above already-rendered content*, never as replacements. If `/` server-renders `showIntro ? <Intro/> : <Overview/>`, every crawler receives an animation instead of a portfolio, and the entire rationale for choosing Next.js collapses. This is called out again as a risk in the development plan.

### 3.2 Content Domain

| Feature | Backend | Frontend | Storage |
|---|---|---|---|
| Timeline (Education + Experience merged) | FastAPI + SQLAlchemy | Next.js RSC | — |
| Projects (+ experience cross-link) | FastAPI + SQLAlchemy | Next.js RSC | R2 (decks, video posters) |
| Skills (sectioned, iconified) | FastAPI + SQLAlchemy | Next.js RSC | Simple Icons + R2 fallback |
| Certifications (inline PDF/image expand) | FastAPI + SQLAlchemy | Next.js + native embed | R2 |
| Investment Thesis (Drive links) | FastAPI + SQLAlchemy | Next.js RSC | — |
| Core A — `Post` (external link entries) | FastAPI + SQLAlchemy | Next.js RSC | — |
| Core B — `CollectionItem` (books, anime/manhwa) | FastAPI + SQLAlchemy | Next.js RSC | R2 (covers, fetched once) |
| Core C — `ProsePage` (hobbies, work views, investor intro) | FastAPI + SQLAlchemy | Next.js + markdown renderer | — |
| `OverviewIntro` (6 rows incl. default) | FastAPI + SQLAlchemy | Next.js RSC | R2 (optional hero) |
| `Resume` (2 variants, audience-mapped) | FastAPI + SQLAlchemy | Next.js RSC | R2 |
| `FormSubmission` (contact + dealflow) | FastAPI + Turnstile + Resend | Next.js client component | — |

### 3.3 Interaction & Presentation

| Capability | Covered by | Confidence |
|---|---|---|
| Intro sequence — six words, six squares, morph to grid | Framer Motion | High |
| `sessionStorage` bypass for returning visitors | Client component | High |
| `prefers-reduced-motion` skip path | CSS media query + Framer's `useReducedMotion` | High |
| Tile-grid selector, responsive | Tailwind grid | High |
| HUD — compact selector + scroll indicator + audio control | Framer Motion + React context | High |
| Instant category swap (no animation, no navigation) | React context over cookie state | High |
| Shareable `?for=` pre-filtered links | Next.js `searchParams` + canonical tag | High |
| Highlight/dim on Timeline and Projects | Relevance engine output → CSS classes | High |
| Ambient audio persisting across navigation | Audio element in root layout + context | Medium — see gap G10 |

### 3.4 Admin & Operations

| Capability | Covered by | Confidence |
|---|---|---|
| Network-level admin gate | Cloudflare Tunnel + Access | High |
| Password + OTP second factor | **Gap G1** | — |
| CRUD for every content model | FastAPI + admin SPA | High |
| `audience_tag_map` editing (matrix UI) | FastAPI + admin SPA | High |
| Submissions inbox | FastAPI + admin SPA | High |
| Media library | StorageAdapter + admin SPA | High |
| Draft / Published / Scheduled | Postgres status + `publish_at` | Partial — **gap G3** |
| Content edit reflects on live site quickly | On-demand revalidation webhook | High |

---

## 4. Gaps Identified

Capabilities that no specified component covers. Each traces to a feature and carries a recommendation that fits the existing stack.

### G1 — Admin authentication (password + OTP)
**Needed by:** Admin Portal.
**Gap:** Cloudflare Access authenticates *identity at the edge* but issues no application session; FastAPI still needs its own auth. Nothing in the stack hashes passwords, generates OTPs, or manages sessions.
**Recommended:**
- `argon2-cffi` for the master password hash (Argon2id; bcrypt is acceptable but Argon2 is the current default recommendation).
- OTP: generate a 6-digit code server-side, store its hash with a 5-minute TTL and an attempt counter, deliver via Resend. Avoid TOTP libraries — you specified email OTP, and a stored-code flow is simpler and matches the requirement exactly.
- Session: `itsdangerous`-signed HttpOnly, Secure, SameSite=Strict cookie. A JWT is unnecessary here — there is one user, no distributed verification, and a signed session cookie is easier to revoke.
- Additionally verify the `Cf-Access-Jwt-Assertion` header against Cloudflare's public keys using `PyJWT`, so the API rejects anything that bypassed the edge. Defense in depth: even if the tunnel is misconfigured, the API refuses unauthenticated traffic.

### G2 — Rate limiting
**Needed by:** Contact form, dealflow form, admin login, OTP issuance.
**Gap:** No rate limiter specified.
**Recommended:** `slowapi` — FastAPI-native, decorator-based. Use in-memory storage initially.
**Caveat:** in-memory counters are per-process. If Railway ever runs more than one replica, limits become per-replica and effectively multiply. Given single-replica deployment (§5, A3) this is acceptable, but it must be revisited before scaling out. Login and OTP endpoints additionally need a **database-backed** attempt counter, which is replica-safe regardless.

### G3 — Scheduled publishing execution
**Needed by:** Draft/Published/Scheduled workflow.
**Gap:** A `publish_at` timestamp filters correctly at query time, but pages are statically generated and edge-cached. A post scheduled for 09:00 appears whenever the page next revalidates — not at 09:00.
**Recommended:** A **Railway cron service** running every 5 minutes that queries for items whose `publish_at` has passed while `status = 'scheduled'`, flips them to `published`, and calls the revalidation webhook for affected paths.
**Rejected alternative:** in-process APScheduler — loses its schedule on every container restart and Railway restarts containers on deploy.
**Risk if unaddressed:** "scheduled posts silently fail to appear" is an expensive bug to diagnose, because the data is correct and only the cache is wrong.

### G4 — Markdown rendering and sanitization
**Needed by:** `ProsePage`, `OverviewIntro` body, project descriptions.
**Gap:** No markdown pipeline specified.
**Recommended:** `react-markdown` + `remark-gfm` (tables, strikethrough, task lists) + `rehype-sanitize`.
**On sanitization:** you are the only author, so XSS via markdown looks like a non-risk. Include it anyway — it costs one line, and the assumption "only trusted content reaches this renderer" is exactly the kind that quietly stops being true.

### G5 — Cover image ingestion pipeline
**Needed by:** Core B (`CollectionItem`).
**Gap:** No component fetches, validates, or stores third-party images.
**Recommended:** On admin save, an async FastAPI task queries Open Library (books) or Jikan (anime/manga), and on success downloads the image once and writes it to R2 under a content-hashed key. On failure, return a flag that prompts manual upload in the admin UI.
**Explicitly not recommended:** hotlinking. Serving directly from Open Library or Jikan makes every page view depend on a third party — and Jikan is an *unofficial* MyAnimeList wrapper with no uptime guarantee. Fetch-once-and-store costs negligible storage and removes the dependency from the render path entirely.
**Expect the manual path more often for manhwa** — Jikan's coverage is thinner there than for anime.

### G6 — In-browser PDF display
**Needed by:** Certifications (expand-to-view), Investment Thesis, Resume preview.
**Gap:** No PDF viewer specified.
**Recommended:** Start with a native `<iframe>` or `<object>` pointing at the R2 URL — zero dependencies, works in every desktop browser.
**Caveat:** mobile Safari and several Android browsers refuse to render PDFs inline. A download/open-in-new-tab fallback is mandatory, not optional. Only reach for `react-pdf` (pdf.js) if you need custom controls — it adds roughly 300KB gzipped and a worker file, which is poor value for "display a certificate."

### G7 — Frontend/backend contract drift
**Needed by:** Every feature.
**Gap:** Pydantic schemas define the API; TypeScript types are written separately. They will diverge.
**Recommended:** Generate TS types from FastAPI's OpenAPI schema with `openapi-typescript`, emitted into a shared pnpm workspace package consumed by both the Next.js app and the admin SPA. Run it in CI so drift fails the build rather than surfacing in production. Use `zod` for client-side form validation only — mirroring full response schemas by hand defeats the purpose.

### G8 — Test tooling
**Needed by:** All phases.
**Gap:** No testing stack specified.
**Recommended:** `pytest` + `pytest-asyncio` + `httpx.AsyncClient` for the API; `testcontainers` or a dedicated Docker Postgres for integration tests (never mock the database for query-logic tests — the relevance engine's tag intersection is precisely where a mock would lie to you). `Vitest` + React Testing Library for components. `Playwright` for the critical journeys: intro → select → overview → sub-page, and the admin login flow.

### G9 — Per-crawler visibility
**Needed by:** Discoverability goal.
**Gap:** Cloudflare Web Analytics reports verified bot traffic but does not break down which AI crawler read which page — and edge cache hits never reach your origin, so backend logging alone undercounts.
**Recommended:** Accept Cloudflare Web Analytics as the primary source. Add a lightweight FastAPI middleware logging `user-agent` + path + timestamp to Postgres for any request that *does* reach the origin, with an admin dashboard panel filtering known agents (GPTBot, ClaudeBot, PerplexityBot, Google-Extended, CCBot). Undercounts by design; still the only view that names the crawler. Zero new infrastructure.

### G10 — Audio persistence across navigation
**Needed by:** Ambient audio player.
**Gap:** Next.js App Router preserves the root layout across route changes, so an `<audio>` element mounted there survives client-side navigation — but a full page load (direct URL entry, hard refresh) remounts it and audio stops.
**Recommended:** Mount the element in the root layout, hold playback state in a context persisted to `sessionStorage`, and on remount restore track and volume but **do not auto-resume** — browsers block autoplay without a fresh user gesture, and attempting it produces a caught promise rejection and a confusing silent-but-"playing" UI state. Restore the *state*, require a click to resume.

### G11 — Error tracking
**Needed by:** Operations.
**Gap:** None specified. A silently failing revalidation webhook or Resend call is invisible until you notice content is stale or emails stopped.
**Recommended:** Sentry free tier (5k errors/month) on both FastAPI and Next.js. If you'd rather add nothing, structured logging to stdout with Railway log retention is the minimum acceptable floor — but you will find out about failures later and less precisely.

### G12 — Database backups
**Needed by:** Operations.
**Gap:** Not addressed.
**Recommended:** Confirm Railway's Postgres backup policy for your plan at provisioning time and, if it isn't automatic, add a weekly `pg_dump` cron writing to R2. All site content lives in this database; losing it means re-authoring everything.

---

## 5. Assumptions Log

Decisions made without explicit instruction. Correct any that are wrong before the plan is executed.

| # | Assumption | Impact if wrong |
|---|---|---|
| A1 | REST over GraphQL, versioned at `/api/v1` | Low — routing only |
| A2 | No public user accounts; the only authenticated user is you | High — a visitor-account requirement would change auth, data model, and hosting |
| A3 | Single Railway replica per service initially | Medium — invalidates in-memory rate limiting (G2) |
| A4 | English only; no i18n scaffolding | Medium — retrofitting i18n after the fact is invasive |
| A5 | All timestamps stored UTC, rendered in viewer-local time | Low |
| A6 | Category state in a **cookie**, not `localStorage` | High — SSR must read the category to render the right variant server-side. `localStorage` is invisible to the server and would force client-side-only category rendering, reintroducing the SEO problem |
| A7 | Single author; no roles, permissions, or edit-collision handling | Medium |
| A8 | Timeline items carry a nullable `end_date`; null means "current" | Low |
| A9 | Projects link to at most one Experience | Low — a many-to-many is a migration if wrong |
| A10 | Certifications and Investment Thesis remain separate models despite near-identical shape | Low — an accepted cost you chose deliberately |
| A11 | Ambient audio is a small fixed set of tracks uploaded by you, not user-supplied | Low |
| A12 | Contact tile appears for all five audiences and the default view | Low |
| A13 | Resume default view (no category) exposes both variants, labelled | Low |
| A14 | Voice agent (Phase 2) is design-only in this plan; no implementation tasks | None — explicitly deferred by you |

---

## 6. Compatibility Notes

### 6.1 pgbouncer — deliberately excluded
Connection pooling middleware solves connection *exhaustion* caused by many stateless workers. With a single FastAPI replica using SQLAlchemy's built-in `QueuePool`, you will hold a handful of connections against a Railway Postgres instance permitting far more. pgbouncer would add an operational component, a failure mode, and transaction-pooling caveats (prepared statements, session state) for zero benefit at portfolio traffic. Design the DB layer so introducing it later is a connection-string change; revisit only on observed connection-limit errors.

### 6.2 Cloudflare Access and CORS — the trap
If the admin SPA is served from `admin.domain.com` and calls an API at `api.domain.com`, those are two Access applications with two cookies. CORS preflight requests against an Access-protected endpoint are redirected to the login page and fail — a confusing failure that looks like a CORS misconfiguration.
**Mitigation, and it is architectural:** serve the admin SPA and the admin API under **one hostname** (`admin.domain.com/` and `admin.domain.com/api/*`) behind a single Access application. One cookie, no cross-origin requests, no preflight. This must be decided at infrastructure setup, not discovered during integration.

### 6.3 Next.js on Railway
Set `output: 'standalone'` in `next.config.js` for a lean production container. On-demand ISR requires a long-lived Node server, which Railway provides. Note that Railway's filesystem is ephemeral: the ISR cache is discarded on every deploy, so the first request to each page after a deploy regenerates it. This is correct behavior, not a bug, but it means post-deploy latency is briefly higher.

### 6.4 Next.js Image and R2
`next/image` requires remote hosts declared in `images.remotePatterns`. Add your R2 custom domain there. Serving media from an R2 custom domain also sidesteps any question about Cloudflare's free-plan restrictions on large non-HTML files, since R2 bandwidth is a separate product with zero egress fees.

### 6.5 SQLAlchemy 2.0 async + Alembic
Use `asyncpg` as the driver. Alembic's `env.py` needs the async pattern (`connection.run_sync(context.run_migrations)`) — the default template is sync and will fail silently against an async engine. Set this up correctly in Phase 1; every later migration depends on it.

### 6.6 Next.js 15 / React 19 / shadcn
Verify shadcn component compatibility against your exact Next.js and React versions at scaffold time. shadcn components are copied into your repo rather than installed, so incompatibilities are yours to patch — cheap to fix, but better found in Phase 1 than Phase 4.

### 6.7 Resend domain verification
Resend's free tier requires a verified sending domain to deliver to arbitrary addresses. Both your use cases (OTP, form alerts) target your own inbox, so this is not blocking — but verify the domain with SPF and DKIM anyway during Phase 0. OTP emails landing in spam is a self-inflicted lockout from your own admin portal.

### 6.8 Turnstile
Requires a site key (client) and secret key (server). The server-side `/siteverify` call must happen **before** any database write, and its failure must return the same generic response as success to avoid confirming to a bot which requests were rejected.

---

## 7. Scope Deltas from the Original PDF

Recorded so the plan can be audited against the source document.

**Removed:**
- Hexagonal selector geometry → responsive tile grid (mobile parity, and it eliminates the highest-effort UI work in the project)
- Horizontal tile carousel (PDF F4) → tile grid with omission-based filtering
- Instagram embedding (PDF F9) → YouTube only; Instagram's oEmbed now requires an approved Meta app
- Hardware/device fingerprinting (PDF F11) → Cloudflare Access + password + OTP, which is stronger and has a recovery path
- External newsletter provider (PDF F6) → collect-only with manual outreach
- Outbound redirect to a separate fundraising tool (PDF F7) → Google Form plus a teaser for the unbuilt deck-analysis project
- Vite SPA → Next.js, forced by the discoverability requirement

**Added:**
- SEO/discoverability layer: SSR, JSON-LD, sitemap, canonical URLs, `?for=` shareable links
- Contact tile, contact form, and Cal.com booking
- Two audience-mapped resume PDFs
- Draft / Published / Scheduled workflow plus revalidation
- Anti-spam stack: Turnstile, honeypot, rate limiting, consent checkbox
- `OverviewIntro` model with a default row
- Unified `FormSubmission` model
- Cover-image auto-fetch with manual fallback
- Crawler analytics

**Reduced from six audiences to five:** Business folded into Investors, inheriting Investment Thesis, Dealflow/Syndication, Tech Rabbithole, and How I Use AI.

---

## 8. Open Items Carried Into `development-plan.md`

None blocking. The following are decided-by-default and flagged for correction:

- "Latest" overview tiles select by most-recent date, with a manual pin override
- Skill icons from Simple Icons, upload fallback for anything absent
- Timeline filter chips retained from PDF F5
- Experience → Projects reverse link rendered (derived, no extra schema)
- Analytics limited to Cloudflare Web Analytics plus origin-side agent logging
