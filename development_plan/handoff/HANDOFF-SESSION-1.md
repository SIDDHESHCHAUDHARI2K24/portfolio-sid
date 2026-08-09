# HANDOFF — Session 1 (P0 foundations + P1 backend spine through TD-19)

**Written:** end of session 1 · **Next session:** continue with the remaining P1 To-Dos (TD-20 → TD-23), then P0 CI/infra leftovers, then P2/P3.
**Start here:** read this file, then `development_plan/todos/README.md` (master index), then the specific To-Do cards you are executing. All cards live in `development_plan/todos/<phase>/`.

---

## 1. Snapshot

- **Repo:** `github.com/SIDDHESHCHAUDHARI2K24/portfolio-sid` (public). Local: `/Users/siddheshc2001gmail.com/Coding Projects/Portfolio`, branch `main`.
- **Commits (oldest → newest):**
  1. `a0a89d2` repo hygiene — gitignore, gitattributes, planning docs, todo cards
  2. `65d9f4a` wave 0-1 — agent tooling, docs/conventions, backend/frontend/admin scaffolds, docker compose
  3. `48f14d5` wave 2 — async alembic, StorageAdapter, multi-stage backend image
  4. `65aaef7` P1 core — data foundations, admin auth, publishing/revalidation
  5. `9809b44` refactor — feature-based backend layout
  6. `b8acd40` P1 relevance engine (TD-18)
- **Backend tests:** 74 passing (`cd backend && uv run pytest -q`). ruff check/format clean, mypy strict clean (49 files).
- **Alembic chain (single head `cf9af7fc8db5`):** `base → d902650351c6` (core foundations: enums, topic_tags) `→ fb100e58ff80` (auth: otp_challenges, login_attempts) `→ cf9af7fc8db5` (relevance: audience_tag_map + seeds).
- **Local services:** `docker compose up -d` gives Postgres 16.14 (:5432, portfolio/portfolio/portfolio) + MinIO (:9000/:9001, minioadmin) + bucket `portfolio-media` auto-created. Test DB `portfolio_test` is auto-created by `backend/app/conftest.py`.
- **Key versions:** Next.js 16.3 (React 19.2), Vite 8 + TS 6 + oxlint, FastAPI 0.141, SQLAlchemy 2.0.51, Pydantic 2.13, shadcn CLI v4 (flag changes — see §5), Tailwind v4, uv 0.11, Python 3.13 local / target >=3.12.

## 2. What was developed (done To-Dos)

### P0 (agent-executable parts)
| To-Do | State | Evidence |
|---|---|---|
| TD-00 repo init | DONE | gitignore (incl. `opencode.json`, `.env*`), gitattributes, secrets never committed |
| TD-01 agent tooling | DONE | caveman (project + global), graphify `--project` for opencode/claude/codex, codegraph init (index built) + telemetry off, superpowers enabled in Claude Code + opencode. **blackbox-cli intentionally NOT installed (user decision).** |
| TD-02 docs + conventions | DONE | `docs/` full set; `docs/conventions.md` holds all 15 invariants + contention protocol |
| TD-03 backend scaffold | DONE | `create_app()` factory, `/health` + `/api/v1/health`, Settings (pydantic-settings), async engine/session, ruff+mypy strict config |
| TD-04 Next.js scaffold | DONE | standalone output, `NEXT_PUBLIC_INDEXABLE=false` → noindex robots (invariant 13), `scripts/check_ssr.sh`, static `/` verified via curl |
| TD-05 admin scaffold | DONE | Vite react-ts, React Router, TanStack Query, Tailwind v4, shadcn, `/api`→:8000 proxy, builds to `admin/dist` |
| TD-06 docker compose | DONE | postgres+minio+createbuckets, verified healthy |
| TD-07 async Alembic | DONE | async `env.py` (`run_sync`), registry import, `compare_type=True`; scratch-model autogenerate proven non-empty then cleaned |
| TD-08 StorageAdapter | DONE | `S3Storage` (R2/MinIO via endpoint) + `LocalDiskStorage`, content-hashed keys, immutable Cache-Control verified live, boto3-isolation test |
| TD-09 backend Dockerfile | DONE | node stage builds admin → python stage serves API + SPA; routers-first, catch-all SPA fallback; curl matrix passed |

