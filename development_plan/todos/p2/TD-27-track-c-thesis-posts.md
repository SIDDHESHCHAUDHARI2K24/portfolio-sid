# TD-27: Track C — Investment Thesis + Posts

**Phase:** P2 · **Wave:** 7 · **Executor:** agent · **Effort:** M (3–4 days)
**Source:** development-plan-P2.md → Track C: C.T1–C.T4
**Depends on:** TD-24 · **Blocks:** GATE-P2

## Purpose
Highest leverage per hour in Phase 2 — one model feeds three public pages. The modelling
decision is the point: collection membership (routing) and topic tags (relevance) are SEPARATE
relationships on `Post`. Conflating them would let a page-routing tag alter highlighting
across Timeline and Projects — corrupting the relevance engine site-wide.

## Paths
- Create: `backend/app/features/posts/...`, `backend/app/features/thesis/...` + tests
- Create: three thin collection routes sharing one `PostList` component; `frontend/app/thesis/page.tsx`
- Modify (per TD-24 protocol): the five shared contention files

## Steps
1. **C.T1 Post model.** `title`, `summary`, `url`, `platform` enum
   (SUBSTACK/MEDIUM/YOUTUBE/OTHER), `published_date`, `collections` array of enum
   (TECH_RABBITHOLE/HOW_I_USE_AI/VC_FOR_FOUNDERS), `topic_tags` M2M, `audience_override`.
   A post may belong to several collections. Corruption risk, stated: if one vocabulary served
   both jobs, adding `how-i-use-ai` to the audience-tag map would silently change highlighting
   everywhere. Keep the enum array and the M2M strictly separate.
2. **C.T2 Three themed pages.** Three thin routes sharing one `PostList` component — never
   three page implementations. Link cards show title, summary, platform badge, date, opening
   externally with `rel="noopener noreferrer"`. Highlight/dim via the standard client
   relevance resolver.
3. **C.T3 Thesis slice.** `Thesis`: `title`, `summary`, `drive_url`, `published_date`, topic
   tags, override. Follows the certifications visual pattern but links out, never iframes —
   Drive documents cannot be reliably iframed and produce a blank frame for anyone not signed
   in. Set Drive sharing to "anyone with the link"; permission walls fail silently for
   visitors while working perfectly for you. Verify every link in a logged-out browser.
4. **C.T4 Tiles.** Tech Rabbithole: all five audiences. How I Use AI: Techies/Founders/
   Recruiters/Investors. VC for Founders: Founders. Investment Thesis: Investors.
5. Register the tiles per the P1 contract → run `scripts/regen_migration.sh "thesis+posts"` →
   pass `scripts/check_registries.py` → rebase on latest main before opening the PR.

## Tests
- A post assigned to two collections appears on both pages
- Collection membership does not affect relevance resolution
- All three pages render from one component; `curl` returns full content on each
- Thesis entries render as cards linking out; verified in a logged-out browser
- Every external link carries `rel="noopener noreferrer"`

## Acceptance Criteria
- [x] C.T1–C.T4 acceptance criteria above all green
- [x] `collections` enum array and `topic_tags` M2M are separate relationships in the schema
- [x] Migration regenerated against latest main; single head
- [x] Registry check passes

## Verify
`curl -s localhost:3000/tech-rabbithole && curl -s localhost:3000/how-i-use-ai && curl -s localhost:3000/thesis && (cd backend && uv run alembic heads) && uv run scripts/check_registries.py`

## Commit
`feat(posts,thesis): models, themed pages, thesis slice, tiles`

## Invariants
- Collections (routing) never share vocabulary or a relationship with topic tags (relevance)
- Thesis links out to Drive; never iframe
- Tiles registered + regen run + registry check passed before PR
