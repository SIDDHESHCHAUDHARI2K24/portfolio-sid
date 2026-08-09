# Development Plan — Phase 0: Foundations

**Document 3 of 3, Part 1** · Companions: `tech-stack-analysis.md`, `dependency-map.md`
**Status:** Draft for approval
**Feature IDs:** F0 (toolchain), F30 (infrastructure), F1 (monorepo), F8 (design tokens)

---

## Phase Overview

**Goal:** Establish every foundation that later phases depend on, so that Phase 1's spine and Phase 2's six parallel tracks proceed without stopping to make infrastructure or tooling decisions.

**Entry criteria:** None. This is the first phase.

**Exit criteria:**
- Domain registered, nameservers on Cloudflare, DNS propagated
- Railway project provisioned with all services and Postgres reachable
- Repository public, scaffolded, with a green CI run on `main`
- `/health` returns 200 from the deployed backend; Next.js placeholder deployed
- All four coding agents configured with CodeGraph, superpowers, react-doctor
- `DESIGN.md` tokens landed in `tailwind.config.ts`
- Deploy workflow pauses for manual approval and completes on approval

**Estimated effort:** 5–8 days of focused work (34 sub-tasks).

**Sequencing note:** P0.T1.S1 and S2 (domain registration and nameserver delegation) must start **first and run in the background**. DNS propagation takes hours; everything else proceeds while it settles.

| Task | Focus | Effort | Blocks |
|---|---|---|---|
| P0.T1 | Domain & Cloudflare | L / 1–2 days (mostly waiting) | Access, Tunnel, CDN, Resend |
| P0.T2 | Railway infrastructure | M / 1 day | All deploys |
| P0.T3 | Repository scaffold | XL / 2–3 days | All code |
| P0.T4 | Agent environment | L / 1 day | All agent-driven work |
| P0.T5 | Design tokens | M / 0.5 day | Phase 3 re-skin |
| P0.T6 | CI/CD pipeline | L / 1–2 days | Every merge |

---

## Task P0.T1: Domain & Cloudflare Foundation

**Feature:** F30 · **Effort:** L / 1–2 days · **Dependencies:** none · **Risk:** Medium (external propagation delays)

Start this before anything else. Everything downstream of the domain — Access, Tunnel, CDN, Resend deliverability — is gated on nameserver propagation you don't control.

### P0.T1.S1: Register the domain

**Description:** Purchase the domain from any registrar. The registrar is irrelevant to Cloudflare's services; only nameserver delegation matters. Evaluate on renewal price rather than promotional first-year price, and confirm WHOIS privacy is included rather than upsold.

**Implementation Hints:** Hostinger, Namecheap and Porkbun are all fine. Cloudflare Registrar sells at cost but requires the zone to already be in your Cloudflare account and supports a limited TLD set — treat it as a place to transfer to after the ICANN 60-day post-registration transfer lock expires, not a starting point.

**Dependencies:** none
**Effort:** XS / 30 min
**Risk Flags:** Introductory pricing masks renewal cost at most registrars. Check the renewal figure explicitly.
**Acceptance Criteria:**
- Domain registered and visible in the registrar dashboard
- Renewal price recorded in `docs/conventions.md`
- WHOIS privacy active

### P0.T1.S2: Delegate nameservers to Cloudflare

**Description:** Add the domain as a zone in Cloudflare (free plan) and replace the registrar's nameservers with the two Cloudflare assigns. This is the step that unlocks Access, Tunnel and CDN. Propagation is typically under an hour but can take up to 24.

**Implementation Hints:** Cloudflare's onboarding scans and imports existing DNS records — verify nothing was missed before switching. Confirm activation via the zone status in the dashboard, not by guessing from `dig`.

**Dependencies:** P0.T1.S1
**Effort:** S / 30 min + propagation wait
**Risk Flags:** Until the zone shows Active, Access and Tunnel cannot be configured. Do not block other tasks on this.
**Acceptance Criteria:**
- Zone status reads "Active" in the Cloudflare dashboard
- `dig NS yourdomain.com` returns Cloudflare nameservers

### P0.T1.S3: Provision R2 bucket and API credentials

**Description:** Create the production R2 bucket for user-uploaded media (certificates, project decks, cover images, resumes, audio) and generate an S3-compatible access key pair. R2 is an account-level feature and does not require the zone, so this can proceed before S2 completes.

**Implementation Hints:** Create one bucket, e.g. `portfolio-media`. Generate an R2 API token scoped to Object Read & Write for that bucket only — not an account-wide token. Record the S3 endpoint (`https://<account-id>.r2.cloudflarestorage.com`) for the `StorageAdapter` config. Attach a custom domain (`media.yourdomain.com`) once the zone is active; this avoids the rate-limited `r2.dev` URLs and gives clean cache headers.

**Dependencies:** none (custom domain step depends on P0.T1.S2)
**Effort:** S / 1 hr
**Risk Flags:** `r2.dev` public URLs are explicitly not intended for production traffic. The custom domain is required before launch, not optional.
**Acceptance Criteria:**
- Bucket exists; a test object uploads and downloads via `aws s3 --endpoint-url`
- API token is bucket-scoped, not account-wide
- Credentials stored in Railway env vars, never in git

