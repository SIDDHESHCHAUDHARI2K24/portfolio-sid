# Development Plan — Phase 2: Parallel Replication

**Document 3 of 3, Part 3** · Companions: `tech-stack-analysis.md`, `dependency-map.md`, `development-plan-P0.md`, `development-plan-P1.md`
**Status:** Draft for approval
**Feature IDs:** F14–F20, F22–F24, F26

---

## Phase Overview

**Goal:** Replicate the spine pattern across every remaining content feature, in six tracks that touch disjoint file sets and can proceed concurrently in any combination.

**Entry criteria:** Phase 1 exit checklist complete. Specifically: the tile contract is documented with a worked example, shared admin field components are extracted, and `public_filter` is the only sanctioned public read path. Starting Phase 2 without these means six tracks inventing six conventions.

**Exit criteria:**
- Every content type has a model, public page, admin CRUD screen and overview tile
- Every public page returns full content to `curl`
- Every content type respects draft/scheduled state
- The intro sequence plays once per session and never on category switch
- `alembic heads` returns one head after all tracks merge

**Estimated effort:** 25–35 days sequential; **12–18 days** with tracks genuinely parallelised. Track A is the critical path.

| Track | Features | Effort | Blocked by |
|---|---|---|---|
| **A** | Projects | L / 4–5 days | P1 complete (schema FK) |
| **B** | Skills, Certifications | L / 4–5 days | P1 complete |
| **C** | Investment Thesis, Posts | M / 3–4 days | P1 complete |
| **D** | Collections, ProsePages | L / 5–6 days | P1 complete |
| **E** | Resume, Forms | L / 4–5 days | P1 complete |
| **F** | Intro sequence, Audio | L / 4–5 days | **Can start during P1** |

---

## Contention Protocol

Feature-slicing makes most of this genuinely disjoint. Five files are not, and every track touches them. Treat these as the only coordination points:

| Shared file | Contention | Protocol |
|---|---|---|
| `app/core/models_registry.py` | One import line per feature | Add your line, never reorder others |
| `app/app.py` router registration | Two lines per feature | Append only; alphabetical within the block |
| Alembic migration chain | **Highest risk** | Rebase on `main` and **regenerate** immediately before opening the PR. Never merge a migration generated against a stale head |
| `frontend/lib/tiles.ts` tile registry | One entry per feature | Append only |
| `frontend/lib/cacheTags.ts` | One constant per feature | Append only |

The migration chain is the one that will actually bite. Six branches each autogenerating against the same head produces six heads on merge, and `alembic upgrade head` then fails outright. The CI check from P0.T6.S4 catches it; the rebase-and-regenerate discipline prevents it.

**Every track ends the same way:** register the feature's tile per the P1 contract. That is what keeps F21 from becoming a big-bang integration.

---

## One Modelling Decision That Affects Two Tracks

`Post` (Core A) carries tags doing two unrelated jobs, and conflating them would corrupt the relevance engine.

**Topic tags** (`#ai`, `#fundraising`, `#engineering`) drive audience relevance — the highlight/dim mechanism from P1.T3.

**Collection tags** (`tech-rabbithole`, `how-i-use-ai`, `vc-for-founders`) decide *which page an entry appears on*. These are routing, not relevance.

If one vocabulary serves both, then adding `how-i-use-ai` to the audience-tag map silently changes highlighting across Timeline and Projects too. Model them as separate relationships: `Post.collections` (an enum set) and `Post.topic_tags` (the shared `TopicTag` many-to-many). Same distinction applies to `ProsePage.group` in Track D.

---

## Track A: Projects

**Feature:** F14 · **Effort:** L / 4–5 days · **Critical path** · **Risk:** Medium

The only content feature with a hard dependency on Timeline, via the experience cross-link. Start it first.

### A.T1: Model projects with experience linkage and media

**Description:** Model projects with an optional foreign key to `TimelineEntry`, plus optional media attachments — links, video, and PDF or PPT files.

