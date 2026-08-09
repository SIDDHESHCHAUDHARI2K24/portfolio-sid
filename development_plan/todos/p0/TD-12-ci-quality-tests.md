# TD-12: CI — Lint/Typecheck + Unit Tests (Codegraph-Scoped)

**Phase:** P0 · **Wave:** 4 · **Executor:** agent · **Effort:** M–L (half day)
**Source:** development-plan-P0.md → P0.T6.S1, P0.T6.S2
**Depends on:** TD-03, TD-04, TD-05, TD-01 · **Blocks:** TD-13, TD-14

## Purpose
Quality gate on every push: ruff + mypy close the backend gap react-doctor
cannot cover; ESLint + tsc cover both frontends. codegraph affected scoping
is a PR-speed optimisation only — main always runs the full suite.

## Paths
- Create: `.github/workflows/quality.yml`
- Reference: `backend/pyproject.toml` (ruff/mypy strict from TD-03)

## Steps
1. `.github/workflows/quality.yml` triggered on `push` and `pull_request`
2. Backend job: setup-python + astral-sh/setup-uv, `uv sync --frozen`, then `uv run ruff check`, `uv run ruff format --check`, `uv run mypy app`
3. Backend unit tests job: Postgres 16 **service container** with DATABASE_URL pointing at it; `uv run pytest`
4. Frontend + admin jobs: `npm ci`, `npm run lint`, `npx tsc --noEmit`, and unit tests (Vitest runners introduced in TD-04/TD-05)
5. PR scoping: run `codegraph init` in CI (index NOT committed — `.codegraph/` stays gitignored), then `git diff --name-only origin/main...HEAD | codegraph affected --stdin --quiet` to get affected test files and feed them to the runners
6. Branch rule: scoped selection on PRs only; when `ref == 'main'` always run the FULL suite
7. Prove it: PR touching one backend file runs scoped; merge; main runs full

## Tests
- A deliberate violation on a throwaway branch fails each of the four lint/typecheck checks
- PR run executes only affected tests; main run executes the full suite
- Backend tests connect to the Postgres service container

## Acceptance Criteria
- [ ] ruff check, ruff format --check, mypy app, npm lint, tsc --noEmit run on push+PR
- [ ] Violations fail the build; green on the P0 scaffold
- [ ] PRs run codegraph-scoped tests; main runs the full suite
- [ ] Backend tests run against a Postgres service container; codegraph index built in CI, never committed

## Verify
`gh run list --workflow=quality.yml --limit 3`

## Commit
`ci: quality workflow — ruff/mypy/eslint/tsc + scoped unit tests`

## Invariants
- Full suite on main, always — import-graph reachability is not behavioural coverage
- mypy stays strict (free on the empty scaffold; never loosen without cause)
- `.codegraph/` never committed; CI indexes fresh each run
