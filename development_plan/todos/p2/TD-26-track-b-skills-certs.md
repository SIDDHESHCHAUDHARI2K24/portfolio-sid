# TD-26: Track B — Skills + Certifications

**Phase:** P2 · **Wave:** 7 · **Executor:** agent · **Effort:** L (4–5 days)
**Source:** development-plan-P2.md → Track B: B.T1–B.T5
**Depends on:** TD-24 · **Blocks:** GATE-P2

## Purpose
Two low-risk content features. Skills is the simplest feature in the project (no relevance
logic at all); Certifications carries the mandatory mobile-PDF fallback and the only
real-device test in Phase 2.

## Paths
- Create: `backend/app/features/skills/...`, `backend/app/features/certifications/...` + tests
- Create: `frontend/app/skills/page.tsx`, `frontend/app/certifications/page.tsx`
- Create: admin screens (drag reorder, live icon preview, file upload)
- Modify (per TD-24 protocol): the five shared contention files

## Steps
1. **B.T1 Skill model.** `name`, `section` (LANGUAGES/TOOLS/FRAMEWORKS/AI/BUSINESS),
   `subsection` (nullable), `icon_slug` (Simple Icons slug), `icon_key` (R2 fallback),
   `sort_order`. NO topic tags and NO audience override — everyone sees everything; do not
   add the tag machinery out of habit. Icon chain at render: resolve `icon_slug` against the
   `simple-icons` npm package → fall back to `icon_key` from R2 → neutral placeholder. Tech
   sections get per-skill icons; Business sections get one icon at the sub-section head.
   Test a deliberately invalid slug through the full fallback chain.
2. **B.T2 Skills slice, page, admin.** Public page groups server-side, static sections, no
   client interactivity beyond hover. Admin groups by section with drag-to-reorder writing
   `sort_order`; the icon-slug field shows a live preview so invalid slugs are caught at
   authoring time, not on the live site.
3. **B.T3 Certification model.** `title`, `issuer`, `kind` (TECHNICAL/BUSINESS),
   `issued_date`, `expires_date` (nullable), `credential_url`, `file_key`, `file_type`
   (PDF/IMAGE), topic tags and audience override. Uploads via `StorageAdapter`.
4. **B.T4 Certifications page.** Two sections; expand-to-view reveals `<iframe>`/`<object>`
   pointing at the R2 URL for PDFs, `next/image` for images. Mobile Safari and several Android
   browsers refuse inline PDFs — detect failure and show an Open/Download PDF fallback; this
   is mandatory, not a nicety. Do not reach for `react-pdf` (~300KB gzipped + worker is poor
   value for a certificate). Real-device test is a paired step on the user's phone — a
   desktop emulator does not count.
5. **B.T5 Tiles.** Skills: all audiences except Personal. Certifications: Recruiters/Founders/
   Investors/Techies. Both omitted when empty.
6. Register the tiles per the P1 contract → run `scripts/regen_migration.sh "skills+certs"` →
   pass `scripts/check_registries.py` → rebase on latest main before opening the PR.

## Tests
- Skills group correctly by section and sub-section
- Invalid slug falls back to uploaded icon, then to placeholder
- No topic-tag or override fields exist on the Skill model
- Reordering persists `sort_order`; invalid slug visible in admin before save
- Both certification kinds persist; PDF and image uploads both work; entry with neither link nor file still renders
- Expand reveals PDF/image inline on desktop; open/download fallback works on a real mobile browser
- `curl` returns full content on both pages

## Acceptance Criteria
- [ ] B.T1–B.T5 acceptance criteria above all green
- [ ] Verified on a real mobile browser (paired step, user's phone)
- [ ] Migration regenerated against latest main; single head
- [ ] Registry check passes

## Verify
`curl -s localhost:3000/skills && curl -s localhost:3000/certifications && (cd backend && uv run alembic heads) && uv run scripts/check_registries.py`

## Commit
`feat(skills,certs): models, slices, pages, mobile PDF fallback, tiles`

## Invariants
- Skill never gains topic tags or audience override
- PDF fallback is mandatory and verified on a real device, never an emulator
- Tiles registered + regen run + registry check passed before PR