**Implementation Hints:** `app/features/projects/models.py` — `Project` inheriting the standard mixins, with `title`, `slug` (unique), `summary`, `description` (markdown), `timeline_entry_id` (nullable FK, `ondelete="SET NULL"` — deleting an experience must not delete project history), `video_url`, `topic_tags` M2M, `audience_override`. Separate `ProjectAttachment` table: `project_id`, `kind` (`PDF`/`PPT`/`IMAGE`), `storage_key`, `label`, `sort_order` — one-to-many rather than JSONB, so files are individually replaceable and deletable. The reverse link (Experience → its Projects) is derived from the FK and needs no schema (assumption A9: one experience per project).

**Dependencies:** P1.T5.S1
**Effort:** M / 4 hrs
**Risk Flags:** `CASCADE` on the timeline FK would silently delete projects when an experience is removed. `SET NULL` is correct.
**Acceptance Criteria:**
- Project persists with and without a linked experience
- Deleting a linked experience nulls the FK and preserves the project
- Attachments upload via `StorageAdapter` with content-hashed keys

### A.T2: Build API, service and admin CRUD

**Description:** Implement the backend slice and admin screens, following the P1 template exactly.

**Implementation Hints:** Mirror `features/timeline/` structure: `repository.py`, `service.py`, `schemas.py`, `router.py`. Public router `/api/v1/projects`, admin `/api/v1/admin/projects` with router-level `require_admin`. Eager-load tags and attachments with `selectinload`. Admin form reuses the shared field components from P1.T8.S3 — `TagSelect`, `AudienceOverrideSelect`, `PublishStatusField`, `MarkdownField` — plus a new `AttachmentUploader` and an experience picker populated from the timeline endpoint.

**Dependencies:** A.T1
**Effort:** L / 1–2 days
**Risk Flags:** If you find yourself writing a new status selector rather than importing one, the P1 extraction failed and should be fixed there rather than duplicated here.
**Acceptance Criteria:**
- Full CRUD with auth assertions; drafts excluded publicly
- Constant query count regardless of project count
- Attachment upload and delete both work end to end

### A.T3: Build the public projects page

**Description:** Render projects with highlight/dim and navigation into the linked timeline entry.

**Implementation Hints:** `app/projects/page.tsx` as an RSC; client component applies relevance. Detail view at `app/projects/[slug]/page.tsx` with markdown description, attachment list, and video. Embed YouTube via `youtube-nocookie.com` with `loading="lazy"` — the privacy-preserving domain avoids setting cookies until playback and costs nothing. The experience cross-link navigates to `/timeline#entry-{id}` with scroll-to and a brief highlight so the target is obvious on arrival.

**Dependencies:** A.T2, P1.T6.S4
**Effort:** L / 1–2 days
**Risk Flags:** An anchor link into a client-filtered timeline can land on a hidden entry if filter chips are active. Clear chips on anchor navigation.
**Acceptance Criteria:**
- `curl` returns all published projects in HTML
- Cross-link scrolls to and highlights the correct timeline entry
- Video embeds lazily and sets no cookies before playback

### A.T4: Register the projects tile

**Description:** Contribute the projects tile to the overview registry per the P1 contract.

**Implementation Hints:** Latest project by date as summary; audiences: Recruiters, Techies, Investors, Founders. Omitted for Personal per your operating description. Omitted entirely when no published projects exist.

**Dependencies:** A.T3, P1.T7.S4
**Effort:** S / 2 hrs
**Acceptance Criteria:** Tile renders for the four professional audiences, is absent for Personal, and disappears when empty.

---

## Track B: Skills & Certifications

**Effort:** L / 4–5 days · **Risk:** Low

### B.T1: Model and build skills

**Description:** Model skills grouped into sections and sub-sections, with icons at the level where they exist.

**Implementation Hints:** `Skill` with `name`, `section` (`LANGUAGES`, `TOOLS`, `FRAMEWORKS`, `AI`, `BUSINESS`), `subsection` (nullable — e.g. "Product Management & Operations", "Consulting & Venture Capital"), `icon_slug` (Simple Icons slug), `icon_key` (R2 fallback), `sort_order`. **Skills carry no relevance logic** — everyone sees everything, so no topic tags and no override. That makes this the simplest feature in the project; do not add the tag machinery out of habit.

