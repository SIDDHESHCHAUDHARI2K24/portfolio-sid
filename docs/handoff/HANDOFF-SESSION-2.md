# HANDOFF — Session 2 (P1 Wave 6 completion through GATE-P1)

**Written:** end of session 2 · **Next session:** P0 CI/infra leftovers (TD-10..15, blocked on GitHub auth) → P2 content tracks (TD-24 → TD-30).
**Start here:** read this file, then `development_plan/todos/README.md` (master index), then the specific To-Do cards you are executing. All cards live in `development_plan/todos/<phase>/`.

---

## 1. Snapshot

- **Repo:** `github.com/SIDDHESHCHAUDHARI2K24/portfolio-sid` (public). Local: `/Users/siddheshc2001gmail.com/Coding Projects/Portfolio`, branch `main`.
- **Commit (head):** `b47bf02` feat(p1): timeline backend + frontend shell + admin CRUD + public page + GATE-P1
  - One commit covering TD-20, TD-21, TD-22, TD-23 + GATE-P1 (72 files, +10369 / −108). All four Wave 6 To-Dos landed in a single commit because they crossed file sets during parallel subagent execution.
- **Previous commits (from Session 1):** `a0a89d2` → `65d9f4a` → `48f14d5` → `65aaef7` → `9809b44` → `b8acd40`
- **Push status:** NOT pushed. GitHub auth still blocked — user needs `gh auth login` or SSH key. 7 local commits unpushed.
- **Backend tests:** 93 passing (`cd backend && uv run pytest -q`). ruff check/format clean, mypy strict clean (66 source files).
- **Alembic chain (single head `4fc2a3dab90d`):** `base → d902650351c6` (core foundations: enums, topic_tags) `→ fb100e58ff80` (auth: otp_challenges, login_attempts) `→ cf9af7fc8db5` (relevance: audience_tag_map + seeds) `→ fe8ef9031bfb` (timeline: entries + M2M) `→ 4fc2a3dab90d` (overview: intro model + 6 seed rows).
- **Feature slices (4 total):** `auth/`, `relevance/`, `timeline/`, `overview/`. All follow conventions invariant 5 template.
- **Frontend build:** `/` and `/timeline` both `○ (Static)`. Only `/api/revalidate` is `ƒ (Dynamic)`. No `cookies()` in content RSCs. Category cookie + HUD wired. 8 relevance parity vitest tests pass.
- **Admin build:** Vite + TS pass. Login flow, auth guard, timeline CRUD, tag-map matrix, 4 shared field components (`TagSelect`, `AudienceOverrideSelect`, `PublishStatusField`, `MarkdownField`).
- **OpenAPI typegen:** Committed `backend/openapi.json` (exported from FastAPI). Types generated into `frontend/src/api.d.ts` and `admin/src/api.d.ts` via `openapi-typescript@7`. Admin required `--legacy-peer-deps` (TS 6 vs openapi-typescript expecting TS 5 — types work fine).
- **Local services:** Unchanged from Session 1: `docker compose up -d` for Postgres 16.14 + MinIO + bucket `portfolio-media`. Test DB `portfolio_test` auto-created.
- **Key versions (unchanged):** Next.js 16.3, Vite 8 + TS 6 + oxlint, FastAPI 0.141, SQLAlchemy 2.0.51, uv 0.11, Python 3.13.

---

## 2. What was developed (done To-Dos)

