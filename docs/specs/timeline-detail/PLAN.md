# Plan — Timeline Detail Page + Reverse Project Linking (Option 2)

**Status:** DRAFT for your review — derived from codegraph + grep investigation below  
**Decision:** D7 = Option 2 (per 2026-08-30: each experience gets its own page, shows brief experience + linked projects, click through to ` /projects/{slug}`)

---

## 1. Codegraph / grep evidence (current wiring)

### 1.1 Project → Timeline (exists, one-way)
- `backend/app/features/projects/models.py:53` — `timeline_entry_id` FK `ondelete SET NULL` (nullable, never CASCADE)
- `frontend/features/projects/lib/types.ts:22` — `Project.timeline_entry_id: string | null`
- `frontend/features/projects/components/ProjectDetail.tsx:83` — `href=/timeline#entry-{project.timeline_entry_id}` with hash-clear + 2 s ring (`frontend/components/timeline/TimelineClient.tsx:40` clears `FilterChips` on `#entry-` hash and scrolls/ring-highlights)
- Admin ownership: `admin/src/routes/projects/ProjectForm.tsx:18` has `TimelineEntry {id,title,organisation}` picker; projects own the link, timeline does not edit it — matches `development-plan-P2.md: A.T1` assumption A9 (one experience per project)

### 1.2 Timeline → Projects (missing, the gap)
- `backend/app/features/timeline/endpoints/router.py:37` — `GET /api/v1/timeline/{entry_id}` **exists** (public, per `TimelineEntryPublic`), but uses `service.get_dict` which calls `repository.get` **without** `public_filter` — so draft entries leak if hit directly (public list filters via `repository.list_public:18`, detail does not). Fix required.
- No `GET /api/v1/timeline/{entry_id}/projects` and no projects fetched inside `frontend/app/timeline/page.tsx:25` or `TimelineClient.tsx:1`.
- Frontend has no detail route: `frontend/app/` contains `timeline/page.tsx` only (list + `TimelineClient`), no `timeline/[id]/page.tsx`. Grep `frontend/app/timeline` → one file. So the inline timeline card cannot show linked projects.

### 1.3 Audience / contact / "show all" (your D2)
- `frontend/components/hud/HUD.tsx:7` — `CATEGORIES = recruiters/techies/investors/founders/personal` (5 tiles, no default), plus explicit `Show everything` button `HUD.tsx:53` when `category != null`
- `frontend/components/intro/IntroOverlay.tsx:19` — `CATEGORY_TILES` has `all` = "Show everything — See it all"
- `frontend/config/tileArrangement.ts:1` — `default` entry holds all 15 tiles (crawlers + unfiltered view); tile grid `TileGrid.tsx:22` falls back to `default` when `category == null`
- `frontend/components/tiles/ContactTile.tsx:9` — `audiences: []` = visible to all (your "Contact should be present for everyone" already true)

**Implication of your "hide Show everything":** `default` audience must remain for crawlers/first visit (SEO `Person` JSON-LD crawlers see overview), but selector should not expose a user-facing way to return to it once a category is chosen. Need to decide what the post-selection "no-category" state means ergonomically.

---

## 2. Proposed design — Timeline Detail Page (Option 2)

### 2.1 Information architecture
- **List stays** at `/timeline` (chronological vertical, education+experience interleaved, dim vs relevant via `CategoryProvider` + `isRelevant`). No change.
- **New detail page** at `/timeline/[id]` (UUID, matches backend param `entry_id: UUID`). Trade-off: UUID URLs are ugly but stable and require no migration; a slug field would need `timeline_entries.slug` + backfill. **Default to UUID** unless you want slugs.
- **Content on detail:**
  - Header: `title at organisation · location`, dates (`Present` when `end_date==null`), `kind` badge (education vs experience)
  - `summary` as `ReactMarkdown + rehypeSanitize + remarkGfm` (already used in `TimelineClient.tsx:140`)
  - `highlights` as ordered list (same styling)
  - `topic_tags` chips
  - `external_url` if present
  - **Related projects section**: cards for every `Project` whose `timeline_entry_id == entry.id` and whose `public_filter(Project)` passes (draft projects hidden publicly, visible in admin). Cards show title/summary + tags, link to `/projects/{slug}`. Empty state hidden.
  - Navigation: back link `← All Timeline` + sibling nav? (optional)
- **Linking:** list entries gain a affordance linking to detail (e.g., title as `Link href=/timeline/{id}`) while keeping the existing anchor `#entry-{id}` for project → timeline scroll. Detail also links back to `#entry-{id}` hash for returning context.

