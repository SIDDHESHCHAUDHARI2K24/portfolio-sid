# Manual Checklists (user-executed To-Dos)

Record every value back into `env-vars-registry.md`. No secret values in either file — record *where* a value lives, not the value.

## TD-M1 — Verify Cloudflare zone

Domain `siddhesh-chaudhari.com` is already registered and delegated. Confirm it settled.

1. Cloudflare dashboard → select zone `siddhesh-chaudhari.com` → Overview: status reads **Active**.
2. Registrar dashboard: note renewal price + confirm WHOIS privacy active; record both in `docs/conventions.md`.
3. Agent verifies: `dig NS siddhesh-chaudhari.com +short` → returns Cloudflare nameservers.

## TD-M2 — R2 bucket + Turnstile + Web Analytics

**R2** (Cloudflare dashboard → R2 Object Storage):
1. Purchase R2 plan if prompted → Create bucket: name `portfolio-media`, location default.
2. R2 → Manage R2 API Tokens → Create API token:
   - Permissions: **Object Read & Write**
   - Scope: **bucket-specific** → `portfolio-media` (NOT account-wide)
   - Record: Access Key ID → `R2_ACCESS_KEY_ID`, Secret Access Key → `R2_SECRET_ACCESS_KEY` (shown once), endpoint `https://<account-id>.r2.cloudflarestorage.com` → `R2_ENDPOINT`.
3. Bucket → Settings → Custom Domains → connect `media.siddhesh-chaudhari.com` (Cloudflare auto-creates DNS + TLS). Record → `R2_PUBLIC_BASE_URL = https://media.siddhesh-chaudhari.com`.
4. Agent verifies: `aws s3 cp` test object up/down with `--endpoint-url $R2_ENDPOINT`.

**Turnstile** (Cloudflare → Turnstile → Add site):
1. Widget name: `portfolio`; mode: **Managed**.
2. Hostnames: `siddhesh-chaudhari.com`, `admin.siddhesh-chaudhari.com`, `*.up.railway.app`, `localhost`.
3. Record Site Key (public → frontend `TURNSTILE_SITE_KEY`) and Secret Key (→ backend `TURNSTILE_SECRET_KEY`).
4. Agent verifies: widget renders on a local dev page; `/siteverify` succeeds with a real token.

**Web Analytics** (Cloudflare → Analytics & Logs → Web Analytics → Add site):
1. Add `siddhesh-chaudhari.com`; copy the beacon token (or use the automatic JS snippet). Record token location.
2. Agent verifies: beacon script in `app/layout.tsx`; a test pageview appears in the dashboard.

## TD-M3 — Resend domain verification

1. Resend dashboard (resend.com) → Domains → Add Domain: `siddhesh-chaudhari.com`.
2. Copy the issued records into Cloudflare DNS (Cloudflare → DNS → Records), each as **DNS only (grey cloud)** — never proxied:
   - SPF: `TXT` on `send` (as Resend specifies)
   - DKIM: `TXT` records on `resend._domainkey` (as issued)
3. Add DMARC: `TXT` on `_dmarc` with `v=DMARC1; p=none;` (visibility only).
4. Back in Resend → Domains → Verify (may take minutes).
5. Resend → API Keys → Create API Key (full access) → backend `RESEND_API_KEY`.
6. Agent verifies: `dig TXT send.siddhesh-chaudhari.com`, `dig TXT _dmarc.siddhesh-chaudhari.com`; send test email via Resend API to `ADMIN_EMAIL` — arrives in inbox, not spam.

## TD-M4 — Railway project setup (paired)

1. Railway dashboard → New Project → **PostgreSQL 16**. Note: internal URL (backend/cron) and public URL (local Alembic).
2. **Decide backup policy now** (see `restore-procedure.md`, gap G12): Railway plan supports backups? If not automatic → weekly `pg_dump` cron to R2 is mandatory before any content is authored. Record the decision in `docs/conventions.md`.
3. New Service → GitHub repo → **backend**. Service Settings → Root Directory: set so build context covers both `backend/` and `admin/` (multi-stage Dockerfile needs both; if Railway root dir must be repo root, leave empty and let the Dockerfile paths do the work — confirm build succeeds either way).
4. Wire backend env per `env-vars-registry.md` (Backend table). Generate `SESSION_SECRET`; set `CORS_ALLOW_ORIGINS` **empty**; `CF_ACCESS_ENABLED=false`.
5. New Service → **frontend** (`frontend/Dockerfile`): wire Frontend table env.
6. New Service → **cron**: same image as backend, start command `uv run python -m app.jobs.scheduler`, schedule every 5 min, backend env subset.
7. Agent verifies: `curl <backend-url>/health` → `{"status":"ok"}`; `curl <frontend-url>` returns content-bearing HTML; cron exits 0 in logs.

## TD-M5 — GitHub: auto-deploy off + environment secret

1. Railway: each service → Settings → Deployments/Source → **disconnect GitHub repo or disable automatic deploys**.
2. Railway → Account Settings → Tokens → New Project Token (or project-level) → copy.
3. GitHub repo → Settings → Environments → New environment → name `production`:
   - Required reviewers: you. **Leave "prevent self-review" OFF** (sole maintainer).
   - Deployment branch rule: `main` only.
   - Add secret `RAILWAY_TOKEN` = the token from step 2. Environment secret only — never a repository secret.
4. Agent verifies: push to `main` triggers no Railway deploy; `railway up --service backend` succeeds locally with the token.

## TD-M6 — Cloudflare Tunnel + Access (paired)

**Tunnel** (Cloudflare Zero Trust → Networks → Tunnels):
1. Create a tunnel → **Cloudflared** connector → name it (e.g. `portfolio-admin`). Copy the token.
2. Public Hostname: `admin.siddhesh-chaudhari.com` → service: backend's Railway **internal** address (`http://<backend-internal>:<port>`).
3. Railway tunnel service: image `cloudflared/cloudflared`, start `cloudflared tunnel run --token <token>` with env `CLOUDFLARE_TUNNEL_TOKEN`.
4. **One hostname covers SPA + `/api/*`** — never split across subdomains (CORS preflights would redirect to the login page and fail).

**Access** (Zero Trust → Access → Applications → Add):
1. Self-hosted app; domain: `admin.siddhesh-chaudhari.com` only (single hostname).
2. Policy: Allow → Include → Emails: your email. Login method: **One-time PIN (email OTP)**.
3. Application settings → copy **Application AUD** → `CF_ACCESS_AUD`; team domain `<team>.cloudflareaccess.com` → `CF_ACCESS_TEAM_DOMAIN`.
4. Agent verifies: `curl -I https://admin.siddhesh-chaudhari.com` → redirects to Access login; with `CF_ACCESS_ENABLED=true` backend rejects requests lacking `Cf-Access-Jwt-Assertion`; `=false` restores app-layer-only auth.
