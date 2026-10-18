# E04-W3: Gate Railway deploys on green CI

**Epic:** E04 CI/CD hardening · **Ticket:** E04-W3 · **Depends on:** W1 and W6 merged (the gate should wait on the final set of checks)

## Purpose

Railway deploys every push to `main` immediately (`checkSuites: false`). A commit that fails CI still reaches production.

## Goal

Railway waits for the commit's GitHub check suites and deploys only when they pass.

## Reference files

- `.railway/railway.ts` (the `portfolioSid` source and the inline `github(...)` sources for `frontend` and `admin`)
- `docs/DEPLOYMENT.md`

## Functionality

- Set `checkSuites: true` on all three `github(...)` calls (backend and cron share `portfolioSid`; frontend and admin have their own).
- Apply with `railway config apply` (production action; needs user approval at that moment).
- Document in `docs/DEPLOYMENT.md`: a red CI means no deploy; to ship anyway, fix forward or use the manual `deploy.yml`.

## Edge cases

- Railway waits on every check suite on the commit, including E2E (several minutes) and `react-doctor` if it runs on push. Deploys start later; W6 decides whether react-doctor runs on push.
- A cancelled run would leave a commit undeployed, and with W4's watch paths a later docs-only push would not redeploy it. CI and E2E therefore never cancel runs on `main` (`cancel-in-progress` is false for `refs/heads/main`; review finding, 2026-10-18).
- `pgbouncer` and `Postgres` are image sources and are unaffected.
- The manual `deploy.yml` uses `railway up` and bypasses the gate by design (emergency path).

## Testing

- `railway config plan` (or the IaC diff) shows only the three `checkSuites` changes.
- After apply, the next push shows "Waiting for CI" on each service in Railway, then deploys when CI is green.

## Acceptance criteria

- [x] `railway.ts` has `checkSuites: true` on every GitHub source; the plan shows no other change.
- [ ] Applied with user approval; Railway shows the services waiting for checks on the next push.
- [x] `docs/DEPLOYMENT.md` documents the gate and the manual bypass.

## Rollback

Set `checkSuites: false` and re-apply (user-approved).
