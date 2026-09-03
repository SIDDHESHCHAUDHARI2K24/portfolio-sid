# portfolio-sid-v2 Deployment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stand up a fresh, clean Railway deployment (`portfolio-sid-v2`) of the portfolio stack — Next.js public site, Vite admin SPA, FastAPI backend, cron scheduler, dedicated PgBouncer, Railway Postgres — with every Postgres connection flowing through PgBouncer, only admin+frontend publicly exposed, and the old project (already deleted) fully replaced.

**Architecture:** Six Railway services in one project/environment. frontend (public, Railpack, `next start`) rewrites `/api`,`/media` to the private backend; admin (public, nginx SPA) proxies `/api`,`/media`,`/health` to `backend.railway.internal:8080` with a dynamic resolver; backend (private, Dockerfile at repo root, volume `/data`, alembic at start) and cron (private, same image, `*/5` scheduler) connect only via `pgbouncer.railway.internal:6432` (scram-sha-256, transaction mode, 100/20/5 pools) to the Postgres plugin. Storage is the Railway volume — no R2 anywhere.

**Tech Stack:** Railway CLI v5 (explicit flags, never interactive prompts), edoburu/pgbouncer:1.22.1-p0, Python 3.12 / FastAPI / asyncpg / SQLAlchemy, Next.js (next start), nginx, Cloudflare DNS, GitHub Actions (CI fallback), gh CLI.

## Global Constraints

- Never commit secrets; secret values live only in Railway env, gh `production` environment secrets, and local gitignored `backend/.env`. Never echo secret values in chat/logs/output.
- Deploys build from `main` HEAD only (≥ `cb98d15`; intermediate commits `2bd928f..7527153` have a broken alembic chain).
- Never connect the Postgres plugin to the GitHub repo.
- pgbouncer image tag is exactly `edoburu/pgbouncer:1.22.1-p0`; `AUTH_TYPE=scram-sha-256`; `POOL_MODE=transaction`.
- Frontend start command is `npm run start` (NOT standalone).
- Backend listens on Railway `PORT` (8080); admin/frontend proxy targets `:8080`.
- Backend must have NO public domain, ever. `CORS_ALLOW_ORIGINS` empty. `NEXT_PUBLIC_INDEXABLE=false`.
- Only admin + frontend have public domains.
- Every Railway command uses explicit `--project/--service/--environment` flags (CLI link state is global — sub-agents must never rely on linked-project state).
- Record PASS/FAIL per gate; never advance a phase on FAIL. `systematic-debugging` per failing service; ≤3 retries then escalate to user.
- All Postgres traffic via pgbouncer:6432 — nothing else connects to `postgres.railway.internal:5432`.
- Design doc: `docs/specs/portfolio-sid-v2-deployment/DESIGN.md` (decisions log D1–D10).

---

## Execution model (sub-agent dispatch)

Phases are strictly sequential — each depends on the previous phase's infrastructure. Sub-agents parallelize *verification* within a phase, never Railway mutations:

| Phase | Sequential executor | Parallel sub-agent work |
|---|---|---|
| P0 | main agent | none (user checkpoint) |
| P1 | main agent | verify service list + IDs (1 verifier) |
| P2 | main agent | pgbouncer gate check (log grep) |
| P3 | main agent | backend gate check; no-public-domain check; admin 200 check (3 verifiers) |
| P4 | main agent | scheduler log gate check (1 verifier) |
| P5 | main agent (after user re-auth) | 4× deploy SUCCESS + build meta verification |
| P6 | code sub-agent (rewrite deploy.yml) + review sub-agent | CI dispatch gate verification |
| P7 | verifier sub-agents (read-only) | admin gates, frontend check_ssr 13/13, kill-test |
| P8 | main agent (ssh seed) | API counts + PDF 200 verification |
| P9 | main agent (domains) + docs sub-agent | dig/curl/SSL verification |
| P10 | verifier sub-agents | full DoD re-run + restore drill |

