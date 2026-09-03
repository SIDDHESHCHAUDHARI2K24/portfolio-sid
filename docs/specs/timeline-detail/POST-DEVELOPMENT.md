# Post-Development — Timeline Detail + Reverse Project Linking (Option 2)

**Date:** 2026-08-30 · **Plan:** `docs/specs/timeline-detail/PLAN.md:1` · **User decision:** Option 2 (experience gets its own page, shows brief experience + linked projects → `/projects/{slug}`)

## Codegraph evidence (rechecked before code)
- `backend/app/features/projects/models.py:53` `timeline_entry_id` FK `SET NULL`
- `frontend/features/projects/components/ProjectDetail.tsx:83` already links `Project → Timeline` via `/timeline#entry-{id}` (TimelineClient:40 ring + FilterChips clear)
- Missing reverse: `frontend/app/timeline/page.tsx` only list, no `[id]`; `TimelineClient:102` renders one `article id=entry-{id}`; no projects fetched

## Changes
### Backend
- `backend/app/features/timeline/repository.py:43` `get_public(session, entry_id)` enforces `public_filter(TimelineEntry)` (draft/future-scheduled → 404)
- `backend/app/features/timeline/service.py:58` `get_public_dict` wrapper (admin `get_dict` unchanged)
- `backend/app/features/timeline/endpoints/router.py:37` `get_public` now delegates to `get_public_dict`; `list_public_projects:47` `GET /{entry_id}/projects` checks timeline public then `projects_service.list_public_by_timeline_dict`; `create/patch/delete:70` revalidate `[TIMELINE, PROJECTS]`
- `backend/app/features/projects/repository.py:50` `list_public_by_timeline(session, entry_id)` where `timeline_entry_id==id && public_filter(Project)`
- `backend/app/features/projects/service.py:77` `list_public_by_timeline_dict`
- `backend/app/features/projects/endpoints/router.py:9` revalidate `[PROJECTS,TIMELINE]`
- `backend/app/app.py:1` no manual edit (auto-registered via existing timeline/projects routers)
- `backend/openapi.json:1` regenerated (98113 bytes, new path `/api/v1/timeline/{entry_id}/projects`)

### Frontend
- `frontend/app/timeline/[id]/page.tsx` (new RSC): `generateMetadata:18` fetch `apiFetch /timeline/{id}` tag `timeline` revalidate 3600, canonical `/timeline/{id}`; `TimelineDetailPage:43` fetch entry + `projects:53` `apiFetch /timeline/{id}/projects` tags `[timeline,projects]`; `ReactMarkdown` summary + highlights list + topic_tags chips + external_url + related projects card grid linking to `/projects/{slug}` (hidden when empty); back nav `← All Timeline` + hash link `#entry-{id}`; JSON-LD `buildTimelineEntryJsonLd` + `buildBreadcrumbJsonLd:77`; no `cookies()` so static ISR, `revalidate 3600`
- `frontend/components/timeline/TimelineClient.tsx:126` title now `Link href=/timeline/{id}` preserving `id=entry-{id}:112` anchor for backwards hash
- `frontend/lib/jsonld.ts:77` added `buildTimelineEntryJsonLd` + `buildBreadcrumbJsonLd`
- `frontend/app/sitemap.ts:62` fetches `/timeline` and pushes `/timeline/{id}` with `lastModified`
- `admin/src/routes/timeline/TimelineList.tsx:7` added EyeIcon view link `href=/timeline/{id} target=_blank`
- `frontend/src/api.d.ts:916` + `admin/src/api.d.ts` regenerated

## Verification
- `uv run --project backend pytest backend/app/features/timeline/tests/test_timeline.py backend/app/features/projects/tests/test_projects.py -q` → **27 passed** (incl. `test_public_detail_excludes_draft`, `excludes_future_scheduled`, `returns_published`, `admin_detail_returns_draft`, `timeline_projects_filters`; revalidation expects `[["timeline","projects"]]` and `[[projects,timeline]]`)
- `npm run build --prefix frontend` → compiled, route `ƒ /timeline/[id]` dynamic ISR (no cookies), `○ /timeline` static, `○ /sitemap.xml` static
- `grep -R cookies() frontend/app/timeline/[id]/page.tsx` → 0 hits (invariant 3 preserved)
- `sitemap.ts` now includes timeline detail URLs

## Open items you are being asked about (per your "ask me more context")
1. **ID vs slug:** Implemented UUID (`/timeline/{uuid}`) as zero-migration default. If you want readable `/timeline/feenix-sports-2026` slugs, we add `timeline_entries.slug` migration (unique, backfill from title+start_date) — tell me to switch.
2. **List→detail interaction:** Title is now a link to detail while keeping `id=entry-{id}` anchor. If you prefer inline expansion instead of navigation, we can add a disclosure.
3. **Projects placement:** Related projects render as bottom card grid. If you want them interleaved inside highlights prose, say so.
4. **Umbrella detail:** Umbrella entry also gets a detail page (same template) — can hide via admin draft or we add `is_umbrella` flag to skip.
5. **Draft visibility:** Detail 404s for drafts — confirm desired (currently correct per public_filter).
6. **D2 follow-up:** `Show everything` already removed from HUD + intro (this tracks's companion change in `docs/specs/resume-consolidation/POST-DEVELOPMENT.md`); `default` stays for crawler SSR only. Confirm no reset mechanism is desired, or propose hidden `?clear=1` route.