### P1 Wave 6 — completed this session
| To-Do | State | Evidence |
|---|---|---|
| TD-20 Timeline backend | DONE | `app/features/timeline/` — model (TimelineEntry with TimelineKind enum, M2M TopicTag via `timeline_topic_tags`, ARRAY audience_override, index start_date DESC), schemas (Public/Admin/Create with `end_date >= start_date` validator, Update all-optional), repository (public_filter, selectinload tags, query-count constant), service (enum coercion, revalidation-triggered from router not service — see §5), routers (public GET + admin full CRUD with router-level admin_auth), migration `fe8ef9031bfb`, 10 integration tests covering draft leaks, auth guards, CRUD lifecycle, revalidation, invalid dates, unknown tags |
| TD-21 Frontend shell + typegen | DONE | `backend/scripts/export_openapi.py` → committed `openapi.json`. `openapi-typescript@7` generates `frontend/src/api.d.ts` + `admin/src/api.d.ts`. `frontend/lib/relevance.ts` mirrors Python `is_relevant` exactly + 8 vitest parity tests. `frontend/lib/api.ts` tagged fetch wrapper. `frontend/components/CategoryProvider.tsx` — `portfolio_category` cookie (1yr/Lax/NOT HttpOnly), `?for=` override. `next build` confirms `/` and `/timeline` static. `grep -rn "cookies()" frontend/app/` returns 0 hits |
| TD-22 Timeline public + tile contract | DONE | `frontend/app/timeline/page.tsx` — RSC fetching entries + tag map, client `TimelineClient` applies highlight/dim via `isRelevant`. `frontend/components/timeline/FilterChips.tsx` — OR semantics, URL-reflected (`?tags=`), canonical bare. `frontend/app/page.tsx` — real homepage with default overview + tile grid. `backend/app/features/overview/` — `OverviewIntro` model (audience unique, 6 seeded rows), schemas, repository, service, router (public GET + admin CRUD), migration `4fc2a3dab90d`. `frontend/components/tiles/TileGrid.tsx` + `TimelineTile.tsx` — tile contract: `{id, title, summary, href, audiences, priority, isEmpty}`, omission (not dimming) for irrelevant tiles. `frontend/components/hud/HUD.tsx` — fixed bottom-right, compact category selector, scroll percentage, instant switching (no animation/navigation), "show everything" reset. Tile contract documented in `docs/conventions.md` with worked example |
| TD-23 Admin shell + CRUD | DONE | Login flow (`/login` password → `/login/verify` OTP with countdown, attempts display, 429 handling). `AuthGuard.tsx` — checks `/api/v1/admin/me`, redirects on 401. `AdminLayout.tsx` — sidebar (Dashboard, Timeline, Tag Map), logout, `<Outlet />`. Timeline CRUD — `TimelineList.tsx` (table with status badges + kind filter), `TimelineForm.tsx` (all fields, tag multi-select, audience checkboxes, status + conditional publish_at, markdown preview). 4 shared field components in `admin/src/components/fields/` (`TagSelect`, `AudienceOverrideSelect`, `PublishStatusField`, `MarkdownField`). `TagMapMatrix.tsx` — audience-tag checkbox grid, batch save, tag CRUD (create/rename/delete with in-use blocking). **Additional backend work:** tag CRUD endpoints added to relevance feature (`GET/POST/PATCH/DELETE /api/v1/admin/tags`), `tag_admin_router` registered in `app.py` |
| GATE-P1 | VERIFIED | All 11 exit criteria checked locally (code-side). Infra-side blocked on manual To-Dos |

---

## 3. New capabilities summary

- **Running backend:** `cd backend && uv run uvicorn app.app:create_app --factory --reload` (port 8000, serves `/api/v1/*` + admin SPA catch-all)
- **Running frontend:** `cd frontend && npm run dev` (port 3000, SSR/ISR with tagged revalidation)
- **Running admin:** `cd admin && npm run dev` (port 5173, proxied `/api`→`:8000`)
- **Regenerate OpenAPI types:** `cd backend && python scripts/export_openapi.py` then `cd frontend && npm run openapi:generate` and `cd admin && npm run openapi:generate`
- **Dev DB:** `docker compose up -d` from repo root → Postgres :5432 + MinIO :9000
- **Frontend test:** `cd frontend && npx vitest run` (8 relevance parity tests)
- **Admin build (for backend Dockerfile):** `cd admin && npm run build` → `admin/dist/`

---

## 4. Decisions taken this session

1. **Revalidation moved from service to router** — Originally the TD card and development plan placed `revalidate()` calls inside the service layer. In Session 1, relevance did it in the service with commit-inside-service. This session's timeline service initially followed that pattern but triggered MissingGreenlet errors because `session.flush()` (inside repository) expires `updated_at` (set by `onupdate=func.now()`), and the subsequent `revalidate()` HTTP call runs before Pydantic validation. **Decision: perform ORM operations + dict serialization in the service, commit in the service, then revalidate in the router after the response is built.** This is a structural deviation from TD-19/conventions invariant 8 ("revalidate after commit in service"). Noted here for Phase 2 reflection — the invariant may need updating.

2. **No `from_attributes=True` in Pydantic schemas** — Pydantic's `model_validate(obj, from_attributes=True)` triggers lazy-loads on ORM relationships, causing `MissingGreenlet` when any attribute was expired (even with `expire_on_commit=False`). **Decision: all feature routers serialize ORM objects to plain dicts before Pydantic construction.** The `_entry_to_dict()` helper in the service layer accesses all attributes while the greenlet is active, then returns a plain dict. Pydantic schemas use `model_validate` without `from_attributes`.