### P0.T1.S4: Configure Turnstile widget

**Description:** Create a Turnstile widget in Managed mode and register the allowed hostnames. Turnstile is an account-level feature independent of the zone, so it works even before nameserver delegation completes.

**Implementation Hints:** Register both the production domain and the Railway `*.up.railway.app` hostname during the interim period, plus `localhost` for development. Site key is public and belongs in frontend config; secret key is server-side only. Managed mode passes most humans invisibly.

**Dependencies:** none
**Effort:** XS / 20 min
**Risk Flags:** Hostname mismatch is the most common Turnstile failure and presents as a widget that silently never renders.
**Acceptance Criteria:**
- Widget created; site key and secret key recorded in Railway env vars
- Allowed hostnames include production domain, Railway domain, and localhost

### P0.T1.S5: Enable Cloudflare Web Analytics

**Description:** Enable Web Analytics for the site and obtain the beacon token for injection into the Next.js root layout. This is the primary crawler-visibility mechanism (gap G9).

**Implementation Hints:** The beacon is a script tag; add it to `app/layout.tsx`. Verify at setup whether the beacon works without the zone being proxied — if it requires the active zone, defer this sub-task until P0.T1.S2 completes rather than assuming.

**Dependencies:** none (possibly P0.T1.S2 — verify)
**Effort:** XS / 20 min
**Risk Flags:** Beacon-based analytics undercount when responses are served entirely from edge cache. Accept this; it is not a bug to chase.
**Acceptance Criteria:**
- Beacon token recorded
- Analytics dashboard registers a test pageview

### P0.T1.S6: Verify the Resend sending domain

**Description:** Create the Resend account and verify the domain by publishing SPF and DKIM records in Cloudflare DNS. Both use cases (admin OTP, form notifications) target your own inbox, so unverified sending would technically work — but OTP emails landing in spam is a self-inflicted lockout from your own admin portal.

**Implementation Hints:** Resend issues the exact DNS records to publish; add them as DNS-only (grey cloud) records in the Cloudflare zone. Add a DMARC record at `p=none` as well — it costs nothing and gives you visibility. Generate a sending API key and store it in Railway env vars.

**Dependencies:** P0.T1.S2
**Effort:** S / 1 hr
**Risk Flags:** Blocked until the Cloudflare zone is active. Free tier allows 3,000 emails/month and 100/day — far beyond this project's needs.
**Acceptance Criteria:**
- Resend dashboard shows the domain verified
- A test email sends and arrives in the inbox, not spam
- SPF, DKIM and DMARC records present in the zone

---

## Task P0.T2: Railway Infrastructure

**Feature:** F30 · **Effort:** M / 1 day · **Dependencies:** P0.T1.S3 · **Risk:** Low

### P0.T2.S1: Create the Railway project and Postgres instance

**Description:** Provision a Railway project with a PostgreSQL 16 database. This is the primary datastore for all content, tags, form submissions and analytics logs. Confirm the backup policy for your plan at provisioning time — if backups are not automatic, gap G12 requires a weekly `pg_dump` cron to R2.

**Implementation Hints:** Note the internal connection URL for service-to-service traffic and the public URL for local Alembic runs. Use the internal URL in the backend service to avoid egress. Per `tech-stack-analysis.md` §6.1, pgbouncer is deliberately excluded.

**Dependencies:** none
**Effort:** S / 45 min
**Risk Flags:** All site content lives here. Confirm backups before any content is authored, not after.
**Acceptance Criteria:**
- Postgres reachable from local machine via public URL with `psql`
- Backup policy documented in `docs/conventions.md`

### P0.T2.S2: Create the backend service

**Description:** Create the Railway service that runs FastAPI and serves the built admin SPA from the same origin. Deploys from the repo's `backend/Dockerfile` (multi-stage, built in P0.T3.S7).

**Implementation Hints:** Set the root directory so Railway's build context includes both `backend/` and `admin/` — the multi-stage build needs both. Wire env vars: `DATABASE_URL` (internal), `R2_*`, `RESEND_API_KEY`, `TURNSTILE_SECRET_KEY`, `SESSION_SECRET`, `ADMIN_PASSWORD_HASH`, and `CORS_ALLOW_ORIGINS` explicitly **empty** in production.

**Dependencies:** P0.T2.S1, P0.T1.S3
**Effort:** M / 2 hrs
**Risk Flags:** An empty `CORS_ALLOW_ORIGINS` in production is a deliberate security posture, not an oversight — admin and API are same-origin by construction. A permissive value surviving into production is exactly the kind of misconfiguration that never announces itself.
**Acceptance Criteria:**
- Service builds and starts
- `GET /health` returns `{"status":"ok"}` over the public Railway URL
- `CORS_ALLOW_ORIGINS` is empty in the production environment

### P0.T2.S3: Create the frontend service

**Description:** Create the Railway service running the Next.js public site, built from `frontend/Dockerfile`.

**Implementation Hints:** Requires `output: 'standalone'` in `next.config.js` for a lean container. Set `NEXT_PUBLIC_API_BASE_URL` to the backend's internal or public URL as appropriate. Railway's filesystem is ephemeral, so the ISR cache is discarded on each deploy and the first request per page regenerates — expected behaviour, not a fault.

