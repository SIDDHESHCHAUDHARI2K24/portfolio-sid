# TD-25: Track A — Projects (Critical Path, Merges First)

**Phase:** P2 · **Wave:** 7 · **Executor:** agent · **Effort:** L (4–5 days)
**Source:** development-plan-P2.md → Track A: A.T1–A.T4 (F14)
**Depends on:** TD-24 · **Blocks:** GATE-P2; first in the P2 merge queue

## Purpose
The only content feature with a hard dependency on Timeline, via the experience cross-link.
Start it first, merge it first: Track A is the critical path for Phase 2.

## Paths
- Create: `backend/app/features/projects/{models,repository,service,schemas,router}.py` + tests
- Create: `frontend/app/projects/page.tsx`, `frontend/app/projects/[slug]/page.tsx`
- Create: admin Project CRUD screen + `AttachmentUploader` component
- Modify (per TD-24 protocol): `models_registry.py`, `app/app.py` router block, Alembic chain, `tiles.ts`, `cacheTags.ts`

## Steps
1. **A.T1 Model.** `Project` with standard mixins: `title`, `slug` (unique), `summary`,
   `description` (markdown), `timeline_entry_id` nullable FK `ondelete="SET NULL"` (CASCADE
   would silently delete projects when an experience is removed), `video_url`, `topic_tags`
   M2M, `audience_override`. `ProjectAttachment` one-to-many: `project_id`, `kind`
   (PDF/PPT/IMAGE), `storage_key`, `label`, `sort_order` — one-to-many not JSONB so files are
   individually replaceable and deletable. Uploads via `StorageAdapter` with content-hashed
   keys. Reverse Experience→Projects link is derived from the FK, no schema (assumption A9).
2. **A.T2 Slice + admin.** Mirror `features/timeline/`: repository, service, schemas, router.
   Public `/api/v1/projects`; admin `/api/v1/admin/projects` with router-level `require_admin`.
   Eager-load tags + attachments with `selectinload`. Admin reuses shared fields
   (`TagSelect`, `AudienceOverrideSelect`, `PublishStatusField`, `MarkdownField`) plus a new
   `AttachmentUploader` and an experience picker populated from the timeline endpoint. Writing
   a new status selector means the P1 extraction failed — fix it there, never duplicate.
3. **A.T3 Public pages.** `app/projects/page.tsx` as RSC; client component applies relevance
   highlight/dim. Detail at `[slug]`: markdown description, attachment list, video. Embed
   YouTube via `youtube-nocookie.com` with `loading="lazy"` (no cookies before playback).
   Experience cross-link → `/timeline#entry-{id}` with scroll-to and brief highlight; clear
   filter chips on anchor navigation or the link can land on a hidden entry.
4. **A.T4 Tile.** Latest project by date as summary; audiences Recruiters/Techies/Investors/
   Founders; omitted for Personal; omitted entirely when no published projects exist.
5. Register the tile per the P1 contract → run `scripts/regen_migration.sh "projects"` → pass
   `scripts/check_registries.py` → rebase on latest main before opening the PR.

## Tests
- Project persists with and without a linked experience
- Deleting a linked experience nulls the FK and preserves the project
- Full CRUD with auth assertions; drafts excluded publicly
- Constant query count regardless of project count (eager loading)
- Attachment upload and delete both work end to end via StorageAdapter
- `curl` returns all published projects in HTML
- Cross-link scrolls to and highlights the correct timeline entry; chips cleared
- Video embeds lazily and sets no cookies before playback

## Acceptance Criteria
- [ ] A.T1–A.T4 acceptance criteria above all green
- [ ] Tile renders for the four professional audiences, absent for Personal, disappears when empty
- [ ] Migration regenerated against latest main; single head
- [ ] Registry check passes

## Verify
`curl -s localhost:3000/projects && curl -s localhost:8000/api/v1/projects && (cd backend && uv run alembic heads) && uv run scripts/check_registries.py`

## Commit
`feat(projects): model, slice, admin CRUD, public pages, tile`

## Invariants
- `SET NULL` on the timeline FK, never CASCADE
- No new copies of shared admin fields — fix the P1 extraction instead
- Tile registered + regen run + registry check passed before PR