### P1 (backend spine)
| To-Do | State | Evidence |
|---|---|---|
| TD-16 core data | DONE | UUID/Timestamp/Sortable/Publishable mixins, `Audience` + `PublishStatus` enums (+`DEFAULT_AUDIENCE` sentinel NOT in DB enum), `TopicTag`, `public_filter`, migration |
| TD-17 admin auth | DONE | Argon2id, 6-digit OTP (SHA-256 + compare_digest, 5min/5 attempts), itsdangerous session cookie, slowapi + DB-backed lockout (10/15min), CF Access JWT (env-gated, JWKS cached), `hash-password` CLI |
| TD-18 relevance | DONE | `AudienceTagMap` + seeded migration (10 tags, 14 rows), pure `is_relevant` resolver, public map endpoint + admin matrix GET/PUT with revalidation |
| TD-19 publishing | DONE | `/api/revalidate` route (timing-safe), `core/revalidation.py` (after-commit, log-not-raise), `app/jobs/scheduler.py` (registry-driven, idempotent), shared cache-tag constants (backend `core/cache_tags.py` ↔ frontend `lib/cacheTags.ts`), leak-guard test helper |

## 3. Feature-based structure (ENFORCED — conventions invariant 5)

Backend layout every feature MUST follow (reference implementation: `app/features/auth/` and `app/features/relevance/`):

```
backend/app/features/<name>/
├── endpoints/          # APIRouter modules (public_router + admin_router)
├── tests/              # feature tests (global fixtures come from app/conftest.py)
├── models.py           # ORM models (each feature owns its models)
├── schemas.py          # Pydantic schemas (each feature owns its schemas)
├── repository.py       # queries — NEVER imports FastAPI
├── service.py          # orchestration, revalidation triggers
└── utils.py            # feature-local helpers (create when needed)
```

- Global test fixtures live in `backend/app/conftest.py` (applies to all tests under `app/`); shared test constants/helpers in `app/tests/helpers.py` (`TEST_ADMIN_PASSWORD`, `TestPublishable`, `assert_public_query_excludes_drafts`). `pyproject.toml` has `testpaths = ["app"]`.
- Register models in `app/core/models_registry.py` (append-only alphabetical zone) and routers in `app/app.py::register_routers` (append zone). Forgotten registry line = silently empty migration.
- Frontend/admin mirror this when built: `frontend/features/<name>/` (components/hooks/lib) with thin `app/` routes; `admin/src/features/<name>/` + shared field components in `admin/src/components/fields/`.

## 4. REMAINING P1 — continue here next session

Execute in this order (migration serialization matters — see §8):

1. **TD-20 Timeline backend slice** (`p1/TD-20-timeline-backend.md`) — `app/features/timeline/` full slice: `TimelineEntry` model (mixins + kind EDUCATION/EXPERIENCE, nullable `end_date`=current, M2M `TopicTag` via `timeline_topic_tags`, index `start_date DESC`), schemas (Public omits status/publish_at/overrides; Admin full; Create/Update with `end_date >= start_date` validator), repository (`list_public` applies `public_filter`, `selectinload` tags, constant query count — assert it), service (revalidation after mutations), routers (`/api/v1/timeline` public read-only; `/api/v1/admin/timeline` router-level `admin_auth`), register model + `register_publishable(TimelineEntry, CACHE_TAGS.timeline)`, migration. Apply `assert_public_query_excludes_drafts`.
2. **TD-21 Frontend shell + typegen** (`p1/TD-21-frontend-shell-typegen.md`) — backend exports committed `openapi.json`; `openapi-typescript` into `frontend/` AND `admin/`; category cookie `portfolio_category` (1yr, Lax, NOT HttpOnly) + `CategoryProvider`; `?for=` override; **never call `cookies()` in content RSCs** + `next build` static assertion; `lib/relevance.ts` mirrors `is_relevant` exactly + shared parity fixture; `lib/api.ts` fetch wrapper with tags from `lib/cacheTags.ts`.
3. **TD-22 Timeline public + tile contract** (`p1/TD-22-timeline-public-tile.md`) — timeline page (RSC + client relevance), filter chips (OR semantics, canonical bare), `OverviewIntro` (6 seeded rows incl. default), `Tile` interface + contract documented with worked example, HUD. Verify with `curl`, not eyes (overlay invariant).
4. **TD-23 Admin shell + Timeline CRUD** (`p1/TD-23-admin-shell-crud.md`) — login flow, auth guard via `/api/v1/admin/me`, Timeline CRUD, **extract shared field components** (`TagSelect`, `AudienceOverrideSelect`, `PublishStatusField`, `MarkdownField` → `admin/src/components/fields/`), audience-tag matrix UI (calls the TD-18 admin endpoints).

