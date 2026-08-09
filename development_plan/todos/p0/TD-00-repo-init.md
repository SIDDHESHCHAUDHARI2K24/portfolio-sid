# TD-00: Repo Init + Git Hygiene + Secrets Guardrails

**Phase:** P0 · **Wave:** 0 · **Executor:** agent · **Effort:** S (1 hr)
**Source:** development-plan-P0.md → P0.T3.S1
**Depends on:** — · **Blocks:** everything

## Purpose
Public repo demands hygiene from commit one. Establish git, ignore rules, and
secret guardrails before any code exists. The repo already exists on GitHub
with one commit; local init must land on top of it.

## Paths
- Create: `.gitignore`, `.gitattributes`
- Modify: repo settings (secret scanning, push protection) via `gh api`
- Gitignore targets: `.env`, `.env.*`, `opencode.json`, `.codegraph/`, `__pycache__/`, `node_modules/`, `.next/`, `dist/`, `*.db`, `*.sql`, `.DS_Store`, `graphify-out/cost.json`

## Steps
1. `git init -b main`; `git remote add origin https://github.com/SIDDHESHCHAUDHARI2K24/portfolio-sid.git`; `git fetch origin`
2. Inspect `origin/main` commit; `git reset origin/main` (mixed) so local work sits on the existing history
3. Write `.gitignore` (targets above) and `.gitattributes` (`* text=auto eol=lf`)
4. `opencode.json` contains a literal provider API key → gitignored, never committed; note rotation recommendation in handoff
5. Commit hygiene files
6. Verify secret scanning + push protection enabled (`gh api repos/{owner}/{repo}/secret-scanning` and `.../push-protection`); enable if not
7. Push protection test: attempt committing a fake key on a throwaway branch; expect rejection; delete branch

## Tests
- `git check-ignore -v opencode.json .env` → both ignored
- Fake-secret push blocked by push protection
- `git log --oneline` shows continuity with remote's first commit

## Acceptance Criteria
- [ ] Local main tracks origin/main with hygiene files committed
- [ ] Secret scanning + push protection verified on
- [ ] Fake-key commit blocked
- [ ] No secret in any committed file (`git grep -i "sk-"` clean)

## Verify
`git status && git log --oneline && git check-ignore -v opencode.json`

## Commit
`chore: repo hygiene — gitignore, gitattributes, secret guardrails`

## Invariants
- Secrets live only in Railway env vars / GitHub environment secrets / local gitignored `.env`
- No content, fixtures, or DB dumps ever enter git ("work views" blogs are private)
- `pull_request_target` with PR-code checkout is forever prohibited (TD-15)
