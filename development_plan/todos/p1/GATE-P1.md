# GATE-P1: Phase 1 Exit Gate

**Phase:** P1 · **Wave:** 6 (end) · **Executor:** paired · **Effort:** S (verification only)
**Source:** development-plan-P1.md → Exit Checklist (verbatim)
**Depends on:** TD-16, TD-17, TD-18, TD-19, TD-20, TD-21, TD-22, TD-23 · **Blocks:** Wave 7 (TD-24..TD-30)

## Purpose
No Phase 2 work starts until every box below is checked with evidence.
Phase 1 proves every pattern nine features will replicate — a skipped check
here is a defect multiplied by nine.

## Exit Checklist
- [ ] Admin login requires password + OTP; brute force locks out persistently
- [ ] Timeline CRUD works end-to-end; edits appear publicly within seconds
- [ ] Drafts invisible publicly; scheduled entries publish via cron
- [ ] Category switching re-highlights instantly with no navigation
- [ ] `curl` on `/timeline` and `/` returns full content in HTML
- [ ] `next build` reports content routes as static
- [ ] Timeline tile renders on overview and disappears when empty
- [ ] Tile contract documented in `conventions.md` with a worked example
- [ ] Shared admin field components extracted and reusable
- [ ] Relevance parity fixture passes on both implementations
- [ ] `alembic heads` returns one head; CI green

## Checklist → Card Map
- Login/OTP/lockout → TD-17, TD-23 · CRUD + seconds-to-public → TD-20, TD-23, TD-19
- Drafts/scheduled → TD-16, TD-19 · Category switching → TD-21, TD-22
- `curl` HTML + static routes → TD-21, TD-22 · Tile + contract → TD-22
- Shared field components → TD-23 · Parity fixture → TD-18, TD-21 · Alembic/CI → TD-16, TD-20

## Verification Commands
- `uv run pytest backend -q` — full backend suite against the docker Postgres service (leak tests, six relevance cases, query-count assertion, auth/lockout)
- `uv run alembic heads` — exactly one head; `uv run alembic upgrade head && uv run alembic downgrade -1 && uv run alembic upgrade head`
- `npm run build` in `frontend/` — `/`, `/timeline` reported static (not dynamic); `grep -rn "cookies()" frontend/src/app` → no content-route hits
- `curl -s localhost:3000/timeline` and `curl -s localhost:3000/` — full content present in server HTML (all entries; default intro copy)
- Parity fixture: backend `uv run pytest -q -k parity` and frontend `npm test -- relevance` both green on the shared fixture
- `npm run build && npm run test` in `admin/` — shared field components present in `admin/src/components/fields/`
- CI: ruff, mypy, ESLint, tsc, OpenAPI drift, Alembic single-head, SSR curl check all green on the gate commit
- Manual: 10 failed logins → lockout persists after backend restart; admin edit visible publicly within seconds; HUD switch re-highlights with no navigation; tile absent when timeline emptied

## On Failure
Any unchecked box → return to the owning card, fix, re-verify with evidence,
then re-run this gate. No partial passes carry into Wave 7.

## Commit
`docs: GATE-P1 exit checklist verified` (only when all boxes are checked)