**Icon strategy matters here:** Simple Icons covers *brands* only. Python, React and Docker resolve; "Stakeholder Management" and "Financial Modelling" never will. Hence your design decision — tech sections get per-skill icons, Business sections get one icon at the sub-section head. Resolve `icon_slug` against the `simple-icons` npm package at render time; fall back to `icon_key` from R2; fall back to a neutral placeholder.

**Dependencies:** P1.T1.S4
**Effort:** M / 4 hrs
**Risk Flags:** A missing Simple Icons slug renders as a broken image unless the fallback chain is complete. Test with a deliberately invalid slug.
**Acceptance Criteria:**
- Skills group correctly by section and sub-section
- Invalid slug falls back to uploaded icon, then to placeholder
- No topic-tag or override fields exist on this model

### B.T2: Skills API, page and admin

**Description:** Standard slice plus a sectioned public page.

**Implementation Hints:** Public page groups server-side and renders as static sections — no client interactivity beyond hover. Admin list groups by section with drag-to-reorder writing `sort_order`, plus an icon-slug field showing a live preview so invalid slugs are caught at authoring time rather than on the live site.

**Dependencies:** B.T1
**Effort:** M / 1 day
**Acceptance Criteria:** All sections render with icons; reordering persists; invalid slug is visible in admin before save.

### B.T3: Model and build certifications

**Description:** Model certifications with a technical/business split, optional external link, and optional embedded file.

**Implementation Hints:** `Certification` with `title`, `issuer`, `kind` (`TECHNICAL`/`BUSINESS`), `issued_date`, `expires_date` (nullable), `credential_url`, `file_key`, `file_type` (`PDF`/`IMAGE`), topic tags and override. Upload via `StorageAdapter`.

**Dependencies:** P1.T1.S4
**Effort:** M / 4 hrs
**Acceptance Criteria:** Both kinds persist; PDF and image uploads both work; entries with neither link nor file still render.

### B.T4: Certifications page with expand-to-view

**Description:** Render certifications in two sections with an expand control revealing the embedded PDF or image inline — and a fallback that actually works on mobile.

**Implementation Hints:** Native `<iframe>` or `<object>` pointing at the R2 URL for PDFs; `next/image` for images. **Mobile Safari and several Android browsers refuse to render PDFs inline** (gap G6) — detect failure and show an "Open PDF" link instead. This fallback is mandatory, not a nicety: without it the expand button silently does nothing on phones. Do not reach for `react-pdf` — roughly 300KB gzipped plus a worker file is poor value for displaying a certificate.

**Dependencies:** B.T3
**Effort:** M / 1 day
**Risk Flags:** This will look fine on your desktop and be broken on every phone unless explicitly tested on a real mobile browser.
**Acceptance Criteria:**
- Expand reveals PDF or image inline on desktop
- Mobile shows a working open/download fallback
- Verified on a real mobile browser, not a desktop emulator

### B.T5: Register both tiles

**Description:** Skills tile (all audiences except Personal) and Certifications tile (Recruiters, Founders, Investors, Techies), both omitted when empty.

**Dependencies:** B.T2, B.T4 · **Effort:** S / 2 hrs

---

## Track C: Investment Thesis & Posts

**Effort:** M / 3–4 days · **Risk:** Low

Highest leverage per hour in Phase 2 — one model feeds three public pages.

### C.T1: Model posts with collections and topic tags

**Description:** Implement Core A: external link entries routed to themed pages by collection, with topic tags driving relevance independently.

**Implementation Hints:** `Post` with `title`, `summary`, `url`, `platform` (`SUBSTACK`/`MEDIUM`/`YOUTUBE`/`OTHER`), `published_date`, `collections` (array of enum: `TECH_RABBITHOLE`, `HOW_I_USE_AI`, `VC_FOR_FOUNDERS`), `topic_tags` M2M, `audience_override`. A post may belong to several collections. Keep collections and topic tags strictly separate per the modelling note above — conflating them would let a page-routing tag alter highlighting across the whole site.

**Dependencies:** P1.T1.S4
**Effort:** M / 4 hrs
**Acceptance Criteria:** A post assigned to two collections appears on both pages; collection membership does not affect relevance resolution.

