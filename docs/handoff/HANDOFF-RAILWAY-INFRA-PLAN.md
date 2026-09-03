# Handoff — Railway Infra & Hosting (post code-removal)

**Date:** 2026-08-29 · **Status:** CODE PHASE DONE · INFRA PHASE PENDING
**Prerequisite doc:** `docs/handoff/HANDOFF-CLOUDFLARE-REMOVAL-PLAN.md` (the locked decision + code edit map)
**Companion docs:** `docs/handoff/env-vars-registry.md`, `docs/conventions.md` (invariants #13/#14/#15)

---

## 0. What is already DONE (this session, 2026-08-29)

All CODE CHANGES from the removal plan §3 are implemented and verified. **Do not re-implement them.** Summary:

- **Storage:** backend mounts `/media` (StaticFiles) when `STORAGE_KIND=local`; `config.media_base_url` added; `LocalDiskStorage.get_url` returns `{media_base_url}/media/{key}` when set. `next.config.ts` image `remotePatterns` now derived from `NEXT_PUBLIC_API_BASE_URL` + keeps `localhost:9000` (MinIO dev) + `localhost:3000`.
- **Turnstile removed:** `core/turnstile.py` deleted; forms router keeps honeypot + per-IP DB rate-limit; `turnstile_secret_key`/`turnstile_site_key` removed from config. Frontend forms (`ContactForm`, `DealflowForm`) and pages (`contact`, `dealflow`) stripped of Turnstile UI/`SITE_KEY`.
- **Analytics:** `layout.tsx` now gated Umami (`NEXT_PUBLIC_UMAMI_SRC` + `NEXT_PUBLIC_UMAMI_WEBSITE_ID`), no-ops when unset; CF beacon removed.
- **Media URLs (decision: backend returns full URL — user-approved):** `file_url`/`icon_url` added to resume/cert/skill API responses via `storage.get_url()` (auto env-aware: MinIO dev, `/media` prod). `CertViewer`, `SkillIcon`, `contact` page, `CertsClient`, `SkillsClient` consume the absolute URL. `openapi.json` + `frontend/src/api.d.ts` regenerated.

**Verification green:** `pytest app/features/forms` (8) + resumes/certs/skills/projects/collections (34); `npm run build` (clean tsc); `scripts/check_registries.py` ("All features registered"); `ruff check app`; grep for `turnstile|cloudflare|media.siddhesh-chaudhari.com` → **zero source matches**.

> **Repo note:** there is pre-existing uncommitted work (auth router, react-doctor) unrelated to this effort. Commit only the Cloudflare-removal changes when asked; do not sweep in the unrelated diffs.

---

## 1. Invariants you MUST preserve (conventions.md)

- **#13** `NEXT_PUBLIC_INDEXABLE` stays `false` until launch (TD-36, after every route verified on the custom domain + submitted to GSC). Never flip early.
- **#14** `CORS_ALLOW_ORIGINS` **empty in production** (same-origin by construction — admin SPA + `/api/*` on one hostname). Do not set a permissive value "temporarily."
- **#15** Never put secrets in git, logs, or response bodies. Record **locations only** in `env-vars-registry.md`. Generated secret values (e.g. `SESSION_SECRET`) are produced by the user / a safe generator and live only in Railway env or local gitignored `.env`.

---

## 2. Execution order (do not reorder)

1. **TD-M2** (Railway Volume + `STORAGE_KIND=local`) → **TD-M3** (Resend) → **TD-M4** (Railway services + env) → **TD-M5** (auto-deploy off + `RAILWAY_TOKEN` env secret) → **TD-M6** (admin custom domain, `CF_ACCESS_ENABLED=false`).
2. **TD-36 partial** — custom-domain cutover, GlitchTip, Postgres restore drill, indexing (deferred until routes verified). **No Access-on step.**
3. **Prepare for hosting** — provision Railway Volume attach, self-host Umami instance, DNS cutover prep.
4. **UI: TD-34 / TD-35** — MUST NOT start until infra (steps 1–3) is complete.
5. **Host on Railway** — final deploy, cutover, indexing, GlitchTip live, restore drill, journeys, content authoring.

---

## 3. Per-task plan (agent vs user, pause points, verify)

> Convention: **agent** = code/CLI work the session can do; **user** = dashboard/account/secret-value steps the session must PAUSE for. After each task's Verify commands pass, report PASS/FAIL explicitly. Do not advance until acceptance met.

### TD-M2 — Railway Volume + local storage (no R2, no Turnstile, no CF analytics)
- **Agent:** ensure backend mounts `/media` (already done in code). Document the Volume mount path expectation (`/data`) in `env-vars-registry.md` note.
- **User:** in Railway, create/attach a **Volume** to the backend service mounted at `LOCAL_STORAGE_DIR` (e.g. `/data`).
- **Agent:** set backend env `STORAGE_KIND=local`, `LOCAL_STORAGE_DIR=/data`, `MEDIA_BASE_URL=https://admin.siddhesh-chaudhari.com` (via `railway variables` or dashboard; record location only).
- **Verify:** `dig +short admin.siddhesh-chaudhari.com` resolves to Railway; `grep -c STORAGE_KIND docs/handoff/env-vars-registry.md` ≥ 1.
- **Decision carried:** captcha = honeypot+rate-limit (code done); analytics = Umami (code done, instance later).

### TD-M3 — Resend (unchanged)
- **User:** verify `siddhesh-chaudhari.com` in Resend; add the Resend SPF/DKIM/DMARC **DNS records in Cloudflare DNS** (DNS only — Cloudflare stays registrar+DNS).
- **Agent:** record the DNS-record requirement + Resend status location in `env-vars-registry.md` (dashboard-held values table). No code change.
- **Verify:** Resend domain shows "Verified"; DNS records present in Cloudflare.

### TD-M4 — Railway services + env (revised)
- **Agent (code/CLI):** confirm backend has a `Dockerfile` (TD-09 exists); confirm **frontend uses Railway native Next.js preset — no `frontend/Dockerfile`** (gap resolved). Wire env per registry: backend gets `DATABASE_URL` (internal), `STORAGE_KIND`, `LOCAL_STORAGE_DIR`, `MEDIA_BASE_URL`, `RESEND_API_KEY`, `ADMIN_EMAIL`, `SESSION_SECRET` (user-generated), `ADMIN_PASSWORD_HASH` (user-generated via CLI), `REVALIDATION_SECRET`, `CORS_ALLOW_ORIGINS=` (empty), `CF_ACCESS_ENABLED=false`, `GLITCHTIP_DSN` (TD-36). Frontend gets `NEXT_PUBLIC_API_BASE_URL`, `NEXT_PUBLIC_INDEXABLE=false`, `REVALIDATION_SECRET` (same value), `NEXT_PUBLIC_UMAMI_SRC`/`_WEBSITE_ID` (TD-36). Cron reuses backend image + same core env.
- **User:** provide secret **values**: `SESSION_SECRET` (`openssl rand -hex 32`), `ADMIN_PASSWORD_HASH` (from `uv run python -m app.cli hash-password`), `RESEND_API_KEY`, `REVALIDATION_SECRET`, `ADMIN_EMAIL`. Record locations only.
- **Verify:** `railway status`; `curl $BACKEND/health` → `{"status":"ok"}`; `bash scripts/check_ssr.sh $FRONTEND`. Record Postgres backup policy in `conventions.md` (TD-M4 gap G12).

### TD-M5 — auto-deploy off + RAILWAY_TOKEN
- **User:** in Railway, disable auto-deploy on every service; generate a project token.
- **Agent:** add `RAILWAY_TOKEN` as a **GitHub `production` ENVIRONMENT secret** (not repo secret) via the `gh` CLI / dashboard; record location in `env-vars-registry.md`. Wire TD-15 deploy workflow if not already.
- **Verify:** protected-environment rule present; `gh secret list -e production` shows `RAILWAY_TOKEN`.

### TD-M6 — admin custom domain, Access off (revised)
- **Agent:** configure a **Railway Custom Domain** `admin.siddhesh-chaudhari.com` → **backend service** (single hostname for SPA + `/api/*` + `/media`). Ensure `CF_ACCESS_ENABLED=false` is set (done in TD-M4).
- **User:** in Cloudflare DNS, point `admin.siddhesh-chaudhari.com` (and the `media` host if separate) at the Railway-provided target; **no cloudflared/tunnel service**.
- **Verify:** `curl -sI https://admin.siddhesh-chaudhari.com` → SPA; `curl https://admin.siddhesh-chaudhari.com/api/v1/...` works same-origin.

### TD-36 partial — cutover + GlitchTip + restore drill + indexing
- **User:** provide `GLITCHTIP_DSN` (+ `NEXT_PUBLIC_GLITCHTIP_DSN`).
- **Agent:** set GlitchTip vars; run a **Postgres restore drill into a scratch DB**; flip `NEXT_PUBLIC_INDEXABLE` only after every route verified on the custom domain + submitted to GSC. **Defer S5 (Playwright) and S6 (content authoring) to the UI phase.**
- **Verify:** GlitchTip receives events; restore drill succeeds; `NEXT_PUBLIC_INDEXABLE` still `false` until the explicit TD-36 flip.

### Prepare for hosting
- **Decide (ask user):** where to self-host **Umami** — separate Railway service + DB, or elsewhere. Then set `NEXT_PUBLIC_UMAMI_SRC`/`_WEBSITE_ID`.
- **Confirm (ask user):** `MEDIA_BASE_URL=https://admin.siddhesh-chaudhari.com` assumes backend serves `/media` (it does, per code). Confirm before cutover.
- Two Railway services (frontend public, backend admin+API+media) + Postgres + cron; cloudflared dropped.

---

## 4. Open items to resolve in this phase
- Umami hosting location (separate service vs external) — blocks final `NEXT_PUBLIC_UMAMI_*` values.
- Postgres backup policy text for `conventions.md`.
- Restore-drill runbook location (create `restore-procedure.md` if missing — gap G12).

---

## 5. Commits
Conventional (`feat`/`fix`/`chore`). **Only docs changes get `doc:` commits; never commit secrets.** Stage only the intended files.
