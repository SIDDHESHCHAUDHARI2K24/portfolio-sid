# Handoff — Remaining Manual Tasks (next session)

**Date:** 2026-08-31 · **Status:** READY — infra bootstrap done, secrets/DNS + cutover remain
**Prerequisites:** `docs/handoff/HANDOFF-RAILWAY-INFRA-PLAN.md` (code removal Done), `SESSION-HANDOFF-RAILWAY-INFRA-COMPLETE.md` (bootstrap Done, bridge live), `docs/handoff/POST-DEVELOPMENT-RECAP-2026-08-30.md` (resume canon + timeline detail + pgBouncer shipped)
**Invariants:** `docs/conventions.md` #13 `NEXT_PUBLIC_INDEXABLE=false` until launch, #14 `CORS_ALLOW_ORIGINS` empty (same-origin `admin.siddhesh-chaudhari.com`), #15 secrets only in Railway env / `production` env secret / local `.env`
**Execution order:** Do not reorder — TD-M2→M3→M4→M5→M6→TD-36 partial → Prepare hosting → UI TD-34/35 → Host (per `HANDOFF-RAILWAY-INFRA-PLAN.md:33`)

> This is the **single handoff** the next manual session should read. Code-phase tasks (resume variant 6-string `869fc8d8c856`, `seed_resumes.py`, `/timeline/[id]` detail, `ContactResumes.tsx` filtered, `pgbouncer` `6432`) are Done and verified — do not re-implement. Only infra/DNS/secrets remain here plus deferred feature notes.

---

## 0. What is DONE (code phase, 2026-08-30 build session)

| Area | Artefact | Verify |
|---|---|---|
| Storage | `backend/app/core/storage.py` `LocalDiskStorage.get_url` absolute, `app.py` mounts `/media` when `STORAGE_KIND=local` | `/media/` on backend, `file_url`/`icon_url` absolute |
| Turnstile/Analytics | `turnstile.py` deleted, honeypot+per-IP rate-limit kept, `layout.tsx` Umami gated | grep `turnstile|cloudflare` zero |
| Resume canon | `backend/scripts/resume_canon.json:1` 11 tags/14 timeline (inc umbrella+Feenix Sports `2026-07` pinned)/5 projects/43 skills/6 resumes/6 intros, `.gitignore:4` `resumes/*.pdf` | `seed_resumes.py --dry-run` 6 PDFs hashed `resumes/{variant}-{sha12}.pdf` |
| Seeding | `backend/scripts/seed_resumes.py:1` idempotent UPSERT + revalidation `[timeline,projects,skills,resumes,overview,relevance]` | `uv run --project backend python backend/scripts/seed_resumes.py --canon ... --dry-run` + real run → `.storage/resumes/*` 6 files, `pytest .../resumes` 9 passed |
| Variant | `backend/app/features/resumes/models.py:12` VARCHAR 6 `ALLOWED_VARIANTS`, admin `ResumeForm:31` / `Contact page.tsx` grid | `pytest .../resumes` 6 passed, `frontend` `○ /contact` static |
| Timeline detail | `/timeline/[id]` RSC `frontend/app/timeline/[id]/page.tsx:1`, `GET /timeline/{id}/projects` scoped endpoint, public-filter 404 on drafts, list link + sitemap | `pytest .../timeline .../projects` 27 passed, `npm run build` `ƒ /timeline/[id]` |
| Contact/selector | `ContactResumes.tsx:1` audience filter (`default` all 6 per `ResumeAudienceMap`), `HUD.tsx:13`/`IntroOverlay.tsx:19` Show everything hidden | `grep -R Show\ everything frontend` 0, `grep -R cookies() frontend/app/timeline/[id]` 0 |
| pgBouncer | `docker-compose.yml:19` `pgbouncer` `6432` transaction `100/20/5`, `config.py:17` `database_pool_size/max_overflow/pgbouncer_enabled`, `database.py:1` `pool_pre_ping` QueuePool (not NullPool) | `docker compose config` valid, `test_pgbouncer_config.py` 8 passed |
| Builds | `openapi.json` 98k regenerated, `frontend/src/api.d.ts` + `admin/src/api.d.ts` regenerated | `npm run build --prefix frontend` 20 pages, `admin` 1993 modules gzip 143KB, `ruff check` All checks passed, `alembic heads` single `869fc8d8c856` |

**Local DB already seeded** — triage via `http://localhost:3000/timeline` + `…/timeline/{id}` + `…/projects` + `…/contact`, `http://localhost:5200/timeline` + `…/resumes`. Production DB still empty (needs same `seed_resumes.py` via `railway run` after secrets).

---

## 1. TL;DR — Current infra