**Dependencies:** P0.T2.S1
**Effort:** M / 2 hrs
**Risk Flags:** On-demand revalidation requires a long-lived Node server. Confirm the service runs `next start` against the standalone output rather than any static export mode.
**Acceptance Criteria:**
- Placeholder page renders over the public Railway URL
- Server-rendered HTML contains page content when fetched with `curl` (no JS execution)

### P0.T2.S4: Create the cron service

**Description:** Create a Railway cron service running every 5 minutes to execute scheduled publishing (gap G3): find content whose `publish_at` has passed while `status = 'scheduled'`, flip to `published`, and call the Next.js revalidation webhook.

**Implementation Hints:** Reuse the backend image with a different start command, e.g. `uv run python -m app.jobs.scheduler`. In P0 this is a stub that logs and exits cleanly; the real logic lands in Phase 1 with the publishing workflow. Rejected alternative: in-process APScheduler, which loses its schedule on every container restart, and Railway restarts containers on deploy.

**Dependencies:** P0.T2.S2
**Effort:** S / 1 hr
**Risk Flags:** If this is never wired up, scheduled posts silently fail to appear — the data is correct and only the cache is stale, which makes it expensive to diagnose.
**Acceptance Criteria:**
- Cron service runs on schedule and exits 0
- Execution visible in Railway logs

### P0.T2.S5: Create the Cloudflare Tunnel service

**Description:** Run `cloudflared` as a Railway service so the admin hostname is reachable without exposing a public inbound port on the origin.

**Implementation Hints:** Create a named tunnel in the Cloudflare Zero Trust dashboard, store the tunnel token as a Railway env var, and run `cloudflared tunnel run` with it. Route the tunnel's public hostname to the backend service's internal address. Per `tech-stack-analysis.md` §6.2, admin SPA and admin API share **one hostname** — the tunnel wraps a single origin.

**Dependencies:** P0.T1.S2, P0.T2.S2
**Effort:** M / 2 hrs
**Risk Flags:** Blocked until the Cloudflare zone is active. Quick tunnels (`trycloudflare.com`) are ephemeral and unsuitable — use a named tunnel.
**Acceptance Criteria:**
- `admin.yourdomain.com` resolves through the tunnel to the backend
- Backend is not reachable on that hostname when the tunnel is stopped

### P0.T2.S6: Configure Cloudflare Access (env-gated)

**Description:** Create an Access application covering `admin.yourdomain.com` with email OTP as the identity method, and add yourself as the only allowed identity.

**Implementation Hints:** Access injects a `Cf-Access-Jwt-Assertion` header; the backend verifies it against the team JWKS at `https://<team>.cloudflareaccess.com/cdn-cgi/access/certs` using `PyJWT`. Build that verification behind an env flag (`CF_ACCESS_ENABLED`) so the app-layer auth can carry the interim if Access is unavailable, per the decision recorded in brainstorming. Free tier covers up to 50 users.

**Dependencies:** P0.T2.S5
**Effort:** M / 2 hrs
**Risk Flags:** A single Access application must cover both the SPA and `/api/*` on the same hostname. Splitting them across subdomains causes CORS preflights to be redirected to the login page and fail — a failure that presents as a CORS misconfiguration and wastes hours.
**Acceptance Criteria:**
- Visiting `admin.yourdomain.com` prompts for Access authentication
- Backend rejects requests lacking a valid `Cf-Access-Jwt-Assertion` when `CF_ACCESS_ENABLED=true`
- Setting `CF_ACCESS_ENABLED=false` restores app-layer-only auth

### P0.T2.S7: Disable Railway's GitHub auto-deploy

**Description:** Turn off Railway's own GitHub integration triggers so deploys happen exclusively through the approved GitHub Actions workflow.

**Implementation Hints:** Disconnect the GitHub repo from each service, or disable automatic deploys in service settings. Generate a `RAILWAY_TOKEN` for CLI-driven deploys and store it as a **GitHub environment secret** scoped to `production`, not a repository secret.

**Dependencies:** P0.T2.S2, P0.T2.S3, P0.T2.S4
**Effort:** XS / 30 min
**Risk Flags:** Leaving auto-deploy on produces two racing deploys per merge and defeats the manual approval gate entirely.
**Acceptance Criteria:**
- Pushing to `main` does not trigger a Railway deploy on its own
- `railway up --service backend` succeeds locally with the token

---

## Task P0.T3: Repository Scaffold

**Feature:** F1 · **Effort:** XL / 2–3 days · **Dependencies:** none · **Risk:** Medium

### P0.T3.S1: Initialise the public repository

**Description:** Create the public GitHub repo with the hygiene that a public repo demands from commit one. Secrets live only in Railway and GitHub environment secrets; no content, fixtures or database dumps enter git.

**Implementation Hints:** `.gitignore` must cover `.env`, `.env.local`, `.codegraph/`, `__pycache__/`, `node_modules/`, `.next/`, `dist/`, `*.db`, `*.sql`. Enable **secret scanning** and **push protection** in repo settings. Add `.gitattributes` for line-ending normalisation.