Every sub-agent instruction includes: exact commands, expected output, and the PASS/FAIL criterion.

---

### Task 0: Pre-flight code commits (before any Railway mutation)

**Files:**
- Commit existing working tree: `backend/app/core/database.py`, `backend/app/tests/test_pgbouncer_config.py`, `docker-compose.yml`
- Modify: `frontend/lib/api.ts:12,24` (env-ize PUBLIC_PROXY)
- Modify: `.gitignore` (add `backend/.storage/`)

- [ ] **Step 1: Commit the asyncpg statement-cache hardening**

```bash
git status --short                      # confirm only the 3 expected modified files
cd backend && uv run pytest app/tests/test_pgbouncer_config.py -q && cd ..
# expected: PASS (asserts both statement_cache_size and prepared_statement_cache_size == 0)
git add backend/app/core/database.py backend/app/tests/test_pgbouncer_config.py docker-compose.yml
git commit -m "fix(backend): disable asyncpg statement cache for pgbouncer"
```

- [ ] **Step 2: Env-ize the frontend build proxy**

Edit `frontend/lib/api.ts`:

```ts
// BEFORE (line 12)
const PUBLIC_PROXY = "https://admin-production-9cc7.up.railway.app";
// AFTER
const PUBLIC_PROXY = process.env.PUBLIC_API_PROXY ?? "";
```

And in `getFallbackServerBase` (line ~24) guard the empty case:

```ts
// BEFORE
  const publicFallback = `${PUBLIC_PROXY}/api/v1`;
  if (publicFallback !== primary) return publicFallback;
// AFTER
  if (PUBLIC_PROXY) {
    const publicFallback = `${PUBLIC_PROXY}/api/v1`;
    if (publicFallback !== primary) return publicFallback;
  }
```

- [ ] **Step 3: Verify frontend change**

```bash
cd frontend && npm run lint && npx tsc --noEmit && npm test
# expected: lint clean, tsc clean, vitest suite PASS (relevance + tileArrangement tests unaffected)
cd .. && git add frontend/lib/api.ts && git commit -m "fix(frontend): make build-time api proxy configurable"
```

- [ ] **Step 4: Ignore local storage + commit docs**

```bash
printf '\n# local disk storage (dev runs with STORAGE_KIND=local)\nbackend/.storage/\n' >> .gitignore
git add .gitignore docs/handoff/HANDOFF-2026-08-31-CLEAN-REBUILD.md docs/specs/portfolio-sid-v2-deployment/
git commit -m "chore: ignore local storage dir; docs(handoff): clean rebuild plan"
git log --oneline -4   # expected: the 3 new commits on top of 595b57e
```

**Gate P0:** working tree clean; 3 commits present; `git log` HEAD chain intact on `main`.

---

### Task 1 (Phase 1): Project skeleton + secrets prep

**User action 1:** If Railway asks for a plan during project creation, pick the paid (Hobby/Pro) plan — the volume, Postgres plugin, and cron service require it.

- [ ] **Step 1: Verify CLI identity + flag shapes**

```bash
railway whoami                        # expected: Siddhesh Chaudhari
railway init --help                   # note exact --name flag
railway add --help                    # note exact flags for service creation
```

- [ ] **Step 2: Create the project**

```bash
railway init -n portfolio-sid-v2
railway project list --json | python3 -c "import json,sys; d=json.load(sys.stdin); print([p for p in d if p['name']=='portfolio-sid-v2'])"
# expected: portfolio-sid-v2 present; record its id + production environment id
```

- [ ] **Step 3: Add the Postgres plugin and 5 services**

```bash
railway add -d postgres -s Postgres
railway add -s backend
railway add -s cron
railway add -s frontend
railway add -s admin
railway add --image edoburu/pgbouncer:1.22.1-p0 --service pgbouncer
# (verify exact flags from Step 1 output; every command needs -e production if prompted)
```