### 2.2 Backend changes
- Fix `timeline/endpoints/router.py:37.get_public` to enforce public visibility: call a new `service.get_public_dict` that checks `public_filter` (or 404 if `status != published && not scheduled-past`), so draft timeline entries don't leak via detail URL. Tests: public GET draft → 404, admin GET → 200.
- Add `GET /api/v1/timeline/{entry_id}/projects` (public) — queries `select(Project).where(Project.timeline_entry_id == entry_id).where(public_filter(Project)).options(selectinload(topic_tags), selectinload(attachments)).order_by(Project.sort_order)` — tag `PROJECTS` + `TIMELINE` for revalidation? Or simply let the frontend fetch the entry + `GET /timeline/{id}/projects` in one RSC `Promise.all`. Alternative: embed `projects: ProjectPublic[]` inside the timeline detail response (avoids second fetch but couples features — feature-sliced rule discourages). **Prefer separate endpoint** (keeps slices disjoint, matches existing `admin/timeline` vs `admin/projects` split).
- Alternatively re-use existing `GET /api/v1/projects` filtered client-side by `timeline_entry_id` — no new endpoint but costs shipping all projects to detail page. For correctness + perf, **new scoped endpoint** is preferred.
- Revalidation: `POST /api/v1/admin/timeline/{id}` and `.../projects/{id}` both revalidate `TIMELINE` + `PROJECTS` (already wired per router `revalidate([TIMELINE])` — add cross-tag where needed).

### 2.3 Frontend changes
- `frontend/app/timeline/[id]/page.tsx` (RSC):
  ```tsx
  const entry = await apiFetch<TimelineEntryDetail>(`/timeline/${id}`, {tags:[CACHE_TAGS.timeline]});
  const projects = await apiFetch<Project[]>(`/timeline/${id}/projects`, {tags:[CACHE_TAGS.timeline, CACHE_TAGS.projects]});
  // generateMetadata title = `${entry.title} — ${entry.organisation} — Siddhesh Chaudhari`
  // canonical /timeline/{id}, JSON-LD: CreativeWork or extra Person worksFor
  ```
- Add `/timeline/[id]/page.tsx` to `sitemap.ts` (previously timeline list + projects list; now per-entry pages) — iterate `list_public` entries.
- List page `TimelineClient.tsx:126` title becomes `Link href=/timeline/{entry.id}` wrapping `h2`, preserving `id=entry-{id}` anchor for backwards hash links.
- Detail page uses `buildCreativeWorkJsonLd` style or reuses `Project` JSON-LD pattern; include breadcrumb.

### 2.4 Admin
- No change to `TimelineForm` or `ProjectForm` — link ownership stays with `Project.timeline_entry_id`. Optional admin quality-of-life: `TimelineList.tsx` detail link `View → /timeline/{id}` + count badge of linked projects.

### 2.5 Invariants
- `next build` must still report content routes static — detail page is **static** (no `cookies()`), data fetched via `apiFetch` with tags.
- `public_filter` as sole sanctioned public path (`conventions.md:8`) — detail enforces it.
- Cache tags shared constants (`conventions.md:11`) — new endpoint reuses `TIMELINE`/`PROJECTS`.

---

## 3. Open items / "ask me more context" (your words)

1. **ID vs slug:** Keep UUID (`/timeline/a1b2-...`) or add `timeline_entries.slug` (e.g., `feenix-sports-2026`) for readable URLs? UUID is zero-migration; slug is nicer for sharing/SEO but requires migration + uniqueness.
2. **List → detail interaction:** Should clicking a timeline row navigate to detail (new URL) or expand inline? Proposal: navigate (distinct page, crawlable).
3. **Projects placement:** Inside experience page, should related projects render as a compact card grid at bottom, or as inline prose links inside highlights?
4. **Umbrella entry detail:** Should the umbrella `Purdue Data Mine — Umbrella` get its own detail page (with its own highlights) or link elsewhere / hide?
5. **Scheduling:** Draft/scheduled timeline entries should detail 404 publicly — confirm?
6. **Contact / "Show everything" (D2):** You said hide "show all". Should clearing category become impossible (once chosen, persists until cookie expiry/manual clear), or should HUD offer a different reset (e.g., only via long-press / settings route)? Default proposal: **remove `Show everything` button and `all` tile** but keep `default` for unauthenticated/crawler visits only. First visit after `intro-seen` goes straight to selector and must choose — no default page rendered for chooser? Need your intent on default visibility.

---

## 4. Effort & dependencies

- Backend endpoint + public-filter fix: ~2 h + tests (real Postgres, no mock DB per `conventions.md` style)
- Frontend RSC detail page + `sitemap.ts` + list link + markdown: ~3 h
- Verification: `pytest app/features/timeline app/features/projects`, `npm run build` static check, SSR `curl /timeline/{id}` contains highlights, Playwright journey list → detail → project → back

**Blocks:** none beyond `resume_canon.json` seeding — can proceed in parallel with resume sub-agents. Requires `timeline` + `projects` tables (already migrated) and `CACHE_TAGS` consistency.