**Dependencies:** none
**Effort:** S / 1 hr
**Risk Flags:** Your "work views" blogs are explicitly private content and must exist only in the database. A seed fixture containing real content published to a public repo is unrecoverable.
**Acceptance Criteria:**
- Repo is public with secret scanning and push protection enabled
- A test commit containing a fake API key is blocked by push protection

### P0.T3.S2: Scaffold the backend with uv and the app factory

**Description:** Create the FastAPI backend using uv, structured feature-sliced per the decision in brainstorming. Establish the app factory pattern and the `core/` module that every feature slice will import from.

**Implementation Hints:**
```
backend/
├── pyproject.toml, uv.lock, .env.example
├── alembic/, alembic.ini
└── app/
    ├── app.py            # create_app() -> FastAPI
    ├── core/             # config.py, database.py, storage.py, security.py, deps.py
    ├── features/         # one directory per feature; empty in P0
    └── tests/
```
`uv init`, then `uv add fastapi uvicorn sqlalchemy asyncpg alembic pydantic-settings python-multipart argon2-cffi pyjwt itsdangerous slowapi resend boto3`. Dev group: `uv add --dev pytest pytest-asyncio httpx ruff mypy`. Config via `pydantic-settings` reading env vars. Run with `uv run uvicorn app.app:create_app --factory --reload`.

**Dependencies:** P0.T3.S1
**Effort:** L / 1 day
**Risk Flags:** `core/` is imported by every feature slice. Getting its interfaces wrong is the one change that ripples across all of Phase 2.
**Acceptance Criteria:**
- `uv run uvicorn app.app:create_app --factory` starts locally
- `GET /health` returns 200
- `uv run ruff check` and `uv run mypy app` both pass on the skeleton

### P0.T3.S3: Configure async Alembic

**Description:** Wire Alembic for async SQLAlchemy over asyncpg. Alembic's default `env.py` template is synchronous and fails against an async engine — this must be corrected here, because every migration in every later phase inherits this configuration.

**Implementation Hints:** In `alembic/env.py`, use `async_engine_from_config` and run migrations via `connection.run_sync(context.run_migrations)` inside an async `run_migrations_online()` driven by `asyncio.run()`. Point `target_metadata` at the declarative `Base`. Feature-sliced models must be imported somewhere Alembic can see them — use an `app/core/models_registry.py` that imports every feature's models, so autogenerate doesn't silently miss tables. Set `compare_type=True` so column type changes are detected.

**Dependencies:** P0.T3.S2, P0.T2.S1
**Effort:** M / 4 hrs
**Risk Flags:** The classic failure is autogenerate producing an empty migration because feature models were never imported. The registry module prevents it. This is also the file that gap G3's migration-head CI check depends on.
**Acceptance Criteria:**
- `uv run alembic upgrade head` succeeds against local Docker Postgres
- `uv run alembic revision --autogenerate -m "test"` produces a non-empty migration for a scratch model
- `uv run alembic heads` returns exactly one head

### P0.T3.S4: Implement the StorageAdapter

**Description:** Build the abstraction over object storage so R2, MinIO and local disk are a config change rather than a refactor (gap in `dependency-map.md` §7). Content-hashed keys make cached media immune to staleness.

**Implementation Hints:** Abstract base in `app/core/storage.py` with `put(key, data, content_type)`, `get_url(key)`, `delete(key)`, `exists(key)`. One `S3Storage` implementation via `boto3` with a configurable endpoint URL serves both R2 and MinIO — same API, different endpoint. Keys must embed a content hash (`certs/aws-sa-{sha256[:12]}.pdf`) so replacing a file changes its URL and the edge cache can never serve a stale version. Set `Cache-Control: public, max-age=31536000, immutable` on upload.

**Dependencies:** P0.T3.S2, P0.T1.S3
**Effort:** M / 4 hrs
**Risk Flags:** Scattering direct boto3 calls through feature slices is the failure mode this task exists to prevent. Nothing outside `core/storage.py` should import boto3.
**Acceptance Criteria:**
- Uploading against local MinIO and against R2 both succeed with only an env change
- Uploaded objects carry the immutable cache header
- Replacing content produces a different key

### P0.T3.S5: Scaffold the Next.js frontend with the overlay invariant

**Description:** Create the Next.js App Router application. Establish the composition pattern that the intro sequence and category selector will later depend on — and which, if wrong, produces an SEO regression that no later task will catch.

**Implementation Hints:** `npx create-next-app@latest frontend --typescript --tailwind --app`. Set `output: 'standalone'` and add the R2 custom domain to `images.remotePatterns`. Add `react-markdown`, `remark-gfm`, `rehype-sanitize`, `framer-motion`. Initialise shadcn/ui.

**The invariant, and it belongs in `docs/conventions.md` as a stated rule:** the homepage must render the full default overview in server HTML, with the intro and selector composed as **overlays above it** — never as `showIntro ? <Intro/> : <Overview/>`. That conditional would serve crawlers an animation instead of a portfolio and would silently undo the entire rationale for choosing Next.js.

Category state lives in a **cookie**, not `localStorage`, because the server must read it to render the right variant (assumption A6).