| Service | Status | Env (set) | Env (NOT SET — secrets) |
|---|---|---|---|
| Postgres (`Postgres`) | ✅ | — | — |
| backend | ✅ `https://backend-production-7a2a.up.railway.app` | `DATABASE_URL=${{Postgres.DATABASE_URL}}` `STORAGE_KIND=local` `LOCAL_STORAGE_DIR=/data` `MEDIA_BASE_URL=https://admin.siddhesh-chaudhari.com` `CF_ACCESS_ENABLED=false` | `SESSION_SECRET` `ADMIN_PASSWORD_HASH` `RESEND_API_KEY` `REVALIDATION_SECRET` `ADMIN_EMAIL` |
| frontend | ✅ `https://frontend-production-38ac.up.railway.app` | `NEXT_PUBLIC_API_BASE_URL=https://backend-production-7a2a.up.railway.app` (bridge, reverts after DNS) `NEXT_PUBLIC_INDEXABLE=false` | `NEXT_PUBLIC_UMAMI_SRC/_WEBSITE_ID` `NEXT_PUBLIC_GLITCHTIP_DSN` (TD-36) |
| cron | ✅ (no public domain) | same as backend | same |
| Volume | `backend-volume` `/data` Ready | — | — |
| Build settings | `source.rootDirectory=/frontend` (GraphQL), `cron startCommand=python -m app.jobs.scheduler` | `railway.toml` deprecated — CLI + GraphQL are source of truth | — |

**Invariants held:** #13 indexable false, #14 CORS empty, #15 no secrets in git/logs.

---

## 2. Remaining tasks (priority order — do not reorder, pause for User where noted)

### TD-M3 — Resend (unchanged, keep Resend per 2026-08-31 decision)
- **User:** verify `siddhesh-chaudhari.com` in Resend, publish SPF/DKIM/DMARC as **DNS-only (grey cloud)** in Cloudflare DNS (check `TD-M3-resend-verify.md` + `manual-checklists.md:TD-M3`)
- **Agent:** record locations in `env-vars-registry.md:25` reference table
- **Verify:** Resend dashboard `Verified`, `dig TXT siddhesh-chaudhari.com` + `dig TXT resend._domainkey.siddhesh-chaudhari.com` + `dig TXT _dmarc.siddhesh-chaudhari.com` present

> **EmailProvider abstraction (deferred):** `docs/specs/email-provider/PLAN.md` (to be authored) keeps `resend` SaaS. Self-host `sluhtie/freesend` (**note:** `freesend.io` is a file-transfer product, not email) or raw SMTP/SES is a future swap via `EMAIL_PROVIDER=resend|freesend|smtp|ses` in `backend/app/core/email.py:1` (swap only this file, keep `send_email/send_otp` signatures). Do not implement this handoff — `Resend` stays prod.

### TD-M4 — Secrets (blocking admin login + email) — do first in next session
- **User:** provide 5 values — `SESSION_SECRET` (`openssl rand -hex 32`), `ADMIN_PASSWORD_HASH` (`uv run --project backend python -m app.cli hash-password <pw>`), `RESEND_API_KEY`, `REVALIDATION_SECRET` (share with frontend build env), `ADMIN_EMAIL`
- **Agent:** `railway variable set VAR --stdin --service backend` (per `env-vars-registry.md`), also `cron` same core env, then `railway up --service backend --detach` + `cron`; `railway logs --service backend --lines 50` no `RESEND_API_KEY not configured`
- **Verify:** `POST /api/v1/auth/login` → `{detail: ...}` generic, OTP email arrives, `curl /api/v1/health` 200

### TD-M5 — Auto-deploy off + RAILWAY_TOKEN (GitHub production env secret)
- **User:** in Railway disable auto-deploy on every service, generate project token
- **Agent:** `gh api` add `RAILWAY_TOKEN` as **`production` ENVIRONMENT secret** (not repo secret) + wire `deploy.yml` `railway up backend/cron/frontend --detach` if missing; record location in `env-vars-registry.md:55`
- **Verify:** push to `main` does not trigger Railway; `gh secret list -e production` shows `RAILWAY_TOKEN`

### TD-M6 — Admin custom domain (single hostname, no tunnel/Access)
- **Agent:** Railway Custom Domain `admin.siddhesh-chaudhari.com` → **backend** service (SPA + `/api/*` + `/media` on one hostname per `conventions.md:6`), confirm `CF_ACCESS_ENABLED=false`
- **User:** Cloudflare DNS point `admin.siddhesh-chaudhari.com` → Railway target, wait SSL
- **Verify:** `curl -sI https://admin.siddhesh-chaudhari.com` → SPA, `curl /api/v1/health` same-origin, `dig +short admin.siddhesh-chaudhari.com` → Railway

### Bridge revert (tied to TD-M6)
- Once `admin.siddhesh-chaudhari.com` live: `railway variable set NEXT_PUBLIC_API_BASE_URL=https://admin.siddhesh-chaudhari.com --service frontend` then `railway up --service frontend --detach`; then `bash scripts/check_ssr.sh --all https://admin.siddhesh-chaudhari.com` 13/13. **Do not flip early** (ENOTFOUND on build).

