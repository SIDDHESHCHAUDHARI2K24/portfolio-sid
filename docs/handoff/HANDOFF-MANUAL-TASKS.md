# Handoff — Manual Infra & Launch Tasks (TD-M1…M6, TD-36)

<!-- REVISED 2026-08-28: Cloudflare services removed (domain/DNS kept). Authoritative revised plan + exact code-edit map: docs/handoff/HANDOFF-CLOUDFLARE-REMOVAL-PLAN.md -->

## ⚠ Revised plan (2026-08-28) — Cloudflare services removed

Keep `siddhesh-chaudhari.com` at Cloudflare as **registrar + DNS only**. Drop
R2, Turnstile, Web Analytics, Tunnel, Access. Replacements: Railway Volume /
MinIO (storage), self-hosted honeypot + rate-limit (captcha), Umami (analytics),
Railway custom domain (admin ingress), `CF_ACCESS_ENABLED=false` (auth).

**Authoritative revised plan + exact code-edit map:** `docs/handoff/HANDOFF-CLOUDFLARE-REMOVAL-PLAN.md`.
The Cloudflare-service-specific steps in the task sections below are superseded by that plan.
Execution order: **code → infra → prepare hosting → UI (TD-34/35) → host on Railway**.

**Purpose:** A self-contained briefing for a session whose *only* goal is to
complete every user-executed / paired ("manual") task in the plan. The local
dev stack runs fully without any of these (see `LOCAL.md`); these are
**production-only** steps.

**Out of scope for that session:** UI work — `TD-34` (reskin) and `TD-35`
(a11y/perf polish) — are a separate phase that runs *after* the manual tasks.
`TD-36.S6` (content authoring) is user-executed and is included here as the
bridge into the UI phase.

**Source of truth reminder:** `docs/` is canonical. `development_plan/` mirrors
it. Invariants in `docs/conventions.md` are the architectural contract and must
not be violated while doing this work.

---

## 1. Spec existence audit (requirement: confirm each task has its own spec)

Every manual task **already has a dedicated spec card** in
`development_plan/todos/`. No new spec cards need to be authored.

| Task | Spec card | Has spec? |
|---|---|---|
| TD-M1 | `development_plan/todos/p0/TD-M1-cloudflare-zone.md` | ✅ yes |
| TD-M2 | `development_plan/todos/p0/TD-M2-r2-turnstile-analytics.md` | ✅ yes |
| TD-M3 | `development_plan/todos/p0/TD-M3-resend-verify.md` | ✅ yes |
| TD-M4 | `development_plan/todos/p0/TD-M4-railway-services.md` | ✅ yes |
| TD-M5 | `development_plan/todos/p0/TD-M5-railway-autodeploy-off.md` | ✅ yes |
| TD-M6 | `development_plan/todos/p0/TD-M6-tunnel-access.md` | ✅ yes |
| TD-36 | `development_plan/todos/p3/TD-36-launch.md` | ✅ yes |

**✅ Gap resolved (2026-08-28):** `frontend/Dockerfile` does not exist; the
backend `Dockerfile` only builds admin SPA + API. Decision: deploy the frontend
via **Railway's native Next.js preset** (no `frontend/Dockerfile` needed) — the
`output: "standalone"` in `frontend/next.config.ts` already satisfies it. See
`HANDOFF-CLOUDFLARE-REMOVAL-PLAN.md` §4 (TD-M4 revised).

---

## 2. Ordering / dependency map

```
TD-M1 (zone active)
 ├─→ TD-M2 (R2 + Turnstile + Analytics) ──→ TD-M4 (Railway services)
 │                                            ├─→ TD-M5 (auto-deploy off + token)
 │                                            └─→ TD-M6 (Tunnel + Access) ──→ TD-36
 ├─→ TD-M3 (Resend verify)        (blocks TD-17 OTP email; independent of M4)
 └─→ TD-M6 (also needs M1 + M4)
TD-36 (launch) also depends on code phases TD-31..35 (assumed complete before launch).
```

Recommended session order: **M1 → M2 → M3 → M4 (resolve Dockerfile gap) → M5 → M6 → TD-36**.

