# Handoff — Cloudflare Removal & Revised Launch Plan

**Date:** 2026-08-28 · **Status:** PLAN — implementation deferred to next session
**Supersedes:** the Cloudflare-service-specific content of `HANDOFF-MANUAL-TASKS.md`.
**Companion docs:** `HANDOFF-MANUAL-TASKS.md` (manual task list), `env-vars-registry.md`, `conventions.md`.

---

## 1. Decision (locked)

**Remove all Cloudflare *services*; keep `siddhesh-chaudhari.com` at Cloudflare as
registrar + DNS only.** DNS records (Resend SPF/DKIM/DMARC, the admin/media
custom-domain A/AAAA/CNAME) still live in Cloudflare DNS — only the value-add
products are dropped.

| Dropped Cloudflare service | Replacement | Notes |
|---|---|---|
| **R2** object storage | **Railway Volume** (`storage_kind=local`) in prod; **MinIO** (`s3`) in local dev | `backend/app/core/storage.py` already has `LocalDiskStorage`; needs a `/media` static route + `media_base_url`. |
| **Turnstile** | **Self-hosted honeypot + rate-limit** | Backend already implements both (`forms/endpoints/router.py:52-70`). Turnstile is deletion/cleanup only. |
| **Web Analytics** | **Umami** (self-hosted) or none | `layout.tsx` beacon swap, env-gated. Umami instance hosted later ("prepare for hosting"). |
| **Tunnel** | **Railway custom domain** on the backend service | `admin.siddhesh-chaudhari.com` → backend; simpler; loses zero-public-port. |
| **Access** | `CF_ACCESS_ENABLED=false` permanently | App-layer auth (TD-17 session + Resend OTP) already covers admin. TD-36.S2 (Access-on) drops. |

**Not Cloudflare, unchanged:** Resend (TD-M3), Railway (TD-M4/M5), GitHub Actions, GlitchTip (TD-36).

**Why this is not a showstopper:** every Cloudflare coupling is isolated and
drop-in replaceable; `access.py` already returns early when
`CF_ACCESS_ENABLED=false` (the default), so the app was architected to run
without Access. The only "showstopper" was logistical (domain transfer) — avoided
by keeping the domain at Cloudflare.

---

## 2. Execution order (as directed)

1. **Code changes** (this plan §3) — done first.
2. **Infra tasks** — revised TD-M1 (done) → M2 → M3 → M4 → M5 → M6 → TD-36 partial.
3. **Prepare for hosting** — provision Railway Volume, self-host Umami, DNS cutover prep.
4. **UI changes** — TD-34 (reskin), TD-35 (a11y/perf). Per direction, these run
   *before* final hosting, after infra + prep.
5. **Host on Railway** — deploy, cutover, indexing, GlitchTip, restore drill,
   journeys, content authoring.

---

## 3. Code prerequisites (exact edit map)

### 3.1 Storage — backend-served `/media` + Railway Volume
- `backend/app/app.py`
  - `from fastapi.staticfiles import StaticFiles`.
  - In `create_app()`, **before** `register_routers(app)`, when
    `settings.storage_kind == "local"`: `Path(settings.local_storage_dir).mkdir(parents=True, exist_ok=True)`
    then `app.mount("/media", StaticFiles(directory=...), name="media")`.
  - Must be registered before the SPA catch-all (`app.py:143`) so `/media/*`
    is not swallowed by `index.html` fallback.
- `backend/app/core/config.py:19-20` — `storage_kind` / `local_storage_dir` exist;
  add `media_base_url: str | None = None` near them.
- `backend/app/core/storage.py:119-120` — `LocalDiskStorage.get_url` currently
  returns `f"/media/{key}"`; change to return
  `f"{media_base_url.rstrip('/')}/media/{key}"` when `media_base_url` is set
  (absolute, so the public frontend — a separate service — can load it).
- `frontend/next.config.ts:7-19` — replace the hardcoded
  `media.siddhesh-chaudhari.com` remotePattern with the host parsed from
  `process.env.NEXT_PUBLIC_API_BASE_URL` (the backend/media host), keeping
  `localhost` and `localhost:9000` (MinIO dev).

### 3.2 Turnstile → honeypot + rate-limit (backend already done)
- `backend/app/features/forms/endpoints/router.py`
  - Delete `from app.core.turnstile import verify_turnstile` (line 14).
  - Delete the Turnstile block (lines 57-65). **Keep** honeypot (52-55) and
    the DB rate-limit (67-70, 105-115).
- Delete `backend/app/core/turnstile.py`.
- `backend/app/core/config.py:32-33` — remove `turnstile_secret_key` /
  `turnstile_site_key`.
- `frontend/features/forms/ContactForm.tsx`
  - Remove `siteKey` prop (6, 20), the Turnstile `<script>` effect (29-47),
    token fetch/verify (54-69), the `cf-turnstile` div (156-160), and the
    `turnstile_token` field in the POST body (81). **Keep** the honeypot
    `<input name="_hpt">` (100-109) and send `_hpt: ""`.
- `frontend/features/forms/DealflowForm.tsx` — same edits (33-49, 62-77, 90,
  191-195).
