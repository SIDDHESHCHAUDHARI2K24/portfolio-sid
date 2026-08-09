# TD-14: react-doctor (Baseline + PR Gate) + Playwright E2E + SSR Check

**Phase:** P0 · **Wave:** 4 · **Executor:** agent · **Effort:** L (1 day)
**Source:** development-plan-P0.md → P0.T4.S5, P0.T6.S5, P0.T6.S6
**Depends on:** TD-12, TD-09 · **Blocks:** TD-15

## Purpose
react-doctor covers state/effects, performance, architecture, security, and
accessibility across both React apps, diff-scoped so it never drowns you on
day one. Playwright runs only where it earns its cost: PRs-to-main and main.
check_ssr.sh graduates from local helper to CI gate.

## Paths
- Create: `doctor.config.ts`, `docs/react-doctor-baseline.md`, `.github/workflows/e2e.yml`, `e2e/` placeholder spec, react-doctor CI workflow
- Reference: `scripts/check_ssr.sh` (TD-04)

## Steps
1. `npx react-doctor@latest` audit against `frontend/` and `admin/`, with `--no-telemetry` (opt out of default Sentry telemetry)
2. `npx react-doctor@latest install` — wires the skill into all four agents; configure rules in `doctor.config.ts`
3. Commit the baseline report to `docs/react-doctor-baseline.md` — the clean starting point for diff-scoped mode
4. `npx react-doctor@latest ci install` — scaffolds the PR workflow + summary comments; tune gate severity and scan scope with `react-doctor ci config`
5. `.github/workflows/e2e.yml`: triggers `pull_request` (to main) and `push` (main) ONLY; Postgres 16 service container; build the backend image (TD-09) and frontend standalone output; start both
6. Placeholder Playwright journey: `/api/v1/health` returns 200; frontend `/` renders placeholder content server-side
7. Wire `bash scripts/check_ssr.sh` into the E2E workflow against the running frontend
8. Negative test: a component using array index as key on a throwaway branch → react-doctor's PR comment flags it

## Tests
- PRs receive a react-doctor summary comment; the deliberately bad component is flagged
- E2E workflow triggers only on PRs-to-main and pushes to main
- check_ssr.sh fails the workflow when SSR HTML lacks content (simulated)

## Acceptance Criteria
- [ ] react-doctor audit runs on both apps; skill installed for all four agents; baseline committed to docs/
- [ ] PRs receive diff-scoped react-doctor summaries; a bad component is flagged
- [ ] E2E workflow: PRs-to-main + main only, Postgres service container, placeholder journey passes
- [ ] `scripts/check_ssr.sh` runs in the E2E workflow

## Verify
`gh run list --workflow=e2e.yml --limit 2 && ls docs/react-doctor-baseline.md`

## Commit
`ci: react-doctor baseline+gate, Playwright E2E, SSR curl check`

## Invariants
- E2E stays off the per-commit path — it is where CI time goes
- react-doctor is diff-scoped on PRs; backlog issues are not day-one failures
- React-only coverage: backend quality is ruff/mypy's job (TD-12)