**Dependencies:** P0.T3.S1
**Effort:** L / 1 day
**Risk Flags:** This invariant is the single highest-consequence architectural detail in the frontend, and it is invisible in normal browser testing — the site looks correct either way. Verify with `curl`, not with eyes.
**Acceptance Criteria:**
- `curl` against `/` returns HTML containing page content, with no JS execution
- `next build` produces standalone output
- Category cookie is readable in a server component

### P0.T3.S6: Scaffold the admin SPA

**Description:** Create the Vite + React + TypeScript admin application. Deliberately not Next.js — there is no SEO requirement, no SSR benefit, and Vite builds faster.

**Implementation Hints:** `npm create vite@latest admin -- --template react-ts`. Add React Router, TanStack Query, shadcn/ui consuming the same tokens. Configure the dev server to proxy `/api` to `localhost:8000` so development matches production's same-origin arrangement as closely as possible. Build output goes to `admin/dist`.

**Dependencies:** P0.T3.S1
**Effort:** M / 4 hrs
**Risk Flags:** Development is cross-origin while production is same-origin — the one deliberate divergence in the stack. `CORS_ALLOW_ORIGINS` handles it and must be empty in production.
**Acceptance Criteria:**
- `npm run dev` serves the admin shell and proxies API calls to the backend
- `npm run build` emits to `admin/dist`

### P0.T3.S7: Write the multi-stage Dockerfile

**Description:** Build the admin SPA in a Node stage and copy its output into the Python stage, so FastAPI serves both the API and the admin UI from one container on one origin.

**Implementation Hints:** Stage 1: `node:20-alpine`, copy `admin/`, `npm ci && npm run build`. Stage 2: `python:3.12-slim`, install uv, `uv sync --frozen`, `COPY --from=0 /admin/dist ./static`. In `create_app()`, register all API routers **first**, then mount `StaticFiles(directory="static", html=True)` at `/` **last** — mount order determines precedence, and mounting static first would shadow every API route. Add a catch-all returning `index.html` for unmatched non-`/api` paths so client-side routing works on refresh.

**Dependencies:** P0.T3.S2, P0.T3.S6
**Effort:** M / 4 hrs
**Risk Flags:** Mount ordering is the trap — static mounted before routers produces 404s on every endpoint with no obvious cause. Note the accepted coupling: any admin change now rebuilds and redeploys the API.
**Acceptance Criteria:**
- `docker build` succeeds from the repo root
- Container serves the admin UI at `/` and the API at `/api/v1/health`
- Refreshing a deep admin route returns the SPA, not a 404

### P0.T3.S8: Docker Compose for local development

**Description:** Provide Postgres and MinIO locally so development matches production storage semantics via the same S3 API.

**Implementation Hints:** `docker-compose.yml` at repo root with `postgres:16-alpine` (named volume for persistence) and `minio/minio` with its console. Add a `createbuckets` init container that runs `mc mb` so the bucket exists on first boot rather than failing on first upload.

**Dependencies:** P0.T3.S1
**Effort:** S / 2 hrs
**Risk Flags:** Without the bucket-creation step, the first local upload fails confusingly.
**Acceptance Criteria:**
- `docker compose up -d` brings up both services
- Backend connects to Postgres and uploads to MinIO with `.env` values from `.env.example`

---

## Task P0.T4: Agent Environment

**Feature:** F0 · **Effort:** L / 1 day · **Dependencies:** P0.T3.S1 · **Risk:** Low

### P0.T4.S1: Author the canonical docs set

**Description:** Place the three planning documents plus a conventions file in `docs/`, as the single source of truth that all four agents reference. Duplicating project context per agent guarantees drift and agents that disagree about your own architecture.

**Implementation Hints:** `docs/tech-stack-analysis.md`, `docs/dependency-map.md`, `docs/development-plan.md`, `docs/conventions.md`. Conventions must state the non-obvious invariants explicitly: overlay-not-replacement (P0.T3.S5); cookie-not-localStorage for category state; feature-sliced backend with no cross-feature imports; `core/` is the only shared surface; migrations regenerated after rebase; nothing but `core/storage.py` imports boto3.

**Dependencies:** P0.T3.S1
**Effort:** M / 3 hrs
**Risk Flags:** These invariants are the ones an agent will violate plausibly and undetectably. If they aren't written down, they aren't real.
**Acceptance Criteria:**
- All four documents present in `docs/`
- `conventions.md` states every invariant listed above

### P0.T4.S2: Write thin agent pointer files

**Description:** Create `CLAUDE.md`, `AGENTS.md` and `.cursor/rules/` as short pointers into `docs/`, authored to tolerate tool-injected content.

**Implementation Hints:** Each file: a one-paragraph project summary, a pointer to `docs/`, and the three or four invariants an agent must never violate. Keep them short — long instruction files get skimmed. **Both CodeGraph and react-doctor write marker-fenced sections into `CLAUDE.md` and `AGENTS.md` during their installers**, so treat these as files with managed regions rather than hand-maintained prose, and don't hand-edit inside the markers.

**Dependencies:** P0.T4.S1
**Effort:** S / 2 hrs
**Risk Flags:** Hand-editing inside tool-managed marker fences means the next installer run silently discards your changes.
**Acceptance Criteria:**
- All three pointer configurations exist and reference `docs/`
- Running the CodeGraph installer does not destroy hand-written content

### P0.T4.S3: Install and index CodeGraph

