# TD-M5: Railway Auto-Deploy OFF + RAILWAY_TOKEN Env Secret

**Phase:** P0 · **Wave:** 4 · **Executor:** user (agent verifies after) · **Effort:** XS (30 min)
**Source:** development-plan-P0.md → P0.T2.S7
**Depends on:** TD-M4 · **Blocks:** TD-15

## Purpose
Deploys must flow exclusively through the approved GitHub Actions workflow.
Leaving Railway's GitHub triggers on produces two racing deploys per merge
and defeats the manual approval gate entirely.

## Paths
- Modify: Railway service settings (all services), GitHub repo settings (environment secret)

## Steps (user)
1. For EACH Railway service (backend, frontend, cron): disconnect the GitHub repo / disable automatic deploys in service settings
2. Generate a Railway project token (RAILWAY_TOKEN) for CLI/CI-driven deploys
3. Store RAILWAY_TOKEN as a GitHub **ENVIRONMENT** secret scoped to `production` — NOT a repository secret, which every workflow (including PR builds) can read
4. The local railway CLI stays logged in with your user session; no change needed locally

## Steps (agent, after user confirms)
5. Push a no-op commit to main; confirm Railway triggers no deploy (deployment list unchanged)
6. `railway up --service backend` from the local machine succeeds
7. Verify secret placement via gh api (see Verify)

## Tests
- Push to main alone triggers no Railway deploy
- `railway up --service backend` succeeds locally
- RAILWAY_TOKEN present at environment scope, absent at repository scope

## Acceptance Criteria
- [ ] Pushing to main does not trigger a Railway deploy on its own
- [ ] `railway up --service backend` succeeds locally with the token/session
- [ ] RAILWAY_TOKEN is a production environment secret, not a repo secret

## Verify (agent runs after user completes steps)
`gh api repos/SIDDHESHCHAUDHARI2K24/portfolio-sid/environments/production/secrets --jq '.secrets[].name' && gh api repos/SIDDHESHCHAUDHARI2K24/portfolio-sid/actions/secrets --jq '.secrets[].name' && railway up --service backend --detach`

## Commit
`chore(infra): railway auto-deploy off; token scoped to production env`

## Invariants
- The GitHub Actions deploy workflow (TD-15) is the only deploy path
- RAILWAY_TOKEN never exists as a repository secret
- Any future service inherits the rule: no GitHub triggers, workflow-only deploys