### C.T2: Build the three themed pages

**Description:** Render one page per collection from the single model.

**Implementation Hints:** One parameterised route or three thin routes sharing a `PostList` component — do not write three page implementations. Link cards show title, summary, platform badge and date, opening externally with `rel="noopener noreferrer"`. Highlight/dim applies via the standard client resolver.

**Dependencies:** C.T1
**Effort:** M / 1 day
**Acceptance Criteria:** All three pages render from one component; `curl` returns full content on each.

### C.T3: Investment thesis slice

**Description:** Standard slice for thesis entries linking to Google Drive documents.

**Implementation Hints:** `Thesis` with `title`, `summary`, `drive_url`, `published_date`, topic tags, override. Page follows the certifications visual pattern but links out rather than embedding — Drive documents cannot be reliably iframed and attempting it produces a blank frame for anyone not signed in. Remind yourself to set Drive sharing to "anyone with the link"; a thesis linking to a permission wall is worse than no thesis.

**Dependencies:** P1.T1.S4
**Effort:** M / 1 day
**Risk Flags:** Drive link permissions are the failure mode here, and they fail silently for visitors while working perfectly for you.
**Acceptance Criteria:** Entries render as cards linking to Drive; verified in a logged-out browser.

### C.T4: Register tiles

**Description:** Tech Rabbithole tile (all five audiences), How I Use AI (Techies, Founders, Recruiters, Investors), VC for Founders (Founders), Investment Thesis (Investors).

**Dependencies:** C.T2, C.T3 · **Effort:** S / 2 hrs

---

## Track D: Collections & Prose Pages

**Effort:** L / 5–6 days · **Risk:** Medium — carries the only third-party integration in Phase 2

### D.T1: Model collection items

**Description:** Implement Core B for books, anime and manhwa.

**Implementation Hints:** `CollectionItem` with `title`, `creator` (author or studio), `kind` (`BOOK`/`ANIME`/`MANHWA`), `section` (Tech/Business/Personal Development for books; unused for anime), `cover_key` (R2), `external_id`, `external_source` (`OPEN_LIBRARY`/`JIKAN`/`MANUAL`), `status` (`READING`/`COMPLETED`/`WANT_TO_READ`), `note`, `sort_order`. No topic tags — this is Personal-audience content and needs no relevance resolution.

**Dependencies:** P1.T1.S4
**Effort:** M / 4 hrs
**Acceptance Criteria:** All three kinds persist with correct sectioning; books section, anime and manhwa do not.

### D.T2: Build the cover ingestion pipeline

**Description:** On admin save, look the title up against Open Library or Jikan, download any cover found **once**, and store it in R2. Prompt for manual upload on failure.

**Implementation Hints:** `features/collections/covers.py`. Books: Open Library search API by title, then `covers.openlibrary.org/b/id/{cover_id}-L.jpg`. Anime and manga: Jikan `/v4/anime?q=` and `/v4/manga?q=`, taking the image from the top match. Both are free and keyless. Jikan rate-limits to roughly 3 req/sec — irrelevant here since lookups happen only at admin save.

**Download and store; never hotlink.** Serving directly from these hosts makes every page view depend on a third party, and Jikan is an *unofficial* MyAnimeList wrapper with no uptime guarantee. Write to R2 with a content-hashed key via `StorageAdapter`. Validate content type and cap size before writing — an endpoint returning HTML instead of an image should fail loudly, not store a 404 page as a cover.

Return a structured result so admin can distinguish "found and stored", "no match" and "lookup failed", and present manual upload for the latter two.

**Dependencies:** D.T1, P0.T3.S4
**Effort:** L / 1–2 days
**Risk Flags:** **Expect the manual path far more often for manhwa** — Jikan's coverage is thinner there than for anime, and korean titles frequently miss. Design the admin flow so manual upload is a normal path, not an error state. Also cache negative lookups briefly so re-saving an unmatched item doesn't re-query on every keystroke.
**Acceptance Criteria:**
- A known book resolves and stores a cover in R2
- An unmatched title returns "no match" and prompts upload
- API downtime returns "lookup failed" without blocking the save
- No page ever requests an image from Open Library or Jikan at render time

