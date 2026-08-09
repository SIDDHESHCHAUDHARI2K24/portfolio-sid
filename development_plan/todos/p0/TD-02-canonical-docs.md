# TD-02: Canonical Docs Set + Conventions + Pointer Files

**Phase:** P0 · **Wave:** 0 · **Executor:** agent · **Effort:** M (half day)
**Source:** development-plan-P0.md → P0.T4.S1, P0.T4.S2
**Depends on:** TD-00 · **Blocks:** all agent-driven work (docs are the single source of truth)

## Purpose
One docs set that all four agents reference — duplicating project context per
agent guarantees drift and agents that disagree about your own architecture.
conventions.md states every non-obvious invariant explicitly: an invariant
that is not written down is not real.

## Paths
- Create: `docs/tech-stack-analysis.md`, `docs/dependency-map.md`,
  `docs/development-plan-P0.md` … `docs/development-plan-P3.md`,
  `docs/conventions.md`, `CLAUDE.md`, `AGENTS.md`, `.cursor/rules/` pointer

## Steps
1. Copy `overall_context/tech-stack-analysis.md` and `overall_context/dependency-map.md` into `docs/`
2. Copy `development_plan/development-plan-P0.md` … `development-plan-P3.md` into `docs/`
3. Write `docs/conventions.md` stating ALL invariants:
   - Overlay-not-replacement: homepage renders the full default overview in server HTML; intro/selector compose as overlays ABOVE it, never `showIntro ? <Intro/> : <Overview/>`
   - Category state lives in a cookie, never localStorage (the server must read it)
   - Never call `cookies()` inside content RSCs — cookie reads stay in the dedicated layout/wrapper so content stays cacheable
   - Feature-sliced backend; no cross-feature imports; `core/` is the only shared surface
   - boto3 only in `backend/app/core/storage.py`
   - Migrations: rebase on main then regenerate; never hand-edit `down_revision`; one migration per feature branch
   - No hardcoded colour literals — tokens only (TD-11)
   - Never `pull_request_target` with a checkout of PR code
   - Topic tags ≠ collection tags — distinct systems, never merged
   - `public_filter` is the only sanctioned public read path
   - noindex-until-launch: `NEXT_PUBLIC_INDEXABLE` defaults false (TD-04)
   - Admin SPA + API share a single hostname (admin.siddhesh-chaudhari.com)
   - All timestamps UTC
4. Write thin `CLAUDE.md` and `AGENTS.md`: one-paragraph project summary, pointer to `docs/`, the 3–4 invariants an agent must never violate — long instruction files get skimmed
5. Author them as files with managed regions: CodeGraph and react-doctor installers write marker-fenced sections into both; never hand-edit inside the markers
6. Add a `.cursor/rules/` pointer with the same content for cursor-agent
7. Re-run `codegraph install` (TD-01) once after the pointer files exist; confirm hand-written content outside the markers survives

## Tests
- All four planning docs + both context docs present in `docs/`
- `conventions.md` contains every invariant listed above (grep each one)
- CodeGraph installer run does not destroy hand-written content

## Acceptance Criteria
- [ ] `docs/` holds tech-stack-analysis, dependency-map, development-plan-P0..P3
- [ ] `conventions.md` states every invariant above
- [ ] CLAUDE.md + AGENTS.md + `.cursor/rules/` pointer exist, short, reference `docs/`
- [ ] Marker fences tolerated: installer re-run leaves hand-written prose intact

## Verify
`ls docs/ && grep -c "overlay" docs/conventions.md && wc -l CLAUDE.md AGENTS.md`

## Commit
`docs: canonical docs set, conventions invariants, agent pointer files`

## Invariants
- `docs/` is the single source of truth; pointer files stay thin
- Never hand-edit inside tool-managed marker fences
- Every invariant discovered later must be back-ported into conventions.md
