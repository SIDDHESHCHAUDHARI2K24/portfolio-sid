# TD-15: Deploy Workflow + Production Environment Approval

**Phase:** P0 · **Wave:** 4 · **Executor:** agent · **Effort:** M (4 hrs)
**Source:** development-plan-P0.md → P0.T6.S7
**Depends on:** TD-M5, TD-14 · **Blocks:** every production deploy

## Purpose
Deploys happen exclusively through GitHub Actions after all checks pass,
paused behind a manual approval gate. Railway auto-deploy is already off
(TD-M5) or this gate would be meaningless. Environment protection rules are
free on public repositories.

## Paths
- Create: `.github/workflows/deploy.yml`
- Modify: GitHub repo settings — `production` environment (reviewer, branch rule, secret)

## Steps
1. Create the `production` environment: yourself as required reviewer; deployment branch rule limiting it to `main`
2. Confirm `RAILWAY_TOKEN` is an ENVIRONMENT secret on `production` (placed in TD-M5) — reachable only after approval
3. `deploy.yml`: runs on `push` to `main` after quality + contracts + e2e pass; the deploy job declares `environment: production` so it pauses and waits
4. Deploy each service explicitly: `railway up --service backend`, `railway up --service frontend`, `railway up --service cron` (railwayapp/cli action, token from the environment secret)
5. Leave "prevent self-review" OFF — you are the only maintainer and enabling it would deadlock you. Note: pending approvals expire after 30 days
6. Use plain `pull_request` triggers wherever PR triggers are needed — NEVER `pull_request_target` with a checkout of PR code: on a public repo that is the standard remote-code-execution path where a fork's PR runs with your secrets
7. Test: merge to main → deploy job pauses → approve → all three services deploy; reject once → nothing deploys

## Tests
- Merge to main pauses the deploy job pending approval
- Approve → all three services deploy; reject → none deploy
- Non-production workflow runs cannot read RAILWAY_TOKEN

## Acceptance Criteria
- [ ] Merging to main pauses the deploy job pending approval
- [ ] Approving deploys backend + frontend + cron; rejecting deploys none
- [ ] RAILWAY_TOKEN is an environment secret, unreadable by non-production jobs
- [ ] No workflow uses pull_request_target; branch rule limits environment to main; prevent-self-review off

## Verify
`gh run list --workflow=deploy.yml --limit 3 && gh api repos/SIDDHESHCHAUDHARI2K24/portfolio-sid/environments/production`

## Commit
`ci: deploy workflow — manual approval gate, per-service railway up`

## Invariants
- `pull_request_target` with PR-code checkout is forever prohibited
- RAILWAY_TOKEN lives only as a production environment secret — never a repo secret
- Railway auto-deploy stays disconnected; this workflow is the only deploy path