### D.T3: Collections API, pages and admin

**Description:** Standard slice plus two public tile pages.

**Implementation Hints:** Books page groups by section; Anime & Manhwa page has two sections. Both are image-tile grids using `next/image` against the R2 custom domain (configured in `images.remotePatterns` in P0). Admin form triggers the cover lookup on title blur, showing the result inline with an upload fallback.

**Dependencies:** D.T2
**Effort:** M / 1 day
**Acceptance Criteria:** Both pages render tile grids; images load from R2 only; lookup result is visible during authoring.

### D.T4: Model and build prose pages

**Description:** Implement Core C — markdown pages with an optional call to action.

**Implementation Hints:** `ProsePage` with `slug` (unique), `title`, `body` (markdown), `group` (`HOBBIES`/`WORK_VIEWS`/`INVESTOR_INTRO`), `cta_label`, `cta_url`, `sort_order`, standard publishing fields. Render markdown with `react-markdown` + `remark-gfm` + `rehype-sanitize` — sanitisation stays even though you are the only author, because "only trusted content reaches this renderer" is exactly the assumption that quietly stops being true.

**The Investor Intro page is a `ProsePage` and needs no new backend work** — prose describing what you offer plus the teaser for the deck-analysis project, with `cta_url` pointing at your Google Form. That is the payoff of Core C existing.

**Dependencies:** P1.T1.S4
**Effort:** M / 1 day
**Acceptance Criteria:** All three groups render; CTA appears only when both label and URL are set; markdown is sanitised.

### D.T5: Register tiles

**Description:** Books, Anime & Manhwa and Hobbies tiles (Personal only). Investor Intro tile (Founders). All omitted when empty.

**Dependencies:** D.T3, D.T4 · **Effort:** S / 2 hrs

---

## Track E: Resume & Forms

**Effort:** L / 4–5 days · **Risk:** Medium — the only track with outbound side effects

### E.T1: Model and serve resumes

**Description:** Two static PDFs mapped to audiences, with both exposed in the default view.

**Implementation Hints:** `Resume` with `variant` (`TECH`/`BUSINESS`), `label`, `file_key`, `is_active`, `updated_at`. Mapping: Recruiters and Techies → tech; Investors and Founders → business; **default view exposes both, clearly labelled** (assumption A13), because an AI parser should choose which fits its search rather than receive your guess.

Link the PDFs from `/` so they are crawlable — AI recruiting tools parse PDFs, and this is the single most machine-readable artifact on the site. Serve from R2 with the content-hashed key so replacing a resume changes its URL and no cache serves the old one.

**Dependencies:** P1.T1.S4, P0.T3.S4
**Effort:** M / 4 hrs
**Acceptance Criteria:** Correct variant surfaces per audience; both appear in the default view; PDFs are reachable and crawlable from `/`.

### E.T2: Model form submissions

**Description:** One model serving both contact and dealflow, with consent captured.

**Implementation Hints:** `FormSubmission` with `form_type` (`CONTACT`/`DEALFLOW`), `payload` (JSONB — fields differ per type), `consent_given`, `consent_text` (a **snapshot of the wording shown**, not a reference to current wording — if you later reword the consent, you must still be able to show what each person actually agreed to), `submitter_email`, `ip_address`, `user_agent`, `is_read`, `created_at`.

**Dependencies:** P1.T1.S4
**Effort:** M / 4 hrs
**Acceptance Criteria:** Both types persist; consent text is stored per submission, not referenced.

### E.T3: Build the submission endpoint

**Description:** One public endpoint handling both forms, with the full anti-abuse stack.

**Implementation Hints:** `POST /api/v1/forms/{form_type}`. Order matters: honeypot check, then Turnstile `/siteverify` via the P1.T2.S7 helper, then rate limit, **then** the database write. Verification must precede any write. Return an identical generic success response whether the submission was accepted or silently discarded, so bots learn nothing.

On success, send a Resend notification reusing the P1.T2.S3 email client. **Email failure must not fail the request** — the submission is safely stored and the person deserves a success response; log the failure at error level and surface unread submissions in admin so nothing is lost if email breaks.