---

## 3. Global invariants to preserve while touching infra (`docs/conventions.md`)

- **#13 Noindex until launch:** `NEXT_PUBLIC_INDEXABLE` stays `false`; the
  Railway hostname must never be indexed. Flip only in TD-36.S1 after every
  route is verified on the custom domain.
- **#14 CORS empty in prod:** `CORS_ALLOW_ORIGINS` ships **explicitly empty**
  (same-origin by construction via tunnel). A non-empty value is a silent
  misconfiguration.
- **#15 Secrets:** only in Railway env vars / GitHub `production` environment
  secrets / local gitignored `.env`. Never git, logs, or response bodies.
  `env-vars-registry.md` records *locations*, never values.
- **Single hostname (TD-M6 / tech-stack-analysis §6.2):** one hostname carries
  both the admin SPA and `/api/*`. Splitting them makes CORS preflights redirect
  to the Access login page and fail, presenting as a CORS bug.
- **Backup policy decision (TD-M4 step 1 + TD-36.S4):** record in
  `docs/conventions.md`; if not automatic, a weekly `pg_dump`→R2 cron is
  mandatory *before any content is authored*.

---

## 4. Per-task detail (each tags every document to consult)

### TD-M1 — Verify Cloudflare zone active + renewal/WHOIS record
- **Spec:** `development_plan/todos/p0/TD-M1-cloudflare-zone.md`
- **Checklist:** `docs/handoff/manual-checklists.md` §TD-M1
- **Executor:** user (agent verifies after)
- **Depends on:** — · **Blocks:** TD-M2, TD-M3, TD-M6
- **Reference documents:**
  - `docs/handoff/manual-checklists.md` §TD-M1
  - `docs/conventions.md` (Domain section — record renewal price + WHOIS privacy)
  - `docs/development-plan-P0.md` (P0.T1.S1/S2)
- **Modify:** `docs/conventions.md` (Domain section)
- **Verify (agent):** `dig +short NS siddhesh-chaudhari.com`, `dig +short SOA …`,
  `grep -i renewal docs/conventions.md`
- **Status:** `[~]` — domain bought + NS delegated; zone-Active confirmation +
  renewal/WHOIS record still pending.

### TD-M2 — R2 bucket + Turnstile widget + Web Analytics
- **Spec:** `development_plan/todos/p0/TD-M2-r2-turnstile-analytics.md`
- **Checklist:** `docs/handoff/manual-checklists.md` §TD-M2
- **Executor:** user (agent verifies after)
- **Depends on:** TD-M1 · **Blocks:** TD-08 (R2 parity), TD-M4 (env wiring)
- **Reference documents:**
  - `docs/handoff/manual-checklists.md` §TD-M2 (R2 / Turnstile / Analytics)
  - `docs/handoff/env-vars-registry.md` (record `R2_*`, `TURNSTILE_*`,
    `CF_WEB_ANALYTICS_TOKEN` as references only)
  - `docs/development-plan-P0.md` (P0.T1.S3–S5)
- **Code referenced later (not edited in this task):** `backend/app/core/storage.py`
  (StorageAdapter, TD-08), `frontend/lib` Turnstile site key,
  `frontend/app/layout.tsx` (beacon, TD-33)
- **Verify (agent):** `dig +short media.siddhesh-chaudhari.com`; S3 round-trip via
  `aws s3 --endpoint-url`; `grep -c "R2_" docs/handoff/env-vars-registry.md`
- **Note:** R2 custom domain `media.siddhesh-chaudhari.com` needs the active zone
  from TD-M1. `r2.dev` URLs are explicitly not for production traffic.

### TD-M3 — Resend domain verification (SPF/DKIM/DMARC)
- **Spec:** `development_plan/todos/p0/TD-M3-resend-verify.md`
- **Checklist:** `docs/handoff/manual-checklists.md` §TD-M3
- **Executor:** user (agent verifies after)
- **Depends on:** TD-M1 · **Blocks:** TD-17 (admin OTP email delivery)
- **Reference documents:**
  - `docs/handoff/manual-checklists.md` §TD-M3
  - `docs/handoff/env-vars-registry.md` (`RESEND_API_KEY` reference)
  - `docs/development-plan-P0.md` (P0.T1.S6)