- [ ] **Step 4: Attach the backend volume**

Dashboard: backend → Settings → Volumes → add `backend-volume` mounted at `/data`. (No CLI flag in v5 — dashboard is the sanctioned path.)

- [ ] **Step 5: Record IDs**

```bash
railway service list --json   # save service ids + environment id to local notes (NOT git)
```

**Gate P1:** `railway service list` shows exactly 6 services (frontend, admin, backend, cron, pgbouncer, Postgres); backend has volume `/data`; `railway variables -s Postgres` returns a `DATABASE_URL` (new plugin password — never reused elsewhere).

---

### Task 2 (Phase 2): Data layer — pgbouncer

- [ ] **Step 1: Harvest the new Postgres URL locally**

```bash
NEW_DB_URL=$(railway variables -s Postgres --json | python3 -c "import json,sys; print([v for v in json.load(sys.stdin) if v['name']=='DATABASE_URL'][0]['value'])")
# keep in shell/local notes only
```

- [ ] **Step 2: Set pgbouncer env** (substitute the real `$NEW_DB_URL`)

```bash
railway variables -s pgbouncer \
  DATABASE_URL="$NEW_DB_URL" \
  POOL_MODE=transaction \
  AUTH_TYPE=scram-sha-256 \
  MAX_CLIENT_CONN=100 \
  DEFAULT_POOL_SIZE=20 \
  RESERVE_POOL_SIZE=5 \
  LISTEN_ADDR='*' \
  LISTEN_PORT=6432 \
  ADMIN_USERS=postgres \
  IGNORE_STARTUP_PARAMETERS=extra_float_digits
```

- [ ] **Step 3: Deploy + gate check**

```bash
railway logs --service pgbouncer   # after variable-triggered redeploy
# expected lines: "listening on 0.0.0.0:6432" and "PgBouncer 1.22.1" / "process up"
```

**Gate P2:** both log lines present; zero auth errors.

---

### Task 3 (Phase 3): Backend + admin pre-deploy

- [ ] **Step 1: Generate fresh secrets locally** (values kept in shell/local notes, never echoed in chat)

```bash
SESSION_SECRET=$(openssl rand -hex 32)
REVALIDATION_SECRET=$(openssl rand -hex 32)
ADMIN_PASSWORD=$(openssl rand -base64 18)   # NEW random password — display to user ONCE (user action 2)
ADMIN_PASSWORD_HASH=$(cd backend && uv run python -m app.cli hash-password "$ADMIN_PASSWORD" && cd ..)
```

- [ ] **Step 2: Read reused secrets from local .env** (per user instruction — never print)

```bash
ADMIN_EMAIL=$(grep -E '^ADMIN_EMAIL=' backend/.env | cut -d= -f2-)
RESEND_API_KEY=$(grep -E '^RESEND_API_KEY=' backend/.env | cut -d= -f2-)
RAILWAY_TOKEN=$(grep -E '^RAILWAY_TOKEN=' backend/.env | cut -d= -f2-)   # kept for P6
```

- [ ] **Step 3: Set backend env**

```bash
railway variables -s backend \
  ENVIRONMENT=production \
  DATABASE_URL="postgresql+asyncpg://postgres:<NEW_DB_PW>@pgbouncer.railway.internal:6432/railway" \
  PGBOUNCER_ENABLED=true \
  DATABASE_POOL_SIZE=10 \
  DATABASE_MAX_OVERFLOW=5 \
  STORAGE_KIND=local \
  LOCAL_STORAGE_DIR=/data \
  MEDIA_BASE_URL=https://admin.siddhesh-chaudhari.com \
  SESSION_SECRET="$SESSION_SECRET" \
  ADMIN_PASSWORD_HASH="$ADMIN_PASSWORD_HASH" \
  ADMIN_EMAIL="$ADMIN_EMAIL" \
  RESEND_API_KEY="$RESEND_API_KEY" \
  RESEND_FROM=onboarding@resend.dev \
  REVALIDATION_SECRET="$REVALIDATION_SECRET" \
  CF_ACCESS_ENABLED=false \
  NEXT_PUBLIC_BASE_URL=https://siddhesh-chaudhari.com
# CORS_ALLOW_ORIGINS omitted deliberately: config.py default is [] (invariant #14) and an
# explicit empty value trips up the CLI variable parser
# <NEW_DB_PW> = password portion of the Postgres plugin DATABASE_URL from P2 Step 1
```