3. **Service returns dicts, not ORM objects** — Related to above. `service.create_dict()`, `service.update_dict()`, `service.get_dict()`, etc. return `dict[str, object]`. Routers pass these dicts to Pydantic constructors (`TimelineEntryAdmin(**d)`). This completely sidesteps MissingGreenlet.

4. **Topic tag relationship must be explicitly initialized** — The `repository.create()` method used `if tag_ids:` to conditionally set `entry.topic_tags`. Empty `[]` is falsy, so entries created without tags had uninitialized relationships → MissingGreenlet on Pydantic access. **Fix: always set `entry.topic_tags = tags` (or `[]`) in create, and `_ = entry.topic_tags` in update when not changing tags.**

5. **Enum coercion in service** — Pydantic `model_dump()` converts StrEnum members to plain strings. When constructing ORM objects from dumped data, string values must be converted back to enum members. The service layer does this explicitly for `kind`, `status`, and `audience_override`.

6. **Alembic use `create_type=False` for all pre-existing enums** — migrations for timeline and overview both use `create_type=False` for `audience`, `publish_status`, and any enum whose CREATE TYPE already exists. Missing this causes `DuplicateObjectError`. The timeline migration additionally has a `timeline_kind` enum which IS created. All uses of existing types in ARRAY columns also need `create_type=False`.

7. **Tag CRUD added to backend** — TD-23 required tag management in the admin matrix UI, which needed backend endpoints. Added `GET/POST/PATCH/DELETE /api/v1/admin/tags` to the relevance feature (not a separate feature). Tags are shared infrastructure.

8. **`openapi-typescript@7` needs TS 5.x, admin uses TS 6.x** — installed with `--legacy-peer-deps`. The generated `.d.ts` files work correctly. Not future-proof — upgrade path is installing openapi-typescript@8 (which supports TS 6) when available.

9. **VS Code Python env file** — Created `.vscode/settings.json` pointing `python.envFile` at workspace root `.env`. Required to let VS Code's Python extension inject env vars into terminals.

---

## 5. Issues hit & resolutions (do not repeat)

1. **MissingGreenlet: `updated_at` expired after flush** — The `updated_at` column with `onupdate=func.now()` was expired by `session.flush()` even with `expire_on_commit=False`. Accessing it after flush (in Pydantic validation or dict serialization) triggered lazy-load requiring greenlet → MissingGreenlet. **Fix: explicitly set `entry.updated_at = datetime.now(UTC)` before flush in service, AND serialize to dict before any async call (revalidate, commit).** This hit the timeline update flow 5+ times before resolution.

2. **MissingGreenlet: topic_tags relationship uninitialized** — `if tag_ids:` skipped setting the relationship when `tag_ids` was empty `[]`. **Fix: always set `entry.topic_tags` in create (to `[]` when empty), and in update, touch the relationship with `_ = entry.topic_tags` when not changing tags.**

3. **Enum mismatch: `entry.status.value` on string** — When constructing ORM objects from Pydantic-dumped dicts, enum fields were strings (not enum members). The `_entity_to_dict` helper initially assumed `.value` was always available. **Fix: added `_enum_val()` helper that handles both `hasattr(v, "value")` and plain strings.** Later replaced by `_entry_to_dict` in service layer with explicit enum coercion.

4. **Test state leakage via session-scoped fixture** — The `seeded_tags` fixture (session-scoped) leaked "engineering", "ai", "consulting" tags into the test DB, causing `test_topic_tag_round_trip` to fail with UniqueViolationError. **Fix: changed `seeded_tags` from `loop_scope="session"` to function-scoped with cleanup (DELETE in teardown).**

5. **Alembic downgrade-to-base fails due to enum types** — Downgrading past `d902650351c6` drops all tables but cannot drop enum types because test tables (`test_publishables`) still reference them. **Workaround: `DROP DATABASE portfolio WITH (FORCE)` then re-create and re-upgrade. Not required for normal development — only when validating full downgrade chain.**

6. **Monkeypatching `revalidate` for tests** — After moving revalidation from service to router, tests that patched `service.revalidate` stopped working. **Fix: patch `router.revalidate` on the router module (`timeline_router`).**

7. **Ruff E501 on long lines** — `repository.py:38` line >100 chars from `session.get()` with inline options list. **Fix: break across multiple lines.**