- **Verify (agent):** `dig +short TXT siddhesh-chaudhari.com`,
  `dig +short TXT resend._domainkey.siddhesh-chaudhari.com`,
  `dig +short TXT _dmarc.siddhesh-chaudhari.com`
- **Note:** until this is done, OTP email is mocked via the dev endpoint
  (`GET /api/v1/auth/dev/otp`); live admin OTP email won't deliver.

### TD-M4 — Railway: Postgres + backend/frontend/cron services
- **Spec:** `development_plan/todos/p0/TD-M4-railway-services.md`
- **Checklist:** `docs/handoff/manual-checklists.md` §TD-M4
- **Executor:** paired (user provisions + supplies secrets; agent does config/deploys/verify)
- **Depends on:** TD-09, TD-M2 · **Blocks:** TD-M5, TD-M6
- **Reference documents:**
  - `docs/handoff/manual-checklists.md` §TD-M4
  - `docs/handoff/env-vars-registry.md` (Backend + Frontend env tables)
  - `docs/conventions.md` (Postgres backup policy; CORS empty; secrets)
  - `docs/development-plan-P0.md` (P0.T2.S1–S4, P0.T4.S7)
- **Reference code:**
  - `backend/Dockerfile` (multi-stage: builds **admin SPA + API**, not the public frontend)
  - **`frontend/Dockerfile` — MISSING (see §1 gap).** Must be created.
  - `scripts/check_ssr.sh` (frontend SSR verification)
  - `backend/app/jobs/scheduler.py` (cron start command)
- **Modify:** `docs/conventions.md` (backup policy)
- **Verify (agent):** `railway status`; `curl -s $BACKEND_PUBLIC_URL/health`
  (expect `{"status":"ok"}`); `bash scripts/check_ssr.sh $FRONTEND_PUBLIC_URL`
- **Critical:** `CORS_ALLOW_ORIGINS` must be **empty** in production.

### TD-M5 — Railway auto-deploy OFF + RAILWAY_TOKEN env secret
- **Spec:** `development_plan/todos/p0/TD-M5-railway-autodeploy-off.md`
- **Checklist:** `docs/handoff/manual-checklists.md` §TD-M5
- **Executor:** user (agent verifies after)
- **Depends on:** TD-M4 · **Blocks:** TD-15 (deploy workflow activation)
- **Reference documents:**
  - `docs/handoff/manual-checklists.md` §TD-M5
  - `docs/handoff/env-vars-registry.md` (RAILWAY_TOKEN is a GitHub *environment*
    secret, not repo secret)
  - `docs/development-plan-P0.md` (P0.T2.S7)
  - `docs/specs/session-2/S2_T06_20260822-2212_ci-e2e-deploy.md` (deploy gate context)
- **Verify (agent):** push no-op to `main` → no Railway deploy triggered;
  `gh api …/environments/production/secrets` and `…/actions/secrets`;
  `railway up --service backend --detach`

### TD-M6 — Cloudflare Tunnel + Access (env-gated, single hostname)
- **Spec:** `development_plan/todos/p0/TD-M6-tunnel-access.md`
- **Checklist:** `docs/handoff/manual-checklists.md` §TD-M6
- **Executor:** paired (user: Zero Trust dashboard; agent: cloudflared service + JWT verify)
- **Depends on:** TD-M1, TD-M4 · **Blocks:** TD-36 (Access turned on permanently)
- **Reference documents:**
  - `docs/handoff/manual-checklists.md` §TD-M6
  - `docs/handoff/env-vars-registry.md` (`CF_TUNNEL_TOKEN`, `CF_ACCESS_ENABLED`,
    `CF_ACCESS_TEAM_DOMAIN`, `CF_ACCESS_AUD`)
  - `overall_context/tech-stack-analysis.md` §6.2 (single-hostname rationale)
  - `docs/development-plan-P0.md` (P0.T2.S5/S6)
- **Reference code:**
  - `backend/app/core/security.py` (Access JWT verification via PyJWT + team JWKS)
  - new `cloudflared` Railway service (`cloudflared tunnel run --token …`)
