# TD-24: Contention Protocol — Regen Script, Registry Checks, Merge Rules

**Phase:** P2 · **Wave:** 7 · **Executor:** agent · **Effort:** M (1 day)
**Source:** development-plan-P2.md → Contention Protocol
**Depends on:** TD-13, TD-21, TD-22 · **Blocks:** TD-25, TD-26, TD-27, TD-28, TD-29

## Purpose
Five shared files are touched by every parallel track: `backend/app/core/models_registry.py`,
the `backend/app/app.py` router block, the Alembic migration chain, `frontend/lib/tiles.ts`,
`frontend/lib/cacheTags.ts`. Encode the coordination rules as docs + scripts + CI so contention
is resolved mechanically. The migration chain is the highest risk: six branches each
autogenerating against the same head produce six heads on merge, and `alembic upgrade head`
then fails outright. Only five tracks carry migrations — Track F uses static audio config.

## Paths
- Create: `docs/conventions.md` (contention section), `scripts/regen_migration.sh`, `scripts/check_registries.py`
- Modify: `.github/workflows/ci.yml`
- Guarded: `backend/app/core/models_registry.py`, `backend/app/app.py`, `backend/alembic/versions/`, `frontend/lib/tiles.ts`, `frontend/lib/cacheTags.ts`

## Steps
1. Conventions doc contention section: append-zone sentinel comments in all four registry files
   (`APPEND-ZONE-START` / `APPEND-ZONE-END`, comment syntax per language), alphabetical
   insertion within the zone, conflicts resolved keep-both in canonical order. Auto-discovery
   registries considered and rejected: explicit imports keep Alembic autogenerate auditable.
2. `scripts/regen_migration.sh "<msg>"`:
   a. `git fetch origin`; assert rebased — `git merge-base --is-ancestor origin/main HEAD`, else abort with "rebase onto origin/main first"
   b. Assert clean tree (`git status --porcelain` empty)
   c. Delete the branch's own prior migrations: files in `backend/alembic/versions/` absent from `origin/main`
   d. `alembic revision --autogenerate -m "<msg>"`
   e. Round-trip on scratch docker Postgres: `alembic upgrade head` → `alembic downgrade -1` → `alembic upgrade head`
   f. Assert single head (`alembic heads` count == 1)
   Invariant: one migration per branch, always the newest.
3. `scripts/check_registries.py`: every `backend/app/features/*/models.py` imported in
   `models_registry.py`; every feature router registered in `app/app.py`; named errors
   (`UNREGISTERED_MODEL: features/x/models.py`, `UNREGISTERED_ROUTER: features/x/router.py`)
   and non-zero exit.
4. CI wiring: `check_registries.py` as a PR gate alongside the TD-13 single-head check;
   `bash -n` + shellcheck on the regen script so it cannot rot.
5. Merge queue rules in conventions.md: Track A first, then completion order; one merge at a
   time; after each merge remaining branches rebase + run `scripts/regen_migration.sh`; daily
   rebase cadence for in-flight tracks; `alembic merge heads` only as a post-merge escape
   hatch; never hand-edit `down_revision`.

## Tests
- Simulated stale branch (origin/main not an ancestor of HEAD) → regen script aborts with rebase message
- Dirty tree → regen script aborts before touching Alembic
- Two-branch scenario: branch-1's migration merges to main; branch-2 rebases + regens → `alembic heads` == 1
- Add `features/ghost/models.py` unregistered → check_registries names it; register it → check passes

## Acceptance Criteria
- [ ] conventions.md contention section merged (append zones, merge queue, rebase cadence)
- [ ] Simulated stale branch fails the regen script guard
- [ ] Two-branch merge scenario yields one head after regen
- [ ] Registry check catches a deliberately unregistered feature
- [ ] Both checks wired into the CI workflow
- [ ] Regen round-trip passes on scratch docker Postgres

## Verify
`bash scripts/regen_migration.sh "gate test" && (cd backend && uv run alembic heads) && uv run scripts/check_registries.py`

## Commit
`chore: contention protocol — regen script, registry checks, merge rules`

## Invariants
- One migration per feature branch, always generated against current `origin/main`
- Never hand-edit `down_revision`; `alembic merge heads` only as post-merge escape hatch
- Append zones: add your line, never reorder others'; conflicts keep-both in canonical order
- Only Tracks A–E carry migrations (Track F: static audio config)