8. **`pytest_asyncio` fixture return type** — mypy requires `AsyncIterator[list[str]]` for async generator fixtures, not plain `list[str]`. **Fix: added proper type annotation.**

---

## 6. REMAINING WORK — continue here next session

### Priority order:

### Block A — P0 CI/infra (execute when GitHub push is unblocked)
| ID | Title | Status | Blocker |
|---|---|---|---|
| TD-10 | Stitch MCP + DESIGN.md | [~] partial | Stitch MCP verification pending (see HANDOFF-SESSION-1 §4) |
| TD-11 | Design tokens → Tailwind/shadcn | [ ] | Blocked on TD-10 |
| TD-12 | CI: ruff/mypy/ESLint/tsc + tests | [ ] | Blocked on GitHub push |
| TD-13 | CI: OpenAPI drift + Alembic single-head | [ ] | Blocked on GitHub push |
| TD-14 | CI: react-doctor + Playwright E2E + SSR curl | [ ] | Blocked on GitHub push |
| TD-15 | Deploy workflow | [ ] | Blocked on TD-M5, TD-14 |
| TD-M1..M6 | Manual infra (domain, R2, Resend, Railway, Tunnel) | [~]/[ ] | User-executed; checklists in `handoff/manual-checklists.md` |

### Block B — P2 content tracks (after TD-24 unlocks parallelism)
| ID | Title | Effort | Notes |
|---|---|---|---|
| TD-24 | Contention protocol: regen script, registry checks, merge rules | L | Must go FIRST in P2 — unblocks all tracks |
| TD-25 | Track A — Projects (critical path, merges first) | XL | FK to `timeline_entries`, attachments, pinning |
| TD-26 | Track B — Skills + Certifications | L | Real-mobile PDF test required |
| TD-27 | Track C — Thesis + Posts | L | Collections ≠ topic tags (invariant 9) |
| TD-28 | Track D — Collections + ProsePages | L | Cover pipeline |
| TD-29 | Track E — Resume + Forms | L | Turnstile integration |
| TD-30 | Track F — Intro sequence + ambient audio | L | Blocked on TD-11 |

All P2 cards are fully written in `development_plan/todos/p2/`. Start with TD-24, then dispatch tracks A–F in the merge queue order from conventions.md §77-78. Only ONE migration-generating track at a time.

### Block C — P3 convergence
| ID | Title | Notes |
|---|---|---|
| TD-31..36 | Overview, SEO, analytics, re-skin, a11y, launch | Cards in `development_plan/todos/p3/` |

---

## 7. File maps for quick orientation

### Backend features (all follow conventions invariant 5 template)
```
backend/app/
├── features/
│   ├── auth/           # login, OTP, session, lockout (TD-17)
│   ├── relevance/      # is_relevant resolver, tag map, tag CRUD (TD-18 + TD-23 extras)
│   ├── timeline/       # TimelineEntry model, CRUD, 10 tests (TD-20)
│   └── overview/       # OverviewIntro model, 6 seeds, public/admin endpoints (TD-22)
├── core/               # shared: models, enums, deps, cache_tags, revalidation
├── jobs/               # scheduler.py
├── tests/              # shared helpers (TestPublishable, TEST_ADMIN_PASSWORD)
├── conftest.py         # global fixtures (test DB engine, session, client)
└── app.py              # create_app factory, register_routers
```

### Frontend components
```
frontend/
├── app/
│   ├── page.tsx              # homepage with TileGrid + default OverviewIntro
│   ├── timeline/page.tsx     # timeline RSC + TimelineClient
│   └── layout.tsx            # root layout with CategoryProvider + HUD
├── components/
│   ├── CategoryProvider.tsx  # cookie-based audience selector
│   ├── hud/HUD.tsx           # fixed bottom-right category switcher
│   ├── tiles/
│   │   ├── TileGrid.tsx      # audience-filtered tile layout
│   │   └── TimelineTile.tsx  # timeline tile (id/summary/href/audiences/priority/isEmpty)
│   └── timeline/
│       ├── TimelineClient.tsx # client component applying highlight/dim
│       └── FilterChips.tsx    # OR-filter tag chips, URL-reflected
├── lib/
│   ├── api.ts            # apiFetch<T>() — tagged + revalidated fetch wrapper
│   ├── cacheTags.ts      # CACHE_TAGS constants (sync with backend core/cache_tags.py)
│   ├── relevance.ts      # isRelevant() — TypeScript mirror of Python resolver
│   ├── relevance.test.ts # 8 parity test cases (vitest)
│   └── tiles.ts          # Tile interface definition
└── src/api.d.ts          # generated OpenAPI types
```