**Then GATE-P1** (`p1/GATE-P1.md`). Note: GATE-P1 needs live infra (Resend OTP delivery TD-M3, deployed env) — the code-side exit criteria are achievable locally; infra-side criteria are blocked on the manual To-Dos below.

### Remaining P0 (needed before/at GATE-P0 and for deploy)
- **TD-10** (paired): Stitch design pass → `docs/DESIGN.md`. `.mcp.json` already committed with `${STITCH_API_KEY}` expansion; key is in local gitignored `.env`. The MCP server URL/invocation was a best-effort guess (docs page was JS-only and unreadable via fetch) — **verify the Stitch MCP actually connects on first use; fallbacks: `npx @_davideast/stitch-mcp proxy` or `@google/stitch-mcp`** per P0.T4.S6. openpencil optional enhancement (user mentioned; not yet set up).
- **TD-11**: design tokens → Tailwind/shadcn both apps (blocked on TD-10).
- **TD-12/13/14/15**: CI workflows (quality, contract checks, E2E/react-doctor, deploy). **Blocked on GitHub push access (see §7).**
- **Manual/paired infra (user-executed, checklists in `handoff/manual-checklists.md`):** TD-M1 (finish: zone-Active confirmation + renewal/WHOIS record — domain already bought, NS already delegated), TD-M2 (R2 bucket + Turnstile + Web Analytics), TD-M3 (Resend SPF/DKIM/DMARC — **blocks live OTP delivery for TD-17**), TD-M4 (Railway services — CLI already logged in), TD-M5 (auto-deploy off + RAILWAY_TOKEN env secret), TD-M6 (Tunnel + Access).

### P2 / P3
Cards fully written (`todos/p2/`, `todos/p3/`) but untouched. Start P2 with **TD-24 contention protocol** before fanning out tracks. P2/P3 deferred to later sessions per user.

## 5. System decisions taken (explicit log)