### TD-36 partial — cutover + GlitchTip + restore drill + indexing guard
- **User:** provide `GLITCHTIP_DSN` (+ `NEXT_PUBLIC_GLITCHTIP_DSN`), decide Umami hosting (separate Railway service+DB vs external) → then `NEXT_PUBLIC_UMAMI_SRC/_WEBSITE_ID`
- **Agent:** set GlitchTip vars, run **from-scratch restore into scratch DB** per `restore-procedure.md` (never prod), keep `NEXT_PUBLIC_INDEXABLE=false` until all routes on `admin.siddhesh-chaudhari.com` verified + submitted to GSC
- **Verify:** GlitchTip receives event, restore drill succeeds, `grep NEXT_PUBLIC_INDEXABLE docs/conventions.md` still false

### TD-M1 gap — renewal price (housekeeping)
- **User:** confirm in Cloudflare Domains dashboard (auto-renew on, WHOIS privacy) → **Agent:** patch `docs/conventions.md:14` `TBD` → value + `dig NS siddhesh-chaudhari.com` check

### Prod resume canon (after secrets + DNS)
```bash
railway run --service backend -- uv run python backend/scripts/seed_resumes.py --canon backend/scripts/resume_canon.json --dry-run
railway run --service backend -- uv run python backend/scripts/seed_resumes.py --canon backend/scripts/resume_canon.json
curl -s https://admin.siddhesh-chaudhari.com/api/v1/resumes | jq '.[].variant'
curl -s https://admin.siddhesh-chaudhari.com/api/v1/timeline | jq length
bash scripts/check_ssr.sh --all https://admin.siddhesh-chaudhari.com && scripts/check_ssr.sh --seo https://admin.siddhesh-chaudhari.com
```

---

## 3. Deferred features (not in this handoff's execution)

| Feature | Decision | Plan doc | When |
|---|---|---|---|
| Email self-host (`freesend`/`sluhtie/freesend`) | **Keep Resend** — add swappable `EmailProvider` later (`resend|freesend|smtp|ses`, `Mailpit` dev). `freesend.io` ≠ email. | `docs/specs/email-provider/PLAN.md` (deferred, ~30 LoC in `email.py:1`) | After hosting stable |
| Temporal | **Deferred** — `scheduler.py:1` stays cron 5-min + 90d retention (idempotent, 8 models). F29 voice agent `backend/app/features/agent/` deferred. | No code now; ADR `scheduler remains registry-driven` | Until F29 gains durable timers/retries (STT→LLM→TTS) |

---

## 4. Useful commands (copy-paste)

```bash
railway status; railway service status -s backend; railway service status -s frontend; railway service status -s cron
railway logs --service backend --lines 50; railway logs --service frontend --lines 50; railway logs --service cron --lines 50
railway variable set SESSION_SECRET --stdin --service backend
railway variable set ADMIN_PASSWORD_HASH --stdin --service backend  # uv run --project backend python -m app.cli hash-password <pw>
railway variable set RESEND_API_KEY --stdin --service backend
railway variable set REVALIDATION_SECRET --stdin --service backend
railway variable set ADMIN_EMAIL --stdin --service backend
railway up --service backend --detach; railway up --service cron --detach
bash scripts/check_ssr.sh --all https://admin.siddhesh-chaudhari.com
bash scripts/check_ssr.sh --seo https://admin.siddhesh-chaudhari.com
TOKEN=<RAILWAY_TOKEN>
curl -s https://backboard.railway.app/graphql/v2 -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"query":"mutation { serviceInstanceUpdate(serviceId:\"0193fd03-ff6c-4022-83fb-df4b3364ef82\", environmentId:\"09b974a1-c963-4e29-bdcb-1d27abe887e2\", input: { rootDirectory: \"/frontend\" }) }"}'
```

---

## 5. Git state at handoff (2026-08-31)

- **Done commits pending push:** infrastructure bootstrap (`awake-success` `5edae34e...`, `production` `09b974a1...`, `Postgres` capital P), pgBouncer `6432`, resume variant `869fc8d8c856`, seed `resume_canon.json` + `seed_resumes.py`, timeline detail `/timeline/[id]` + `/{id}/projects`, contact `ContactResumes.tsx` + HUD/intro cleanup.
- **Working tree:** 36 tracked mods + 7 untracked `backend/scripts/*`, `frontend/app/timeline/[id]/`, `docs/specs/*`, `docs/specs/timeline-detail/`, `doctor.config.ts`, etc. — see `git status --short`. `resumes/*.pdf` now gitignored (`resumes/.gitkeep` tracked). `RAILWAY_TOKEN c5e95764...` rotate after use.
- **DoD before UI:** secrets set, bridge reverted, domain + SSL green, SSR 13/13 + SEO 6/6, restore drill passed, `NEXT_PUBLIC_INDEXABLE` still false. UI `TD-34/35` MUST NOT start until this handoff's infra is PASS.