**Description:** Install the CodeGraph CLI, wire it into all four agents, and build the project index. It gives agents pre-indexed symbol, call-graph and blast-radius queries instead of grep-and-read crawls.

**Implementation Hints:** `curl -fsSL https://raw.githubusercontent.com/colbymchenry/codegraph/main/install.sh | sh` (or `npm i -g @colbymchenry/codegraph`), open a **new terminal**, then `codegraph install` — it auto-detects Claude Code, Cursor, Codex CLI and opencode. Then `codegraph init` at the repo root. Auto-sync is on by default via native OS file events; there is no manual sync step. Add `.codegraph/` to `.gitignore`. Optionally `codegraph telemetry off`.

**Dependencies:** P0.T3.S1
**Effort:** S / 1 hr
**Risk Flags:** FastAPI routes are recognised (measured ~98%), but **Next.js App Router routing is not in CodeGraph's supported-framework list** — symbol and call-graph indexing of `.tsx` still works, you simply won't get route nodes for the public frontend. If you develop under WSL2 with the repo on a Windows drive (`/mnt/c`), expect SQLite locking problems; keep the project on the Linux-native filesystem.
**Acceptance Criteria:**
- `codegraph status` reports a populated index
- All four agents list a `codegraph_explore` tool
- `.codegraph/` is gitignored

### P0.T4.S4: Install superpowers skills

**Description:** Install the obra/superpowers skill set so agents follow disciplined workflows — brainstorming before building, TDD, systematic debugging, verification before completion.

**Implementation Hints:** Install per the repository's own instructions at `github.com/obra/superpowers`. The rigid skills (test-driven-development, systematic-debugging, verification-before-completion) matter most in Phase 2, where six parallel tracks make undisciplined work expensive to unpick. Note that `brainstorming` carries a hard gate against writing code before design approval — intended, and it will fire.

**Dependencies:** P0.T3.S1
**Effort:** S / 1 hr
**Risk Flags:** Skills that instruct agents to pause for approval will interrupt otherwise-autonomous runs. That is the point, but expect it.
**Acceptance Criteria:**
- Skills discoverable by at least Claude Code and one other agent
- Invoking the TDD skill produces its RED-GREEN-REFACTOR workflow

### P0.T4.S5: Install react-doctor and capture a baseline

**Description:** Install react-doctor's agent skill and run a first audit to establish a baseline before any real frontend code exists — so the CI diff-scoped mode has a clean starting point.

**Implementation Hints:** `npx react-doctor@latest` for the audit, then `npx react-doctor@latest install` to wire the skill into all four agents. Configure rules in `doctor.config.ts`. It covers state and effects, performance, architecture, security and accessibility across both Next.js and Vite, so it serves `frontend/` and `admin/` alike. Telemetry goes to Sentry by default; `--no-telemetry` opts out.

**Dependencies:** P0.T3.S5, P0.T3.S6
**Effort:** S / 1 hr
**Risk Flags:** React-only. The FastAPI backend has no coverage from it — ruff and mypy (P0.T6.S1) close that gap.
**Acceptance Criteria:**
- Audit runs and reports against both frontend apps
- Skill installed for all four agents
- Baseline report committed to `docs/`

### P0.T4.S6: Configure Stitch MCP with env var expansion

**Description:** Wire the Stitch MCP server into the project so design generation is available from the coding agents — without committing an API key to a public repository.

**Implementation Hints:** Obtain a Stitch API key. Commit `.mcp.json` referencing `${STITCH_API_KEY}` rather than the literal value, and keep the real key in your shell profile or a gitignored `.env`. Sources disagree on the exact server invocation — some show `@google/stitch-mcp`, others `@_davideast/stitch-mcp proxy`, others a direct HTTP transport to `stitch.googleapis.com/mcp` with an `X-Goog-Api-Key` header. **Follow the official setup page** (`stitch.withgoogle.com/docs/mcp/setup`) and treat the others as fallbacks. MCP servers load at session start, so restart the agent after any config change. Free, billed against your standard Stitch generation quota.

**Dependencies:** P0.T3.S1
**Effort:** M / 2 hrs
**Risk Flags:** A literal API key in a committed `.mcp.json` on a public repo will be scraped quickly. Env var expansion is the whole point of this sub-task. There is also a gcloud OAuth path, but tokens expire hourly — not worth it here.
**Acceptance Criteria:**
- `.mcp.json` is committed and contains no secret
- Agent lists Stitch tools after restart
- `git log -p .mcp.json` shows no key was ever committed

### P0.T4.S7: Install the Railway CLI

**Description:** Install and authenticate the Railway CLI for local deploys and for the GitHub Actions deploy job.

**Implementation Hints:** Install per Railway's docs, `railway login`, `railway link` to the project. Generate a project token for CI and store it as a GitHub **environment** secret scoped to `production` — not a repository secret, which every workflow can read.

**Dependencies:** P0.T2.S1
**Effort:** XS / 30 min
**Acceptance Criteria:**
- `railway status` shows the linked project
- `railway up --service backend` deploys successfully

---

## Task P0.T5: Design Tokens

**Feature:** F8 · **Effort:** M / 0.5 day · **Dependencies:** P0.T4.S6 · **Risk:** Low