- **Verify (agent):** `curl -sI https://admin.siddhesh-chaudhari.com | head -5`;
  `curl -H 'Cf-Access-Jwt-Assertion: invalid' …/api/v1/health` (expect reject
  when `CF_ACCESS_ENABLED=true`)
- **Critical:** `CF_ACCESS_ENABLED=false` first (app-layer auth carries interim),
  flip to `true` only after verification; retain env-var rollback.

### TD-36 — Launch (cutover, Access, Sentry, restore drill, journeys, content)
- **Spec:** `development_plan/todos/p3/TD-36-launch.md`
- **Checklist:** `docs/handoff/content-authoring-checklist.md` (S6),
  `docs/handoff/restore-procedure.md` (S4); infra steps reuse
  `docs/handoff/manual-checklists.md`
- **Executor:** paired (user + agent)
- **Depends on:** TD-31..35 (all code) + TD-M1..M6 · **Blocks:** GATE-P3
- **Reference documents (tagged per sub-step):**
  - **S1 cutover + indexing:** `docs/handoff/manual-checklists.md` (M steps),
    `docs/conventions.md` (#13 noindex), `docs/development-plan-P3.md` (P3.T6.S1),
    Google Search Console
  - **S2 Access on:** `TD-M6` spec + `docs/handoff/env-vars-registry.md`
    (`CF_ACCESS_ENABLED`), `overall_context/tech-stack-analysis.md` §6.2
  - **S3 Sentry:** `docs/development-plan-P3.md` (P3.T6.S3) — FastAPI + Next.js;
    alert on revalidation-webhook / Resend / cover-fetch quiet failures
  - **S4 restore drill:** `docs/handoff/restore-procedure.md`, `docs/conventions.md`
    (backup policy), `docs/development-plan-P3.md` (P3.T6.S4)
  - **S5 Playwright journeys:** `frontend/tests/journeys/critical.spec.ts`,
    `LOCAL.md` §8, `docs/development-plan-P3.md` (P3.T6.S5)
  - **S6 content authoring (USER):** `docs/handoff/content-authoring-checklist.md`,
    `docs/development-plan-P3.md` (P3.T6.S6), `docs/conventions.md` (tile contract,
    audience tags) — this is the bridge to the UI phase
- **Verify (agent):** all routes over HTTPS on custom domain; Access rejects
  missing/invalid assertion; Sentry alert fires on deliberate revalidation
  failure; scratch-DB restore spot-checked; `npx playwright test` green in CI
  against production build.

---

## 5. Definition of Done for the manual session

> **REVISED DoD** (Cloudflare services removed) is in `HANDOFF-CLOUDFLARE-REMOVAL-PLAN.md` §5.
> The items below that reference R2 / Turnstile / Tunnel / Access are superseded by that plan.

- [ ] TD-M1: zone Active; renewal price + WHOIS recorded in `docs/conventions.md`
- [ ] TD-M2: R2 bucket + custom domain + bucket-scoped token; Turnstile widget;
      Analytics beacon; all referenced in `env-vars-registry.md` (no values in repo)
- [ ] TD-M3: Resend verified; SPF/DKIM/DMARC in zone; `RESEND_API_KEY` in registry
- [ ] TD-M4: Postgres + backend + frontend + cron live; **`frontend/Dockerfile`
      created**; backup policy in `docs/conventions.md`; `CORS_ALLOW_ORIGINS` empty
- [ ] TD-M5: auto-deploy off; `RAILWAY_TOKEN` is a `production` *environment* secret
- [ ] TD-M6: tunnel + Access up; single hostname; `CF_ACCESS_ENABLED` verified both states
- [ ] TD-36: cutover + indexing, Access on, Sentry, restore drill, journeys,
      content authoring complete
- [ ] No secret value committed to git; `git grep` for literals clean
- [ ] All `Verify` commands in each spec card return green

## 6. Next phase (after this handoff)

UI work only: `TD-34` (reskin — token swap per convention #12), `TD-35`
(a11y/perf), and any content-model gaps surfaced during `TD-36.S6`.