1. **npm, not pnpm** — per-app OpenAPI typegen; pnpm workspaces + shared types package rejected (conflict between tech-stack-analysis and development-plan resolved toward the development-plan).
2. **Feature-based layout** (user-mandated mid-session) — refactored backend after TD-17; conventions invariant 5 now carries the template for backend/frontend/admin.
3. **noindex from day one** — `NEXT_PUBLIC_INDEXABLE` defaults false (P3 decision pulled into TD-04); Railway hostname never indexable; flip only at TD-36.
4. **Client-side relevance** — pages ship full dataset + tag map as one static variant; no `cookies()` in content RSCs (kills ISR silently). OverviewIntro: default row server-rendered, all six in payload, client swap.
5. **Migration serialization** — only ONE agent generates migrations at a time (this session: TD-16 → TD-17 → TD-18 ran sequentially for exactly this reason). `scripts/regen_migration.sh` (TD-24) will mechanize it for P2.
6. **Resolver contract** — `is_relevant(item_tag_slugs: set[str], overrides: set[str], audience: str, tag_map: dict[str, set[str]]) -> bool` lives in `features/relevance/service.py` (decision: feature-local, not core, matching the feature-based structure; TD card said `core/relevance.py` — feature layout wins). TS twin must match verbatim (TD-21 parity fixture).
7. **StorageAdapter is sync** (boto3 is sync) — documented in module.
8. **Static admin serving via catch-all route, not StaticFiles mount** — avoids the mount-order trap entirely; `/api/*` still 404s correctly.
9. **Stitch key** stored only in local `.env` (gitignored); `.mcp.json` committed with env expansion.
10. **Caveman** project-level installed (AGENTS.md carries it); responses in future sessions should stay terse per that config.
11. **Test DB strategy** — real `portfolio_test` Postgres DB, schema from registry metadata, never mock query logic. Seeds from migrations are NOT present in the test DB (metadata.create_all doesn't run migrations) — integration tests insert their own fixtures.

## 6. Mistakes hit & resolutions (do not repeat)

1. **`git mv` on uncommitted files fails** ("not under version control") — commit first, then plain `mv`; git detects renames at next commit.
2. **Parallel agents editing the same file** — TD-08 and TD-09 both edited `core/config.py` concurrently; survived because edits were disjoint appends, but TD-09 saw TD-08's half-written state and reported phantom test failures. Rule: never dispatch two agents that touch the same file; verify merged state after parallel waves (`pytest + ruff + mypy`).
3. **Parallel autogenerate = multiple heads** — the core P2 risk already bit conceptually; prevented by serializing migration-generating To-Dos. Keep this discipline.
4. **`sa.Enum(PythonEnum)` persists member NAMES by default** (`'DRAFT'` not `'draft'`) — fixed with `values_callable=lambda obj: [e.value for e in obj]`. Apply to every future enum column.
5. **Alembic autogenerate can't see enums with no columns yet** — TD-16 migration needed hand-added `CREATE TYPE audience`/`publish_status`. TD-18 reused them with `create_type=False`. Check generated enum handling on every migration.
6. **`greenlet` missing** broke SQLAlchemy async — added explicitly to deps.
7. **shadcn CLI v4 breaking changes** — `--base-color` flag gone; shadcn 2.x broken against current registry; use v4 defaults (`--base radix --preset nova` worked for admin). Expect drift; verify flags at runtime.
8. **`ruff format` debt accumulated across parallel agents** — subagents avoided formatting foreign files (conflict risk), leaving 10 unformatted files; repo-wide `uv run ruff format .` applied at session end. Future sessions: run format check in VERIFY of every card.
9. **conftest imports break when moved** — promoting `app/tests/conftest.py` → `app/conftest.py` broke `from app.tests.conftest import TEST_ADMIN_PASSWORD`; constants moved to `app/tests/helpers.py`. Import constants from `helpers`, never from `conftest`.
10. **`gh` CLI was absent and still unauthenticated**; `git push` fails (no credentials) — see blockers.
11. **MinIO bucket needed public-read policy** for URL GETs (test fixture sets it via the adapter client; mirrors prod R2 public access).

## 7. BLOCKERS needing user action

1. **GitHub auth** — `git push` fails ("Password authentication not supported") and `gh` is not logged in. User must run `gh auth login` (or add SSH key). Until then: 6 local commits unpushed, secret-scanning/push-protection verification pending, ALL CI To-Dos (TD-12..15) untestable.
2. **TD-M2/M3** — R2 credentials, Turnstile keys, Resend verified domain. TD-17's OTP email path is mocked in tests until Resend is live.
3. **TD-M4..M6** — Railway service provisioning, tunnel, Access.
4. **Stitch MCP verification** — confirm the committed `.mcp.json` invocation connects (see §4 TD-10 note).

## 8. Execution protocol for the next session

1. Read this handoff → `todos/README.md` → the card you're executing → `docs/conventions.md` invariants.
2. Per To-Do loop: brainstorm (gap check; small decisions recorded on the card; big gaps → ask user) → plan → execute (subagents only where file sets are disjoint AND at most one agent touches migrations) → code (TDD) → test (card acceptance + `uv run pytest -q`, `ruff check`, `ruff format --check`, `mypy app`; frontend: `npm run lint`, `tsc --noEmit`, `next build`) → code review → verify (evidence before claims) → conventional commit.
3. Same error 3× → stop, systematic-debugging, re-plan.
4. Backend commands run from `backend/`; local services via `docker compose up -d` from repo root.
5. Update the card's status in `todos/README.md` after each To-Do.
6. Never commit secrets; never echo key values; `.env` files stay gitignored.
7. Terse output (caveman config active in AGENTS.md).

## 9. Watch-list for future work

- **GATE-P1 static-route assertion**: add a CI/build check that content routes are `○ Static` (catches accidental `cookies()` usage).
- **OpenAPI typegen** (TD-21) must include a committed `openapi.json` export script; TD-13's drift check depends on it.
- **Timeline FK for Projects** — P2 Track A FKs into `timeline_entries`; settle nothing in TD-20 that would make that FK painful (UUID PK already set).
- **Query-count assertion** in TD-20 guards N+1 (`selectinload` tags).
- **Revalidation tag parity** — backend `core/cache_tags.py` and frontend `lib/cacheTags.ts` must stay in sync manually until a generator exists.
- **Seeded data duplication** — relevance seeds exist via migration; test DB doesn't get them. Any feature relying on seeded tags in tests must insert fixtures explicitly.
- **opencode.json** contains a provider API key and is gitignored — recommend the user move it to env expansion and consider rotating it (it was pasted in chat once).
- **Docker image cleanup** — `portfolio-backend:test` image from TD-09 verification can be pruned.