### P0.T5.S1: Generate the first design pass and export DESIGN.md

**Description:** Generate an initial design in Stitch and export its `DESIGN.md` — a portable markdown description of the design system (colour tokens, typography scale, spacing, component rules) readable by both humans and AI agents. This is the artifact worth importing, not the HTML export, which would need refactoring into components and redoing whenever the design changes.

**Implementation Hints:** Generate a dark-themed pass covering the tile grid and one content page — enough to fix tokens without committing to layouts you'll revisit in Phase 3. Dark theme only, single palette: a light mode you don't want doubles the token surface for no benefit. Store the export at `docs/DESIGN.md` so agents read it alongside the conventions.

**Dependencies:** P0.T4.S6
**Effort:** M / 3 hrs
**Risk Flags:** Resist importing Stitch's HTML. The full design pass is deliberately deferred to Phase 3, and code imported now would be discarded then.
**Acceptance Criteria:**
- `docs/DESIGN.md` present with colour, typography and spacing tokens
- Dark palette only

### P0.T5.S2: Map tokens into Tailwind and shadcn

**Description:** Translate `DESIGN.md` tokens into `tailwind.config.ts` and the shadcn CSS variables in both `frontend/` and `admin/`, so every component built in Phases 1 and 2 consumes tokens rather than literal values. This indirection is what makes the Phase 3 re-skin a token swap instead of a rewrite.

**Implementation Hints:** Define tokens as CSS custom properties in `globals.css`, reference them from `tailwind.config.ts` `theme.extend`. shadcn reads `--background`, `--foreground`, `--primary` and friends — map Stitch's palette onto those names rather than inventing parallel ones. Add a lint rule or review convention forbidding hardcoded hex values in component code.

**Dependencies:** P0.T5.S1, P0.T3.S5, P0.T3.S6
**Effort:** M / 3 hrs
**Risk Flags:** Any hardcoded colour that slips into a component in Phase 2 becomes a manual fix during the Phase 3 re-skin. Catch these at review.
**Acceptance Criteria:**
- Both apps render shadcn components in the dark palette
- No hardcoded colour literals in either app
- Changing one token value visibly changes both apps

---

## Task P0.T6: CI/CD Pipeline

**Feature:** F1 · **Effort:** L / 1–2 days · **Dependencies:** P0.T3.*, P0.T4.* · **Risk:** Medium

### P0.T6.S1: Lint and typecheck workflow

**Description:** Run ruff, mypy, ESLint and `tsc --noEmit` on every push. ruff and mypy close the backend quality gap that react-doctor cannot cover.

**Implementation Hints:** `.github/workflows/quality.yml` on `push` and `pull_request`. Backend: `uv run ruff check`, `uv run ruff format --check`, `uv run mypy app`. Frontend and admin: `npm run lint`, `npx tsc --noEmit`. Configure ruff and mypy in `backend/pyproject.toml`. Start mypy non-strict and tighten — enabling strict mode against an empty codebase is free, so do it now rather than retrofitting.

**Dependencies:** P0.T3.S2, P0.T3.S5, P0.T3.S6
**Effort:** M / 3 hrs
**Acceptance Criteria:**
- All four checks run on push and fail the build on violations
- Green on the P0 scaffold

### P0.T6.S2: Unit tests with codegraph-scoped selection

**Description:** Run backend and frontend unit tests, using `codegraph affected` to run only tests reachable from changed files.

**Implementation Hints:** `git diff --name-only origin/main...HEAD | codegraph affected --stdin --quiet` yields affected test files; feed them to Vitest. Requires `codegraph init` in CI (or a committed index, which is not recommended — keep `.codegraph/` gitignored and index in the workflow). **Always run the full suite on `main`** — scoped selection is a PR-speed optimisation, and trusting it as the only gate on the default branch would let a missed edge slip through.

**Dependencies:** P0.T6.S1, P0.T4.S3
**Effort:** M / 4 hrs
**Risk Flags:** Import-graph reachability is not the same as behavioural coverage — a config or fixture change can affect tests it doesn't import. The full-suite-on-main rule is the safety net.
**Acceptance Criteria:**
- PR runs execute only affected tests; `main` runs the full suite
- Backend tests run against a Postgres service container

### P0.T6.S3: OpenAPI drift check

**Description:** Fail the build when generated TypeScript types diverge from the FastAPI schema (gap G7). Contract drift is otherwise silent until runtime.

**Implementation Hints:** Start the backend, run `npm run openapi:generate` in both `frontend/` and `admin/` (the pattern already proven in your jobs-tracker repo), then `git diff --exit-code` on the generated files. A non-zero exit means someone changed an endpoint without regenerating types.

**Dependencies:** P0.T6.S1
**Effort:** M / 3 hrs
**Acceptance Criteria:**
- Changing a Pydantic schema without regenerating types fails CI
- Regenerating and committing makes it pass

### P0.T6.S4: Alembic single-head check

**Description:** Fail the build if the migration chain has more than one head. In Phase 2, six parallel branches each autogenerate a migration whose `down_revision` points at the same head; merging produces multiple heads and `alembic upgrade head` then fails outright. This is not a hypothetical — it will happen.

