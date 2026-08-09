# GATE-P0: Phase 0 Exit Checklist

**Source:** development-plan-P0.md → Exit Checklist (verbatim)
**Rule:** Every box checked with verification evidence before any P1 card starts. Evidence is recorded in `development_plan/handoff/HANDOFF-SESSION-N.md`.

## Exit Checklist

- [ ] Domain active on Cloudflare; Resend verified with SPF/DKIM/DMARC
  - Verify: `dig +short NS siddhesh-chaudhari.com` (TD-M1) · `dig +short TXT siddhesh-chaudhari.com && dig +short TXT _dmarc.siddhesh-chaudhari.com` (TD-M3)
- [ ] R2 bucket with custom domain; MinIO running locally
  - Verify: `dig +short media.siddhesh-chaudhari.com` (TD-M2) · `docker compose ps` shows minio healthy (TD-06)
- [ ] Railway: backend, frontend, cron, tunnel, Postgres — all healthy
  - Verify: `railway status` + per-service deploy logs green (TD-M4, TD-M6)
- [ ] `GET /health` returns 200 from the deployed backend
  - Verify: `curl -s -o /dev/null -w '%{http_code}' https://<backend-public>/health` → 200 (TD-M4)
- [ ] `curl` on the deployed frontend returns content-bearing HTML
  - Verify: `bash scripts/check_ssr.sh https://<frontend-public>` (TD-04, TD-M4)
- [ ] Repo public; push protection and secret scanning on; no secrets in history
  - Verify: `gh api repos/SIDDHESHCHAUDHARI2K24/portfolio-sid/secret-scanning` + `gh api repos/SIDDHESHCHAUDHARI2K24/portfolio-sid/push-protection` + `git grep -i "sk-"` clean across history (TD-00)
- [ ] `alembic upgrade head` succeeds; `alembic heads` returns one head
  - Verify: `cd backend && uv run alembic upgrade head && uv run alembic heads` (TD-07)
- [ ] All four agents configured with CodeGraph, superpowers, react-doctor
  - Verify: `codegraph status` + skill discovery in opencode/Claude Code/Codex CLI/cursor-agent (TD-01, TD-14)
- [ ] `.mcp.json` committed with env var expansion, no key
  - Verify: `git log -p .mcp.json` shows only `${STITCH_API_KEY}` (TD-10)
- [ ] `docs/` complete, including `conventions.md` with every invariant
  - Verify: `ls docs/` + grep of each invariant from the TD-02 checklist
- [ ] `DESIGN.md` tokens live in both Tailwind configs; no hardcoded colours
  - Verify: `git grep -nE "#[0-9a-fA-F]{6}" -- frontend/app admin/src` → token definition files only (TD-11)
- [ ] Full CI pipeline green on `main`
  - Verify: `gh run list --branch main --limit 5` all green (TD-12, TD-13, TD-14)
- [ ] Deploy workflow pauses for approval and completes on approval
  - Verify: observed approve→deploy run in `gh run list --workflow=deploy.yml` (TD-15)

## Sign-off
All boxes checked with evidence in the session handoff → proceed to Wave 5 (TD-16).