**Dependencies:** E.T2, P1.T2.S7
**Effort:** M / 1 day
**Risk Flags:** Turnstile tokens expire after 300 seconds and are single-use. A form left open in a tab will fail — handle re-challenge gracefully rather than showing a raw error.
**Acceptance Criteria:**
- Honeypot submissions return success and persist nothing
- Missing or expired Turnstile token is rejected
- Rate limiting returns 429
- Resend failure logs an error and still returns success

### E.T4: Build the contact and dealflow pages

**Description:** Contact surface with email, LinkedIn, booking and form; dealflow signup form.

**Implementation Hints:** Contact page shows your **email as plain text**, not obfuscated. Obfuscation would defeat the discoverability goal — agents read the DOM, and an assembled-by-JS address is invisible to them. Include it in the `Person` JSON-LD too. Add LinkedIn and a Cal.com booking link (free tier permits multiple event types; Calendry's caps at one).

Dealflow form collects name, email, firm, focus area and the consent checkbox. Both forms embed the Turnstile widget.

**Dependencies:** E.T3
**Effort:** M / 1 day
**Acceptance Criteria:** Email is plain text in the DOM and in JSON-LD; both forms submit successfully; consent is required before dealflow submission.

### E.T5: Build the admin submissions inbox

**Description:** One screen listing both form types with read/unread state.

**Implementation Hints:** Filterable by type and read state, sorted newest first. Detail view renders the JSONB payload plus the stored consent text. Include CSV export — you chose collect-only with manual outreach, so exporting is how you actually work the list.

**Dependencies:** E.T3
**Effort:** M / 1 day
**Acceptance Criteria:** Both types listed and filterable; consent text visible per submission; CSV exports correctly.

### E.T6: Register tiles

**Description:** Contact tile — all five audiences plus default, positioned directly below the main tile, showing email and LinkedIn inline. Dealflow tile — Investors only. Resume surfaces within the contact tile rather than as its own.

**Dependencies:** E.T4 · **Effort:** S / 2 hrs

---

## Track F: Intro Sequence & Ambient Audio

**Effort:** L / 4–5 days · **Can start during Phase 1** · **Risk:** Medium

No dependency on any content model — only the app shell. Starting this early de-risks the most novel work in the project while the backend spine is still being built. The HUD itself was built in P1.T7.S5; this track fills it.

### F.T1: Port the intro animation to Framer Motion

**Description:** Rebuild the supplied HTML animation as a React component: six adjectives accumulating, six squares filling, over roughly three seconds.

**Implementation Hints:** Words appear sequentially at ~0.45s intervals and **accumulate rather than replace** — all six visible at the final frame, which is the payoff of the original. Six squares fill in step with the words, replacing the original hexagon: at completion they form a 2×3 mini-grid that becomes the selector.

Port corrections from the source: replace `window.onload` with `useEffect` (it does not fire reliably in Next.js); drop the `cdn.tailwindcss.com` script for compiled Tailwind; scope `overflow: hidden` to the intro's lifetime rather than globally, or scrolling stays broken afterwards. Keep the percentage counter as a decorative element but **relabel "Status"** to something that isn't a claim — it measures nothing today, and becomes a genuine connection indicator when the voice agent lands in Phase 4.

**Dependencies:** P0.T3.S5
**Effort:** L / 1–2 days
**Risk Flags:** The original ran 4.67s total. Target ~3s. Timing drift here is the difference between "distinctive" and "get on with it".
**Acceptance Criteria:**
- Six words accumulate and remain visible at the final frame
- Six squares fill in step and end as a 2×3 grid
- Total duration ~3s; no global style leakage after unmount

### F.T2: Implement the morph into the tile selector

**Description:** Resolve the six squares outward into the category tile grid as one continuous motion — no cut, no second animation.

**Implementation Hints:** Framer Motion shared layout animation (`layoutId`) linking each loader square to its corresponding category tile. This is why six squares replaced the hexagon: loader and selector are the same object at two scales, which is what makes the sequence continuous rather than sequential. The tile grid is responsive on all breakpoints — no separate mobile pattern.

**Dependencies:** F.T1
**Effort:** M / 1 day
**Risk Flags:** Shared layout animations across a conditional unmount are where Framer gets fragile. Keep both states mounted through the transition and animate opacity and layout rather than mounting and unmounting.
**Acceptance Criteria:** Squares morph into tiles in one continuous motion with no visible cut; grid is responsive.

### F.T3: Session bypass, reduced motion, and the overlay invariant

**Description:** Implement the three behaviours that determine whether the intro is delightful or hostile — and the one that determines whether the site is indexable.

**Implementation Hints:** Check a `sessionStorage` flag on mount; if present, skip straight to the selector. Check `prefers-reduced-motion` via Framer's `useReducedMotion` and skip entirely when set — a 3s forced animation with no escape is a genuine accessibility failure for users with vestibular sensitivity. Add click and Escape to skip.

**The invariant, restated because this is where it gets violated:** the intro renders as an **overlay above already-server-rendered content**. Never `showIntro ? <Intro/> : <Overview/>`. That conditional serves crawlers an animation instead of a portfolio and undoes the entire rationale for Next.js. It looks identical in a browser either way — verify with `curl`, not with your eyes.

**Dependencies:** F.T2, P1.T7.S3
**Effort:** M / 1 day
**Risk Flags:** Rated Critical in the P0 risk register. This sub-task is where the failure would actually occur.
**Acceptance Criteria:**
- Returning visitors within a session skip the intro
- `prefers-reduced-motion` skips it entirely
- **`curl` on `/` returns full overview content while the intro is enabled**
- Category switching never replays the intro

### F.T4: Build the ambient audio player

**Description:** Mount ambient audio in the HUD slot left in P1.T7.S5, persisting across navigation.

**Implementation Hints:** A single `<audio>` element in the root layout — the App Router preserves the root layout across client navigation, so it survives route changes. Tracks stored in R2, listed from a small admin-managed table or static config. Controls in the HUD: play/pause, volume, track switch.

Persist state (track, volume, playing) to `sessionStorage`. On a full page load the element remounts — **restore the state but do not auto-resume** (gap G10). Browsers block autoplay without a fresh gesture, and attempting it yields a caught promise rejection plus a UI that claims to be playing in silence. Restore state, require a click.

**Dependencies:** P1.T7.S5, P0.T3.S4
**Effort:** M / 1 day
**Risk Flags:** Audio must be off by default. An ambient track that starts unbidden is the fastest way to lose a visitor.
**Acceptance Criteria:**
- Audio continues uninterrupted across client-side navigation
- Full page reload restores track and volume without auto-resuming
- Off by default on first visit

---

## Phase 2 Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Alembic multiple heads on track merge | **High** | High | Rebase-and-regenerate before PR; CI single-head check |
| Collection tags conflated with topic tags | Medium | High | Separate relationships, stated in modelling note |
| Overlay invariant violated in F.T3 | Medium | **Critical** | `curl` verification in acceptance criteria |
| PDF embed silently broken on mobile | **High** | Medium | Mandatory fallback; test on a real device |
| Cover hotlinking instead of storing | Medium | Medium | Explicit prohibition; render-time request check |
| Tracks re-implement shared admin fields | Medium | Medium | Fix the P1 extraction rather than duplicating |
| Drive thesis links behind a permission wall | Medium | Medium | Verify logged out |
| Turnstile token expiry on stale forms | Medium | Low | Graceful re-challenge |

---

## Exit Checklist

- [ ] Every content type has model, page, admin CRUD and registered tile
- [ ] `curl` returns full content on every public page
- [ ] Drafts excluded and scheduled publishing verified on every type
- [ ] Projects cross-link navigates to the correct timeline entry
- [ ] Certifications expand works on desktop and falls back on real mobile
- [ ] Covers served only from R2; no third-party image requests at render
- [ ] Both forms reject bots and notify via Resend; failures logged not lost
- [ ] Email plain text in DOM and JSON-LD; resumes crawlable from `/`
- [ ] Intro plays once per session, respects reduced motion, never replays on switch
- [ ] `curl` on `/` returns overview content with the intro enabled
- [ ] Audio persists across navigation, off by default, no auto-resume
- [ ] `alembic heads` returns one head; CI green
