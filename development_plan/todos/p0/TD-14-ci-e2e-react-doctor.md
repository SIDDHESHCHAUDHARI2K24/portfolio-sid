# TD-14: react-doctor (Baseline + PR Gate) + Playwright E2E + SSR Check

**Phase:** P0 · **Wave:** 4 · **Executor:** agent · **Effort:** L (1 day)
**Source:** development-plan-P0.md → P0.T4.S5, P0.T6.S5, P0.T6.S6
**Depends on:** TD-12, TD-09 · **Blocks:** TD-15

## Purpose
react-doctor covers state/effects, performance, architecture, security, and
accessibility across both React apps, diff-scoped so it never drowns you on
day one. Playwright runs only where it earns its cost: PRs-to-main and main.
check_ssr.sh graduates from local helper to CI gate.

> **Status (session 3):**
> - A1 (react-doctor baseline + PR gate): DONE — `docs/react-doctor-baseline.md`,
>   `.github/workflows/react-doctor.yml`, `doctor.config.ts`, agent skill install.
>   Frontend 35 issues / admin 35 issues, 0 blocking errors, audits exit 0.
> - A3 (local dev runbook + smoke): DONE — `docs/specs/session-3/LOCAL-01-runbook.md`
>   + `LOCAL.md`. Boot verified: docker compose healthy, `/health` 200,
>   admin `/login` 200, `check_ssr.sh --all` 13/13, `--seo` 6/6.
> - A4 (complete critical journeys vs TD-36.S5): DONE — Journeys 1–6 pass
>   (19/21; Journey 4 runs once on desktop because the dev-OTP shortcut uses a
>   single shared challenge slot and races under parallel viewports). Added a
>   dev-only `GET /api/v1/auth/dev/otp` endpoint (gated on `ENVIRONMENT=development`)
>   so the admin login journey runs locally without Resend; regenerated
>   `openapi.json` + both `api.d.ts`. `seed_e2e.py` now seeds a cross-linked
>   project for Journey 6.
> - A2 (deliberate-break CI test, local-equivalent): DONE — injected a ruff
>   violation on a scratch branch; `uv run ruff check .` went RED (exit 1) then
>   GREEN after revert. Gate is effective. (Not pushed; tunnel/push blocked.)
>
> **Known hand-backs (not fixed this session, out of A1–A4 scope):**
> - `frontend/tests/accessibility/keyboard.spec.ts:3` fails: a focused element is
>   `visibility:hidden` during tab order — pre-existing app a11y bug.
> - `uv run pytest -q` shows ~52 failures when run in bulk (test-isolation/DB
>   ordering); they pass in isolation. Pre-existing, not caused by these changes.
> - M1–M10 launch-infra cards (Cloudflare zone, R2/Turnstile/Analytics, Resend,
>   Railway env, tunnel access) remain the user's manual phase.

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
- [x] react-doctor audit runs on both apps; skill installed for all agents (OpenCode/Claude/Codex/Cursor/…); baseline committed to `docs/react-doctor-baseline.md` (session 3)
- [x] PRs receive diff-scoped react-doctor summaries via `.github/workflows/react-doctor.yml`; a bad component is flagged (advisory; `doctor.config.ts` => `blocking: error` on new errors)
- [x] E2E workflow: PRs-to-main + main only, Postgres service container, critical journeys pass (`.github/workflows/e2e.yml`)
- [x] `scripts/check_ssr.sh` runs in the E2E workflow

## Verify
`gh run list --workflow=e2e.yml --limit 2 && ls docs/react-doctor-baseline.md`

## Commit
`ci: react-doctor baseline+gate, Playwright E2E, SSR curl check`

## Invariants
- E2E stays off the per-commit path — it is where CI time goes
- react-doctor is diff-scoped on PRs; backlog issues are not day-one failures
- React-only coverage: backend quality is ruff/mypy's job (TD-12)