- [ ] **Step 4: Deploy backend from repo root**

```bash
railway up --service backend --detach
```

- [ ] **Step 5: Deploy admin (pre-deploy so PUBLIC_API_PROXY is live before frontend's first build)**

```bash
cd admin && railway up --service admin --detach && cd ..
```

- [ ] **Step 6: Backend gates (verifier sub-agent A)**

```bash
railway logs --service backend | tail -40
# expected: alembic single head migration success, then "Uvicorn running on http://0.0.0.0:8080"
# FORBIDDEN: DuplicatePreparedStatementError, KeyError in alembic, connection refused to postgres:5432 (must be :6432)
```

- [ ] **Step 7: Privacy gate (verifier sub-agent B)**

```bash
railway domain --service backend   # expected: NO domains
railway variables -s backend --json | python3 -c "import json,sys; names={v['name'] for v in json.load(sys.stdin)}; print('PRIVATE_DOMAIN' if any('PRIVATE_DOMAIN' in n for n in names) else 'MISSING')"
```

- [ ] **Step 8: Admin gate (verifier sub-agent C)**

```bash
ADMIN_HOST=$(railway domain --service admin | awk '{print $1}')   # e.g. admin-production-XXXX.up.railway.app
curl -sI "https://$ADMIN_HOST/" | head -1      # expected: HTTP/2 200
```

**Gate P3:** all of: uvicorn on 8080, no prepared-statement/auth errors, no public domain on backend, admin generated host 200. **User action 2:** give the user the generated `$ADMIN_PASSWORD` (once).

---

### Task 4 (Phase 4): Cron

- [ ] **Step 1: Set cron env** (same core as backend)

```bash
railway variables -s cron \
  ENVIRONMENT=production \
  DATABASE_URL="postgresql+asyncpg://postgres:<NEW_DB_PW>@pgbouncer.railway.internal:6432/railway" \
  PGBOUNCER_ENABLED=true \
  REVALIDATION_SECRET="$REVALIDATION_SECRET" \
  STORAGE_KIND=local \
  LOCAL_STORAGE_DIR=/data \
  MEDIA_BASE_URL=https://admin.siddhesh-chaudhari.com \
  NEXT_PUBLIC_BASE_URL=https://siddhesh-chaudhari.com
```

- [ ] **Step 2: Set instance config** (cron schedule + start command via dashboard or GraphQL `serviceInstanceUpdate`; introspect `__type(name:"ServiceInstanceUpdateInput")` for exact field names)

```text
cronSchedule: "*/5 * * * *"
startCommand: "python -m app.jobs.scheduler"
```

- [ ] **Step 3: Deploy from repo root**

```bash
railway up --service cron --detach
```

- [ ] **Step 4: Gate (verifier sub-agent)**

```bash
sleep 330 && railway logs --service cron | tail -20
# expected within 5 min: "scheduler: promoted 0 row(s) across 8 model(s)" — no asyncpg errors
```

**Gate P4:** scheduler log line appears within 5 minutes with zero asyncpg errors.

---

### Task 5 (Phase 5): GitHub native triggers + first full push

**User action 3:** Re-authorize the Railway GitHub App on `SIDDHESHCHAUDHARI2K24/portfolio-sid` in the Railway dashboard (service → Source → Connect GitHub). Gate: `railway service source connect` succeeds.

- [ ] **Step 1: Connect sources (NEVER Postgres)**

```bash
railway service source connect --repo SIDDHESHCHAUDHARI2K24/portfolio-sid --branch main --service backend
railway service source connect --repo SIDDHESHCHAUDHARI2K24/portfolio-sid --branch main --service cron
railway service source connect --repo SIDDHESHCHAUDHARI2K24/portfolio-sid --branch main --service frontend
railway service source connect --repo SIDDHESHCHAUDHARI2K24/portfolio-sid --branch main --service admin
```

- [ ] **Step 2: Per-service build config**

```text
backend:  dockerfilePath="/Dockerfile", rootDirectory=null
cron:     dockerfilePath="/Dockerfile", rootDirectory=null (keep cronSchedule + startCommand from P4)
frontend: builder=RAILPACK, rootDirectory="/frontend", startCommand="npm run start"
admin:    dockerfilePath="admin/Dockerfile", rootDirectory="admin"
```

- [ ] **Step 3: Set frontend env + the new proxy var**

```bash
ADMIN_HOST=$(railway domain --service admin | awk '{print $1}')
railway variables -s frontend \
  BACKEND_URL=http://backend.railway.internal:8080 \
  NEXT_PUBLIC_INDEXABLE=false \
  REVALIDATION_SECRET="$REVALIDATION_SECRET" \
  NEXT_PUBLIC_BASE_URL=https://siddhesh-chaudhari.com \
  PUBLIC_API_PROXY="https://$ADMIN_HOST"
# NEXT_PUBLIC_API_BASE_URL stays unset (relative /api via rewrites; backend is private)
```

- [ ] **Step 4: Trigger push**

```bash
git commit --allow-empty -m "ci: trigger railway native deploys"
git push origin main
```

- [ ] **Step 5: Gates (verifier sub-agents, one per service)**

```bash
railway status   # 4 deployments SUCCESS from the push; metas show builder/dockerfilePath/rootDirectory as intended
railway logs --service frontend | tail -10   # "next start"-style startup
railway logs --service admin | tail -10      # nginx started
```

**Gate P5:** all 4 SUCCESS with correct build meta; Postgres shows NO deployment triggered by the push.

---

### Task 6 (Phase 6): CI fallback workflow (separate planned task)

**Scope:** rewrite `.github/workflows/deploy.yml` (current: dry-run stub, no admin job, no project targeting, no health gate) per handoff §6 design inputs. Own commit `ci(deploy):`.

- [ ] **Step 1: Draft the workflow** (code sub-agent)

Key elements (handoff §6): `workflow_dispatch` with `service` choice input (`all|backend|cron|frontend|admin`); `environment: production`; Railway CLI pinned via `npx @railway/cli@<pinned>`; `RAILWAY_PROJECT_ID` env = portfolio-sid-v2 id; per-service jobs with correct workdir (`backend`/`cron`: repo root; `frontend`: `frontend/`; `admin`: `admin/`) → `railway up --service <s> --detach`; post-deploy health gate: `railway status` + `curl -f https://<frontend-host>/api/v1/health`; `concurrency: ci-deploy`; `timeout-minutes: 30`; `permissions: contents: read`; `RAILWAY_SILENT=true`; never echo the token.

- [ ] **Step 2: Verify token scope** (before any gh secret write)

```bash
RAILWAY_TOKEN="$RAILWAY_TOKEN" railway project list --json
# expected: portfolio-sid-v2 listed. If not → token is scoped to the deleted project →
# user action 4: user creates a new project-scoped token in the Railway dashboard.
```

- [ ] **Step 3: Set the gh secret (no echo)**

```bash
grep -E '^RAILWAY_TOKEN=' backend/.env | cut -d= -f2- | gh secret set RAILWAY_TOKEN --env production
gh secret list --env production
```

- [ ] **Step 4: Dispatch test**

```bash
gh workflow run deploy.yml -f service=all
gh run watch && gh run view --log
# expected: all 4 deploy SUCCESS in portfolio-sid-v2; health step green; no token value in logs
```

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/deploy.yml && git commit -m "ci(deploy): manual dispatch fallback for portfolio-sid-v2"
```

**Gate P6:** manual dispatch deploys all 4; health gate green; `gh secret list --env production` shows RAILWAY_TOKEN; no secrets in workflow logs.

---

### Task 7 (Phase 7): Frontends + proxies (verifier sub-agents, read-only)

- [ ] **Step 1: Admin gates**

```bash
ADMIN_HOST=<admin host from P5>; FRONTEND_HOST=<frontend host from P5>
curl -sI "https://$ADMIN_HOST/" | head -1                    # 200
curl -sf "https://$ADMIN_HOST/api/v1/health" | head -c 200   # 200 + healthy payload
curl -s -o /dev/null -w "%{http_code}\n" "https://$ADMIN_HOST/media/<seeded-key>"  # P8; until then any /media path must not 502
```

- [ ] **Step 2: Frontend gates**

```bash
bash scripts/check_ssr.sh --all "https://$FRONTEND_HOST"   # expected 13/13 PASS
curl -sf "https://$FRONTEND_HOST/api/v1/health" | head -c 200   # 200 via rewrites
curl -s -o /dev/null -w "%{http_code}\n" "http://backend.railway.internal:8080/api/v1/health"  # from local = fail (private)
```

- [ ] **Step 3: Kill-test (dynamic resolver proof)**

```bash
railway service restart --service backend --yes
sleep 20 && curl -s -o /dev/null -w "%{http_code}\n" "https://$ADMIN_HOST/api/v1/health"
# expected: 200 WITHOUT any admin restart
```

**Gate P7:** all of the above PASS.

---

### Task 8 (Phase 8): Content seed (in-container)

- [ ] **Step 1: Verify ssh mechanics** (before the real run)

```bash
railway ssh --help                 # note command/pipe support
ls resumes/*.pdf | wc -l           # expected: 6
```

- [ ] **Step 2: Copy PDFs into the backend container**

```bash
tar czf - resumes | railway ssh --service backend -- bash -c 'mkdir -p /data/seed-pdfs && tar xzf - -C /data/seed-pdfs'
# fallback if stdin piping unsupported: base64 chunks via railway ssh heredoc; if ssh itself is
# unusable → escalate to systematic-debugging; last resort = admin-API resume rows + PDF upload
# path decided at execution time.
```

- [ ] **Step 3: Dry-run then real seed (inside the container — this is what writes /data)**

```bash
railway ssh --service backend -- bash -lc "uv run --project backend python backend/scripts/seed_resumes.py --dir /data/seed-pdfs --canon backend/scripts/resume_canon.json --dry-run"
railway ssh --service backend -- bash -lc "uv run --project backend python backend/scripts/seed_resumes.py --dir /data/seed-pdfs --canon backend/scripts/resume_canon.json"
```

- [ ] **Step 4: Gates (verifier sub-agent)**

```bash
curl -s https://$ADMIN_HOST/api/v1/resumes | python3 -c "import json,sys; print(len(json.load(sys.stdin)))"   # 6
curl -s https://$ADMIN_HOST/api/v1/timeline | python3 -c "import json,sys; print(len(json.load(sys.stdin)))"  # 14
curl -s https://$ADMIN_HOST/api/v1/overview | python3 -c "import json,sys; print(len(json.load(sys.stdin)))"  # 6
# one resume PDF: curl -sI https://$ADMIN_HOST/media/<file_key> → 200
```

**Gate P8:** 6 resumes / 14 timeline / 6 overview; at least one PDF download 200; pgbouncer logs show the traffic.

---

### Task 9 (Phase 9): Custom domains + docs

- [ ] **Step 1: Attach domains**

```bash
railway domain siddhesh-chaudhari.com --service frontend
railway domain admin.siddhesh-chaudhari.com --service admin
railway domain --service frontend   # prints the CNAME target to give Cloudflare
railway domain --service admin      # prints the CNAME target
```

- [ ] **Step 2: Cloudflare (user action 5)**

Update both CNAME records in Cloudflare DNS to the new Railway targets (proxy status as before). Then verify:

```bash
dig +short siddhesh-chaudhari.com
dig +short admin.siddhesh-chaudhari.com
curl -sI https://siddhesh-chaudhari.com | head -1                # 200, SSL green
curl -sI https://admin.siddhesh-chaudhari.com | head -1          # 200, SSL green
curl -sf https://admin.siddhesh-chaudhari.com/api/v1/health      # 200
bash scripts/check_ssr.sh --all https://siddhesh-chaudhari.com   # 13/13 on custom domain
```

- [ ] **Step 3: Docs updates (docs sub-agent)**

- `docs/conventions.md` §Connection pooling: replace the stale "no sidecar service is deployed" claim — dedicated `pgbouncer` service, image `1.22.1-p0`, scram/transaction, prepared-statement note.
- `docs/handoff/env-vars-registry.md`: add pgbouncer service section, `PGBOUNCER_ENABLED`, `NEXT_PUBLIC_BASE_URL`, `PUBLIC_API_PROXY`, `RAILWAY_TOKEN` source note.
- `LOCAL.md` §1a: correct the "Railway production" note (dedicated pgbouncer service now exists).

```bash
git add docs/conventions.md docs/handoff/env-vars-registry.md LOCAL.md
git commit -m "docs: record pgbouncer service + new prod env vars"
graphify update .
```

**Gate P9:** dig → Railway, curl 200 + SSL green on both hostnames, check_ssr 13/13 on custom domain, docs committed.

---

### Task 10 (Phase 10): Cutover + drill

- [ ] **Step 1: Full DoD re-run on the new project** (verifier sub-agents — every gate from P2–P9 re-verified against `portfolio-sid-v2`)

- [ ] **Step 2: Restore drill** per `docs/handoff/restore-procedure.md` §3: scratch `postgres:16-alpine` container, fetch latest Railway backup (dashboard backups or `railway connect`-assisted dump), `pg_restore --no-owner --clean --if-exists`, row counts, `alembic_version` check, teardown. Record the result in `docs/conventions.md` (commit).

- [ ] **Step 3: Final hygiene**

```bash
git status                          # clean; no secrets
gh secret list --env production     # RAILWAY_TOKEN only
railway project list                # portfolio-sid-v2 only (old project already deleted)
```

**Gate P10:** DoD all green; restore drill executed + recorded; no secrets anywhere in git.

---

## DoD checklist (final)

- [ ] All 4 code services deploy from a GitHub push (native trigger) — SUCCESS
- [ ] CI fallback `workflow_dispatch` deploys all 4 (token verified against new project)
- [ ] backend: Uvicorn 8080, alembic clean single head, zero prepared-statement/auth errors, no public domain
- [ ] cron: `*/5` running, `promoted …` through pgbouncer
- [ ] pgbouncer: 6432, transaction, scram — connections visible in Postgres dashboard
- [ ] admin 200 + `/api/v1/health` 200 (+ self-heals across backend restarts)
- [ ] frontend `check_ssr.sh --all` 13/13, `/api/v1/health` 200, backend direct = private
- [ ] `NEXT_PUBLIC_INDEXABLE=false` · `CORS_ALLOW_ORIGINS` empty · no secrets in git
- [ ] custom domains SSL green on both hostnames · Cloudflare CNAMEs updated
- [ ] seed: 6 resumes / 14 timeline / 6 overview (+ PDF download 200)
- [ ] restore drill executed and recorded · docs updated (`conventions.md`, `env-vars-registry.md`, `LOCAL.md`)