### Admin components
```
admin/src/
├── App.tsx                    # route tree
├── main.tsx                   # QueryClient + BrowserRouter
├── lib/
│   ├── api.ts                 # auth-aware fetch wrapper with 401 redirect
│   └── utils.ts               # existing
├── api.d.ts                   # generated OpenAPI types
├── components/
│   ├── AuthGuard.tsx           # /admin/me check → redirect on 401
│   ├── AdminLayout.tsx         # sidebar + outlet
│   └── fields/
│       ├── TagSelect.tsx       # multi-select tag picker (fetches from API)
│       ├── AudienceOverrideSelect.tsx  # checkbox group for 5 audiences
│       ├── PublishStatusField.tsx      # status select + conditional publish_at
│       └── MarkdownField.tsx          # edit/preview toggle
└── routes/
    ├── login.tsx               # password form
    ├── login-verify.tsx        # OTP 6-digit inputs + countdown
    ├── Dashboard.tsx           # stats cards
    ├── TagMapMatrix.tsx        # audience-tag checkbox grid + tag CRUD
    └── timeline/
        ├── TimelineList.tsx    # table with status badges + kind filter
        └── TimelineForm.tsx    # full create/edit form
```

---

## 8. BLOCKERS needing user action

1. **GitHub auth** — unchanged from Session 1. `git push` fails. User must run `gh auth login` or add SSH key. 7 commits unpushed. CI To-Dos (TD-12..15) untestable until resolved.
2. **TD-M2/M3** — R2 credentials, Turnstile keys, Resend verified domain. OTP email send is mocked everywhere.
3. **TD-M4..M6** — Railway services, tunnel, Access.
4. **Stitch MCP verification** — unchanged from Session 1.

---

## 9. Execution protocol for the next session

1. Read this handoff → `todos/README.md` → the card you're executing → `docs/conventions.md`.
2. Per To-Do loop: brainstorm (gap check; small decisions on card; big gaps → ask user) → plan → execute (subagents only where file sets are disjoint AND at most one agent touches migrations) → code (TDD) → test (`uv run pytest -q`, `ruff check`, `ruff format --check`, `mypy app`; frontend: `npm run lint`, `tsc --noEmit`, `npm run build`) → code review → verify (evidence before claims) → conventional commit.
3. Same error 3× → stop, systematic-debugging, re-plan.
4. **Revalidation pattern for P2:** place revalidate in the router (after commit + response build), not in the service layer. Service returns dicts, not ORM objects. See §4 decisions 1-3.
5. **ORM serialization pattern:** never use `from_attributes=True` on Pydantic response schemas. Serialize ORM to dict in service layer → routers pass dict to Pydantic constructor.
6. **Migrations:** set `create_type=False` for ALL pre-existing native Postgres enum types. Only new enums (e.g., per-feature kind enums) get `create_type=True`.
7. Never commit secrets; `.env` files stay gitignored.
8. Backend commands from `backend/`; local services from repo root.
9. Concise output per AGENTS.md conventions.

---

## 10. Watch-list for P2/P3

- **Tile contract** — documented in `docs/conventions.md` (appended in TD-22). Every P2 content feature contributes one `Tile` to `TileGrid.tsx`. The `Tile` interface lives in `frontend/lib/tiles.ts`.
- **Revalidation tags** — must add P2 tags to both `backend/app/core/cache_tags.py` AND `frontend/lib/cacheTags.ts`. Tag parity is currently manual.
- **Project FK → TimelineEntry** — P2 Track A will add a foreign key from Projects to `timeline_entries`. The UUID PK is already set to make this painless.
- **Audience_override as ARRAY** — Timeline's `audience_override` column is `postgresql.ARRAY(AUDIENCE_ENUM)`. P2 content features should follow this pattern (not invent their own).
- **Tag CRUD** — already exists at `/api/v1/admin/tags` (in relevance feature). P2 features reuse these endpoints.
- **openapi.json needs regeneration** after any schema change. Regenerate + commit both `openapi.json` and `*.api.d.ts` files together.
- **`d.b.cot.com.vscode/settings.json`** already exists with `python.envFile` — do NOT overwrite it.