**Implementation Hints:** Run `uv run alembic heads` and assert exactly one line of output. Document the resolution in `docs/conventions.md`: rebase on `main` and **regenerate** the migration before opening a PR; use `alembic merge` for anything that slips through.

**Dependencies:** P0.T3.S3
**Effort:** S / 2 hrs
**Risk Flags:** The highest-probability recurring failure in Phase 2. Catching it in CI is far cheaper than discovering it on a deploy.
**Acceptance Criteria:**
- Two migrations sharing a `down_revision` fail the build
- Error message names the offending revisions

### P0.T6.S5: react-doctor PR gate

**Description:** Add react-doctor's CI workflow, which scans pull requests and reports **only issues the change introduced**, not the existing backlog.

**Implementation Hints:** `npx react-doctor@latest ci install` scaffolds the workflow and PR summary comments. Tune gate severity and scan scope with `react-doctor ci config`. Because it reports diff-scoped findings, it won't drown you on day one.

**Dependencies:** P0.T4.S5
**Effort:** S / 1 hr
**Acceptance Criteria:**
- PRs receive a react-doctor summary comment
- A deliberately bad component (array index as key) is flagged

### P0.T6.S6: Playwright E2E workflow

**Description:** Run end-to-end tests on PRs to `main` and on `main` only. Full-stack E2E needs Postgres, a built Next app and a running API; running it on every commit would make iteration miserable.

**Implementation Hints:** Postgres via a service container, MinIO or the local-disk StorageAdapter for media. Build both apps, start the backend, run Playwright. In P0 this covers only the health check and placeholder render — the real journeys (intro → select → overview, and admin login) land in later phases.

**Dependencies:** P0.T6.S2, P0.T3.S7
**Effort:** L / 1 day
**Risk Flags:** E2E is where CI time goes. Keep it off the per-commit path.
**Acceptance Criteria:**
- Workflow triggers only on PRs to `main` and pushes to `main`
- Placeholder journey passes

### P0.T6.S7: Deploy workflow with manual approval

**Description:** Deploy to Railway after all checks pass, gated behind a GitHub environment requiring your approval. Environment protection rules are free on public repositories — an accidental benefit of that choice.

**Implementation Hints:** Create a `production` environment with yourself as a required reviewer and a deployment branch rule limiting it to `main`. The deploy job declares `environment: production`, so it pauses and waits. Store `RAILWAY_TOKEN` as an **environment** secret, reachable only after approval. Deploy each service explicitly with `railway up --service <name>`. Leave "prevent self-review" **off** — you're the only maintainer and enabling it would deadlock you. Pending approvals expire after 30 days.

**Use plain `pull_request` triggers, never `pull_request_target` with a checkout of PR code.** On a public repo that is the standard remote-code-execution path: a fork's pull request runs with your secrets.

**Dependencies:** P0.T2.S7, P0.T6.S6
**Effort:** M / 4 hrs
**Risk Flags:** The `pull_request_target` misconfiguration is the single most dangerous thing that can be added to a public repo's CI. Railway auto-deploy must already be disabled or the gate is meaningless.
**Acceptance Criteria:**
- Merging to `main` pauses the deploy job pending approval
- Approving deploys all three services; rejecting deploys none
- `RAILWAY_TOKEN` is unreadable by non-production jobs

---

## Phase 0 Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| DNS propagation delays Access/Tunnel/Resend | High | Low | Start P0.T1.S1–S2 first; everything else proceeds in parallel |
| Async Alembic misconfigured; autogenerate silently empty | Medium | High | Explicit models registry (P0.T3.S3); verified by acceptance criteria |
| Static files mounted before API routers | Medium | Medium | Mount order stated in P0.T3.S7; caught by acceptance test |
| Overlay-not-replacement violated in frontend composition | Medium | **Critical** | Stated invariant in `conventions.md`; verified by `curl`, not by eye |
| API key committed to public repo | Low | **Critical** | Push protection, secret scanning, env var expansion in `.mcp.json` |
| `pull_request_target` used in a workflow | Low | **Critical** | Explicitly prohibited in `conventions.md` |
| Cloudflare Access split across subdomains breaks CORS | Medium | High | Single-hostname architecture fixed at P0.T2.S5/S6 |
| Hardcoded colours bypass the token layer | High | Medium | Review convention; makes Phase 3 re-skin manual where violated |

---

## Exit Checklist

- [ ] Domain active on Cloudflare; Resend verified with SPF/DKIM/DMARC
- [ ] R2 bucket with custom domain; MinIO running locally
- [ ] Railway: backend, frontend, cron, tunnel, Postgres — all healthy
- [ ] `GET /health` returns 200 from the deployed backend
- [ ] `curl` on the deployed frontend returns content-bearing HTML
- [ ] Repo public; push protection and secret scanning on; no secrets in history
- [ ] `alembic upgrade head` succeeds; `alembic heads` returns one head
- [ ] All four agents configured with CodeGraph, superpowers, react-doctor
- [ ] `.mcp.json` committed with env var expansion, no key
- [ ] `docs/` complete, including `conventions.md` with every invariant
- [ ] `DESIGN.md` tokens live in both Tailwind configs; no hardcoded colours
- [ ] Full CI pipeline green on `main`
- [ ] Deploy workflow pauses for approval and completes on approval