- `frontend/app/contact/page.tsx:137` and `frontend/app/dealflow/page.tsx:29`
  — drop `SITE_KEY` and the `siteKey` prop.

### 3.3 Analytics — Cloudflare → Umami (self-hosted, env-gated)
- `frontend/app/layout.tsx:23-37` — replace the Cloudflare beacon
  (`static.cloudflarestorage.com/beacon.min.js`) with an Umami script gated on
  `process.env.NEXT_PUBLIC_UMAMI_SRC` + `process.env.NEXT_PUBLIC_UMAMI_WEBSITE_ID`.
  (Umami *instance* is stood up in "prepare for hosting".)

### 3.4 Docs (planning, do alongside code)
- `docs/conventions.md` — Domain line: drop "Tunnel + Access"; #14 wording:
  "same-origin by construction via tunnel" → "same-origin (admin SPA + `/api/*`
  on one hostname, no Cloudflare Tunnel)".
- `docs/handoff/env-vars-registry.md` — drop `R2_*` / `TURNSTILE_*`; add
  `STORAGE_KIND`, `LOCAL_STORAGE_DIR`, `MEDIA_BASE_URL`, `NEXT_PUBLIC_UMAMI_SRC`,
  `NEXT_PUBLIC_UMAMI_WEBSITE_ID`; keep `RESEND_*`, `GLITCHTIP_*`, `RAILWAY_TOKEN`.
- Amend spec cards `TD-M2`, `TD-M4`, `TD-M6` to record the deltas (or rely on
  this handoff as the delta source).

---

## 4. Revised infra task flow (next session)

- **TD-M1** ✅ DONE this session (zone Active at Cloudflare; renewal/WHOIS in `conventions.md`).
- **TD-M2 (revised)** — No R2 bucket, no Turnstile widget, no CF analytics.
  Instead: provision Railway Volume + set `STORAGE_KIND=local`; finalize
  captcha (done via §3.2) + analytics (Umami per §3.3). Verify: `dig +short
  admin.siddhesh-chaudhari.com` resolves to Railway; `grep -c "STORAGE_KIND"
  env-vars-registry.md`.
- **TD-M3** — unchanged (Resend; DNS records still in Cloudflare DNS).
- **TD-M4 (revised env)** — drop `R2_*`/`TURNSTILE_*`; add `STORAGE_KIND=local`,
  `LOCAL_STORAGE_DIR=/data`, `MEDIA_BASE_URL=https://admin.siddhesh-chaudhari.com`,
  analytics var; frontend service uses **Railway native Next.js preset** (no
  `frontend/Dockerfile` — gap resolved). Keep `CORS_ALLOW_ORIGINS` empty; record
  backup policy in `conventions.md`.
- **TD-M5** — unchanged (auto-deploy off; `RAILWAY_TOKEN` as `production`
  environment secret).
- **TD-M6 (revised)** — "Expose admin via Railway custom domain;
  `CF_ACCESS_ENABLED=false`; no tunnel/Access." Verify:
  `curl -sI https://admin.siddhesh-chaudhari.com` → SPA; API works same-origin.
- **TD-36 partial** — cutover (custom domains → Railway), **no Access-on step**,
  GlitchTip, restore drill, indexing after routes verified; S5 (Playwright) /
  S6 (content) deferred to the UI phase.

---

## 5. Definition of Done (full manual session, revised)

- [ ] Domain at Cloudflare (registrar+DNS) Active; renewal price + WHOIS in `conventions.md`.
- [ ] Storage: Railway Volume + `STORAGE_KIND=local` in prod; `/media` served by
      backend; local MinIO for dev; remotePatterns updated.
- [ ] Captcha: honeypot + rate-limit only (no third-party); Turnstile code removed.
- [ ] Analytics: Umami (self-hosted) or none, env-gated; CF beacon removed.
- [ ] TD-M3: Resend verified; SPF/DKIM/DMARC in Cloudflare DNS.
- [ ] TD-M4: Postgres + backend (Dockerfile) + frontend (native preset) + cron
      live; `CORS_ALLOW_ORIGINS` empty; backup policy recorded.
- [ ] TD-M5: auto-deploy off; `RAILWAY_TOKEN` is a `production` environment secret.
- [ ] TD-M6: admin on Railway custom domain; `CF_ACCESS_ENABLED=false` permanent.
- [ ] TD-36 partial: cutover + indexing, GlitchTip, restore drill complete;
      Access-on step dropped; S5/S6 deferred.
- [ ] No secret value in git; `git grep` for literals clean.
- [ ] All `Verify` commands per spec return green.

---

## 6. Open items to resolve in "prepare for hosting"

- **Umami instance:** where self-hosted (separate Railway service + DB, or
  elsewhere)? Decide before §3.3 is wired to a live ID.
- **Media host confirmation:** `MEDIA_BASE_URL=https://admin.siddhesh-chaudhari.com`
  assumes media is served by the backend service. Confirm before cutover.
- **Public vs admin services:** frontend (public) and backend (admin+API+media)
  remain two Railway services + Postgres + cron; cloudflared service is dropped.
