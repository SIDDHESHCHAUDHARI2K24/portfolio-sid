# Development Plan — Phase 1: The Vertical Spine

**Document 3 of 3, Part 2** · Companions: `tech-stack-analysis.md`, `dependency-map.md`, `development-plan-P0.md`
**Status:** Draft for approval
**Feature IDs:** F2 (data foundations), F4 (admin auth), F5 (publishing), F6 (relevance engine), F7 (typegen), F9 (frontend shell), F10 (admin shell), F12 (anti-abuse), F13 (Timeline)

---

## Phase Overview

**Goal:** Build one content type end-to-end — database through public page — proving every pattern that the nine content features in Phase 2 will replicate. Timeline was chosen deliberately as the hardest case: it merges two record types, carries the most complex tag logic, and exercises highlight/dim, filter chips, publishing states and admin CRUD in a single slice.

**Entry criteria:** Phase 0 exit checklist complete.

**Exit criteria:**
- A Timeline entry created in the admin portal appears on the public site within seconds
- Draft entries are invisible publicly; scheduled entries appear at their scheduled time
- Switching category changes which entries are highlighted, with no page navigation
- Admin portal is unreachable without password + OTP
- The Timeline tile renders on the overview page using the tile contract Phase 2 will reuse
- CI green, including the Alembic single-head check against real migrations

**Estimated effort:** 15–22 days (41 sub-tasks). This is the longest phase and it should be — nine features copy what it establishes.

| Task | Focus | Effort | Risk |
|---|---|---|---|
| P1.T1 | Core data foundations | L / 2–3 days | Medium |
| P1.T2 | Admin auth & anti-abuse | XL / 3–4 days | High |
| P1.T3 | Relevance engine | L / 2 days | Medium |
| P1.T4 | Publishing & revalidation | L / 2–3 days | High |
| P1.T5 | Timeline backend slice | L / 2–3 days | Low |
| P1.T6 | Frontend shell & contract tooling | L / 2 days | High |
| P1.T7 | Timeline public experience | XL / 3–4 days | Medium |
| P1.T8 | Admin shell & Timeline CRUD | L / 2–3 days | Low |

---

## The Architectural Decision This Phase Must Settle

Before any of it, one decision determines how every page in the project caches. It was not resolved during brainstorming because it only becomes visible at implementation.

**Reading a cookie in a Next.js server component opts that route into dynamic rendering.** Calling `cookies()` disables static generation for the whole route. So if we resolve highlight/dim server-side from the category cookie, we lose ISR on every content page — which would forfeit both the caching strategy and much of the reason we chose Next.js.

**Resolution: highlight/dim and tile filtering are client-side concerns.**

Every content page ships the complete dataset plus the `audience_tag_map`, server-rendered and statically cached as **one** variant — the default, unhighlighted view. That is what crawlers receive, and it is the correct thing for them to receive: everyone sees all content, and highlighting is a personalisation layer, not a content difference. A client component then reads the category cookie and applies highlight, dim and tile visibility after hydration.

The one wrinkle is `OverviewIntro`, where the headline and body genuinely differ per audience — that *is* content. Solution: server-render the `default` row into the HTML, ship all six rows in the initial payload, and swap client-side on hydration when a cookie exists. Returning visitors see a brief flash of the default copy; crawlers and first-time visitors see correct content immediately; the page stays statically cacheable. Rendering six server variants of every page to change opacity values would be poor value for the cache complexity it buys.

This is recorded as an invariant in `docs/conventions.md`.

---

## Task P1.T1: Core Data Foundations

**Feature:** F2 · **Effort:** L / 2–3 days · **Dependencies:** P0.T3.S3 · **Risk:** Medium

Everything in `core/` is imported by every feature slice. Errors here are the only ones that ripple across all of Phase 2.

### P1.T1.S1: Define base model and mixins

**Description:** Establish the declarative base and the mixins every content model inherits, so nine feature slices don't each invent their own conventions for primary keys, timestamps and ordering.

**Implementation Hints:** In `app/core/models.py`: `Base` via `DeclarativeBase`; `UUIDMixin` with `id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)`; `TimestampMixin` with `created_at` / `updated_at` as `DateTime(timezone=True)` defaulting to `func.now()` and `onupdate`. Store all timestamps in UTC (assumption A5). Add `SortableMixin` with an integer `sort_order` — manual ordering will be wanted on Books, Skills and Certifications, and retrofitting it later means nine migrations.

**Dependencies:** P0.T3.S3
**Effort:** M / 4 hrs
**Risk Flags:** UUID primary keys are the right call for a public API (no enumerable IDs), but confirm `postgresql.UUID(as_uuid=True)` rather than a string column — a string column costs index efficiency and silently accepts malformed values.
**Acceptance Criteria:**
- A scratch model inheriting all mixins migrates cleanly
- `created_at` and `updated_at` populate automatically
- `updated_at` changes on update, `created_at` does not

### P1.T1.S2: Define the audience enum and topic tag schema

**Description:** Create the five-audience enum and the topic tag model that the relevance engine resolves against. Tags are shared across every content type, so this lives in `core/`, not in a feature slice.

**Implementation Hints:** `Audience` as a Python `enum.StrEnum` with `RECRUITERS`, `TECHIES`, `INVESTORS`, `FOUNDERS`, `PERSONAL` — plus a separate `DEFAULT` sentinel used for the uncategorised view, which must not be a database enum value. Use a native Postgres enum via `SAEnum(Audience, name="audience")`. `TopicTag` model: `id`, `slug` (unique, lowercase, indexed), `label`, `description`. Association tables per content type (`timeline_topic_tags`, later `project_topic_tags`) rather than a polymorphic join — polymorphic tag tables lose foreign key integrity and query poorly.

**Dependencies:** P1.T1.S1
**Effort:** M / 4 hrs
**Risk Flags:** Adding a value to a Postgres native enum requires `ALTER TYPE`, which Alembic does not autogenerate. Document this in `conventions.md` now; a sixth audience later will otherwise produce a migration that appears to succeed and doesn't.
**Acceptance Criteria:**
- `TopicTag` CRUD works with unique slug enforcement
- Audience enum persists and round-trips
- Association table enforces referential integrity on delete

### P1.T1.S3: Define the publishing mixin

**Description:** Add the draft/published/scheduled state that every content model carries. Building this into `core/` now is the difference between one implementation and nine inconsistent retrofits.

**Implementation Hints:** `PublishableMixin` with `status: Mapped[PublishStatus]` (`DRAFT`, `SCHEDULED`, `PUBLISHED`), `publish_at: Mapped[datetime | None]`, `published_at: Mapped[datetime | None]`. Provide a reusable query helper in `core/queries.py`: `public_filter(model)` returning `or_(model.status == PUBLISHED, and_(model.status == SCHEDULED, model.publish_at <= func.now()))`. Every public endpoint applies it; no endpoint reimplements it. Add a composite index on `(status, publish_at)`.

**Dependencies:** P1.T1.S1
**Effort:** M / 4 hrs
**Risk Flags:** The failure mode is a Phase 2 feature forgetting the filter and leaking drafts publicly. Make `public_filter` the only sanctioned path and assert it in tests for each feature.
**Acceptance Criteria:**
- Draft records are excluded by `public_filter`
- Scheduled records with a past `publish_at` are included; future ones are not
- Admin queries can bypass the filter explicitly

### P1.T1.S4: Build the models registry and first real migration

**Description:** Wire the models registry that Alembic autogenerate depends on, then generate the first migration containing real tables — validating the async Alembic configuration against something other than a scratch model.

**Implementation Hints:** `app/core/models_registry.py` imports every feature's `models` module; `alembic/env.py` imports the registry so `Base.metadata` is fully populated. Adding a feature slice in Phase 2 means adding one import line here — call that out in `conventions.md`, because a forgotten import produces a silently empty migration.

**Dependencies:** P1.T1.S1, P1.T1.S2, P1.T1.S3
**Effort:** S / 2 hrs
**Risk Flags:** This is the exact failure P0.T3.S3 was designed to prevent; this sub-task confirms the prevention works.
**Acceptance Criteria:**
- `alembic revision --autogenerate` produces a migration containing tags and association tables
- `alembic upgrade head` then `downgrade -1` both succeed
- `alembic heads` returns one head

---

## Task P1.T2: Admin Authentication & Anti-Abuse

**Feature:** F4, F12 · **Effort:** XL / 3–4 days · **Dependencies:** P1.T1 · **Risk:** High

With no domain-gated Access in the interim and a public repository documenting the entire API surface, app-layer auth is the only barrier. It has to be right rather than adequate.

### P1.T2.S1: Password hashing and verification

**Description:** Implement master password verification with Argon2id. The hash is generated once offline and stored as a Railway environment variable — no password is ever stored in the database or the repository.

**Implementation Hints:** `argon2-cffi`'s `PasswordHasher` with library defaults. Provide a small CLI (`uv run python -m app.cli hash-password`) to generate the hash. Read `ADMIN_PASSWORD_HASH` via `pydantic-settings`. `verify()` raises rather than returning False — catch `VerifyMismatchError` explicitly. Return an identical generic response for wrong-password and unknown-state cases so responses reveal nothing.

**Dependencies:** P1.T1.S1
**Effort:** M / 3 hrs
**Risk Flags:** Argon2's verification time is deliberately slow, which is also what makes the login endpoint a plausible denial-of-service target. The rate limiter in S5 is not optional.
**Acceptance Criteria:**
- Correct password verifies; incorrect fails
- No plaintext password appears in code, logs or git history
- Timing does not distinguish failure modes

### P1.T2.S2: OTP generation, storage and verification

**Description:** Implement the one-time code issued after successful password verification. Codes are single-use, short-lived, attempt-limited, and stored hashed.

**Implementation Hints:** Generate with `secrets.randbelow(1_000_000)` zero-padded to six digits — never `random`. `OtpChallenge` model: `id`, `code_hash`, `expires_at` (5 minutes), `attempts` (max 5), `consumed_at`, `created_ip`. Hash with SHA-256; Argon2 is unnecessary for a six-digit five-minute secret and its cost would be paid on every verification attempt. Compare with `hmac.compare_digest`. Invalidate any outstanding challenge when a new one is issued, so an attacker cannot widen the valid-code space by requesting many.

**Dependencies:** P1.T2.S1
**Effort:** M / 4 hrs
**Risk Flags:** Six digits is a million-value space — without the attempt cap and expiry it is brute-forceable in minutes. The cap is what makes this secure, not the code length.
**Acceptance Criteria:**
- Expired, consumed, and over-attempted codes are all rejected
- Issuing a new challenge invalidates the previous one
- Codes are never logged or returned in any response body

### P1.T2.S3: Deliver OTP via Resend

**Description:** Send the code to the configured admin email address.

**Implementation Hints:** Wrap the Resend SDK in `app/core/email.py` with a `send_otp(code)` function, so Phase 2's form notifications reuse one client. Send asynchronously but **await the result before returning success** — a fire-and-forget send that silently fails locks you out of your own portal with no signal. Log delivery failures at error level.

**Dependencies:** P1.T2.S2, P0.T1.S6
**Effort:** S / 2 hrs
**Risk Flags:** If the domain is unverified, Resend's free tier delivers only to your own verified address — acceptable here since that is the only recipient, but confirm before relying on it.
**Acceptance Criteria:**
- Requesting an OTP delivers an email within seconds
- Send failure returns a clear error rather than a false success

### P1.T2.S4: Session cookie issuance and validation

**Description:** Issue a signed session cookie on successful OTP verification and validate it on every admin request.

**Implementation Hints:** `itsdangerous.URLSafeTimedSerializer` with `SESSION_SECRET`. Cookie flags: `HttpOnly`, `Secure`, `SameSite=Strict`, `max_age=8h`, `path=/`. A JWT is unnecessary — there is one user and no distributed verification, and a signed cookie is easier to invalidate. Rotate the session value on login. FastAPI dependency `require_admin()` in `core/deps.py` raises 401 on absent or invalid cookie.

**Dependencies:** P1.T2.S2
**Effort:** M / 4 hrs
**Risk Flags:** `SameSite=Strict` is correct given same-origin admin, but will break the local cross-origin dev setup — allow `Lax` in development via config, never in production.
**Acceptance Criteria:**
- Valid session grants access; tampered or expired cookie returns 401
- Cookie carries all four security flags in production
- `require_admin()` protects a test endpoint

### P1.T2.S5: Rate limiting and database-backed lockout

**Description:** Apply request-rate limits and a persistent attempt counter to the login and OTP endpoints.

**Implementation Hints:** `slowapi` for IP-based limits — login 5/min, OTP issuance 3/15min. Because in-memory counters are per-process (gap G2), add a database-backed `LoginAttempt` table recording IP, timestamp and outcome, with a lockout after 10 failures in 15 minutes. The database counter is replica-safe regardless of how Railway scales. Return 429 with a generic message.

**Dependencies:** P1.T2.S1, P1.T2.S2
**Effort:** M / 4 hrs
**Risk Flags:** In-memory limits multiply if replicas ever exceed one. The DB counter is the real protection; treat slowapi as a cheap first line.
**Acceptance Criteria:**
- Exceeding the rate returns 429
- Ten failures within the window locks out further attempts even across process restarts
- Successful login clears the counter

### P1.T2.S6: Cloudflare Access JWT verification (env-gated)

**Description:** Verify the `Cf-Access-Jwt-Assertion` header against Cloudflare's team JWKS when Access is enabled, so the API rejects anything that bypassed the edge.

**Implementation Hints:** `PyJWT` with the JWKS at `https://<team>.cloudflareaccess.com/cdn-cgi/access/certs`, cached with a TTL rather than fetched per request. Validate `aud` against the Access application AUD tag and `iss` against the team domain. Gate the whole dependency on `CF_ACCESS_ENABLED`; when false, app-layer auth carries alone. This is defense in depth — Access authenticates identity at the edge, and this ensures the origin refuses traffic that didn't come through it.

**Dependencies:** P1.T2.S4, P0.T2.S6
**Effort:** M / 4 hrs
**Risk Flags:** Fetching JWKS on every request adds latency and a hard dependency on Cloudflare availability. Cache it.
**Acceptance Criteria:**
- With the flag on, requests without a valid assertion return 403
- With the flag off, app-layer auth behaves unchanged
- JWKS is cached, not refetched per request

### P1.T2.S7: Turnstile verification helper

**Description:** Build the reusable server-side Turnstile verification that Phase 2's contact and dealflow forms will both depend on.

**Implementation Hints:** `app/core/antispam.py` with `verify_turnstile(token, remote_ip) -> bool` calling the `/siteverify` endpoint with the secret key. Verification is mandatory — an unverified token is worthless. Call it **before any database write**, and return the same generic response on failure as on success, so a bot cannot learn which submissions were rejected. Add a `honeypot` helper that accepts and silently discards submissions with the hidden field populated.

**Dependencies:** P0.T1.S4
**Effort:** S / 2 hrs
**Risk Flags:** Tokens expire after 300 seconds and are single-use. A form left open on a tab will fail validation — the frontend must handle re-challenge gracefully in Phase 2.
**Acceptance Criteria:**
- A valid token passes; an expired, reused or forged token fails
- Honeypot submissions return success without persisting

---

## Task P1.T3: Relevance Engine

**Feature:** F6 · **Effort:** L / 2 days · **Dependencies:** P1.T1 · **Risk:** Medium

The mechanism behind highlight/dim on Timeline and Projects, tile visibility on Overview, and resume variant selection. Three features, one implementation.

### P1.T3.S1: Model the audience-tag mapping

**Description:** Create the admin-editable table mapping each audience to the topic tags that make content relevant to it. In the database rather than a config file, so changing the mapping doesn't require a deploy.

**Implementation Hints:** `AudienceTagMap` with `audience` (enum) and `topic_tag_id`, unique together. Seed it in a migration with sensible defaults — `#engineering` and `#consulting` for Recruiters, `#startup` and `#fundraising` for Founders, and so on — so the feature is demonstrable before you've hand-configured anything.

**Dependencies:** P1.T1.S2
**Effort:** S / 2 hrs
**Acceptance Criteria:**
- Mapping persists and enforces uniqueness
- Seed data present after migration

### P1.T3.S2: Implement relevance resolution

**Description:** Implement the function deciding whether a content item is highlighted for a given audience: tag intersection, unioned with any per-item override.

**Implementation Hints:** In `app/core/relevance.py`:
```python
def is_relevant(item_tag_slugs: set[str], overrides: set[Audience], audience: Audience,
                tag_map: dict[Audience, set[str]]) -> bool:
    if audience in overrides:
        return True
    return bool(item_tag_slugs & tag_map.get(audience, set()))
```
Keep it a pure function over plain data — no ORM objects, no database access. That makes it trivially testable and lets the identical logic ship to the client (see the architectural decision above). Load the tag map once per request, never per item.

**Dependencies:** P1.T3.S1
**Effort:** M / 3 hrs
**Risk Flags:** Resolving per item with a database round-trip each turns a page render into N+1 queries. Load the map once.
**Acceptance Criteria:**
- Matching tags produce a highlight; non-matching do not
- An override forces a highlight regardless of tags
- `Audience.DEFAULT` highlights nothing

### P1.T3.S3: Expose the tag map endpoint

**Description:** Serve the full audience-tag map to the frontend so the client can resolve relevance without a round-trip per page.

**Implementation Hints:** `GET /api/v1/relevance/map` returning `{audience: [tag_slug, ...]}`. Small and rarely changing — cache aggressively and revalidate when the admin edits the mapping. Ship it in the initial payload of every content page.

**Dependencies:** P1.T3.S2
**Effort:** S / 2 hrs
**Acceptance Criteria:**
- Endpoint returns all five audiences with their tags
- Editing the mapping in admin invalidates the cached response

### P1.T3.S4: Test the resolution logic against a real database

**Description:** Cover the intersection and override behaviour with integration tests running against Postgres, not mocks.

**Implementation Hints:** `pytest` with a Docker Postgres or `testcontainers`. Cases: no tags; tags matching one audience only; tags matching several; override with no matching tags; override plus matching tags; empty tag map for an audience. Do not mock the database for these — tag intersection is exactly the query logic where a mock will confidently return whatever you told it to.

**Dependencies:** P1.T3.S2
**Effort:** M / 3 hrs
**Acceptance Criteria:**
- All six cases covered and passing
- Tests run against real Postgres in CI

---

## Task P1.T4: Publishing Workflow & Revalidation

**Feature:** F5 · **Effort:** L / 2–3 days · **Dependencies:** P1.T1.S3 · **Risk:** High

### P1.T4.S1: Build the revalidation route handler

**Description:** Add the Next.js endpoint the backend calls after any content mutation, triggering immediate regeneration of affected pages.

**Implementation Hints:** `app/api/revalidate/route.ts` accepting POST with a shared secret in a header, compared with a timing-safe comparison. Body carries tags to invalidate; call `revalidateTag()` for each. Use tags (`timeline`, `projects`, `overview`) rather than paths — a tag invalidates every page consuming that data, whereas paths must be enumerated and will be forgotten.

**Dependencies:** P0.T3.S5
**Effort:** M / 4 hrs
**Risk Flags:** An unauthenticated revalidation endpoint is a cheap denial-of-service vector on a public site. The secret is required.
**Acceptance Criteria:**
- Valid secret triggers revalidation; invalid returns 401
- Fetches tagged `timeline` return fresh data after a call

### P1.T4.S2: Trigger revalidation from content mutations

**Description:** Call the webhook from the backend whenever content is created, updated, deleted or published.

**Implementation Hints:** A `revalidate(tags)` helper in `app/core/revalidation.py`, invoked from feature service layers rather than routers, so admin API and the scheduler share one path. Fire after commit, never inside the transaction — revalidating a change that then rolls back publishes a lie. Failures must log loudly but not fail the write: the content is saved and correct, only the cache is stale.

**Dependencies:** P1.T4.S1
**Effort:** M / 4 hrs
**Risk Flags:** Silent webhook failure is exactly gap G11 — content edits appear not to work while the database is perfectly correct. Log at error level.
**Acceptance Criteria:**
- Creating a Timeline entry in admin surfaces it publicly within seconds
- Webhook failure logs an error and does not roll back the write
- Revalidation fires after commit, not before

### P1.T4.S3: Implement the scheduled-publish cron job

**Description:** Replace the P0 stub with the job that promotes scheduled content and triggers revalidation.

**Implementation Hints:** `app/jobs/scheduler.py` querying every publishable model for `status == SCHEDULED AND publish_at <= now()`, setting `status = PUBLISHED` and `published_at = now()`, then revalidating affected tags. Iterate the models registry rather than hardcoding a list — a Phase 2 feature that forgets to register would otherwise never publish on schedule. Make the job idempotent: a second run within the same minute must be a no-op.

**Dependencies:** P1.T4.S2, P0.T2.S4
**Effort:** M / 4 hrs
**Risk Flags:** Running every 5 minutes means up to 5 minutes of latency against the scheduled time. Acceptable for a portfolio; state it in `conventions.md` so it isn't later mistaken for a bug.
**Acceptance Criteria:**
- An entry scheduled for the past is published on the next run
- Future-scheduled entries are untouched
- Repeated runs cause no duplicate work or repeated revalidation

### P1.T4.S4: Enforce the public filter across endpoints

**Description:** Apply `public_filter` to every public read path and verify that drafts and future-scheduled content never leak.

**Implementation Hints:** Add a test helper asserting that any public endpoint excludes draft records, and apply it per feature in Phase 2. Consider a shared base repository whose public read method applies the filter by default, so a feature has to opt *out* rather than remember to opt in.

**Dependencies:** P1.T1.S3, P1.T5.S3
**Effort:** S / 2 hrs
**Risk Flags:** This is the leak that would embarrass you publicly — an unfinished thesis draft served on the live site. Make it structurally hard rather than a rule to remember.
**Acceptance Criteria:**
- Public endpoints exclude drafts and future-scheduled content
- Admin endpoints see everything
- A test asserts the exclusion and is reusable by Phase 2 features

---

## Task P1.T5: Timeline Backend Slice

**Feature:** F13 · **Effort:** L / 2–3 days · **Dependencies:** P1.T1–P1.T4 · **Risk:** Low

The first feature slice. Its shape is the template nine more will copy — layout matters as much as behaviour here.

### P1.T5.S1: Model the unified timeline entry

**Description:** Model education and professional history as a single chronological entity distinguished by kind, rather than two models joined at render time.

**Implementation Hints:** `app/features/timeline/models.py` — `TimelineEntry` inheriting `UUIDMixin`, `TimestampMixin`, `SortableMixin`, `PublishableMixin`, with `kind` (`EDUCATION` / `EXPERIENCE`), `title`, `organisation`, `location`, `start_date`, `end_date` (nullable — null means current, assumption A8), `summary` (markdown), `highlights` (JSONB array of strings), `external_url`, `audience_override` (array of audience enum), and a many-to-many to `TopicTag`. Index `(start_date DESC)`. A single model is right because the two record types differ only in labels and render identically in one chronological list — separate models would mean union queries and duplicated tag and publishing logic.

**Dependencies:** P1.T1.S4
**Effort:** M / 4 hrs
**Risk Flags:** Projects will foreign-key to this in Phase 2 (`dependency-map.md` §5) — Projects is the only content feature on the critical path for that reason. Settle this schema before Phase 2 starts.
**Acceptance Criteria:**
- Both kinds persist with tags and overrides
- Null `end_date` renders as current
- Migration applies and reverses cleanly

### P1.T5.S2: Define Pydantic schemas

**Description:** Create request and response schemas — the public shape, the admin shape, and create/update payloads.

**Implementation Hints:** `schemas.py` — `TimelineEntryPublic` (no status or internal fields), `TimelineEntryAdmin` (everything), `TimelineEntryCreate`, `TimelineEntryUpdate` (all optional for PATCH). Pydantic v2 with `model_config = ConfigDict(from_attributes=True)`. **Never return the admin schema from a public endpoint** — that is how draft status and internal notes leak. Validate `end_date >= start_date` with a model validator.

**Dependencies:** P1.T5.S1
**Effort:** M / 3 hrs
**Acceptance Criteria:**
- Public responses omit status, `publish_at` and overrides
- Invalid date ranges return 422 with a clear message

### P1.T5.S3: Implement service and repository layers

**Description:** Build the query and business logic, keeping routers thin. This separation is what makes the pattern copyable.

**Implementation Hints:** `repository.py` for queries (`list_public()` applying `public_filter`, `list_admin()`, `get()`, `create()`, `update()`, `delete()`), `service.py` for orchestration (validation, revalidation triggers, tag attachment). Use `selectinload(TimelineEntry.topic_tags)` on list queries to avoid N+1. Order by `start_date DESC` with `sort_order` as tiebreak.

**Dependencies:** P1.T5.S2, P1.T4.S2
**Effort:** M / 4 hrs
**Risk Flags:** Without eager loading, a 30-entry timeline issues 31 queries. Assert query count in a test.
**Acceptance Criteria:**
- List endpoint issues a constant number of queries regardless of entry count
- Service triggers revalidation after mutations
- Repository never imports FastAPI

### P1.T5.S4: Build public and admin routers

**Description:** Expose the endpoints, with the admin router protected by `require_admin()`.

**Implementation Hints:** `router.py` with two `APIRouter` instances — `/api/v1/timeline` (public, read-only) and `/api/v1/admin/timeline` (full CRUD, `dependencies=[Depends(require_admin)]` at router level, not per endpoint, so a new endpoint cannot be added unprotected by omission). Register both in `create_app()`.

**Dependencies:** P1.T5.S3, P1.T2.S4
**Effort:** S / 2 hrs
**Risk Flags:** Router-level auth is deliberate. Per-endpoint decorators are one forgotten line away from a public admin endpoint.
**Acceptance Criteria:**
- Public list returns only published entries without auth
- Every admin endpoint returns 401 without a session
- OpenAPI schema generates cleanly

### P1.T5.S5: Test the slice

**Description:** Cover the timeline feature end-to-end at the API level, establishing the test template Phase 2 copies.

**Implementation Hints:** `httpx.AsyncClient` against the app with a Postgres test database. Cover: public list excludes drafts; admin list includes them; create triggers revalidation (mock the webhook, not the database); relevance resolution across audiences; scheduled entry appears after the cron runs. Add the entry to `models_registry.py` and confirm autogenerate sees it.

**Dependencies:** P1.T5.S4
**Effort:** M / 4 hrs
**Acceptance Criteria:**
- Full CRUD covered with auth assertions
- Draft-leak test present and passing
- Suite runs in CI against a Postgres service container

---

## Task P1.T6: Frontend Shell & Contract Tooling

**Feature:** F7, F9 · **Effort:** L / 2 days · **Dependencies:** P1.T5.S4 · **Risk:** High

### P1.T6.S1: Wire OpenAPI type generation

**Description:** Generate TypeScript types from the FastAPI schema into both frontends, closing gap G7.

**Implementation Hints:** Add a backend script exporting `openapi.json` to a **committed file**, then run `openapi-typescript` against that file in `frontend/` and `admin/`. Generating from a file rather than a running server means the CI drift check (P0.T6.S3) needs no live backend — meaningfully simpler and faster. `npm run openapi:generate` in both apps, mirroring the pattern from your jobs-tracker repo.

**Dependencies:** P1.T5.S4
**Effort:** M / 3 hrs
**Acceptance Criteria:**
- Types generate into both apps
- Changing a Pydantic schema without regenerating fails CI
- No hand-written API response types remain

### P1.T6.S2: Implement the category cookie and context

**Description:** Build category state as a cookie plus a React context, with the client-side resolution model established in the architectural decision above.

**Implementation Hints:** Cookie `portfolio_category`, one year, `SameSite=Lax`, **not** `HttpOnly` — the client must read it. A `CategoryProvider` client component in the root layout reads it on mount and exposes `{category, setCategory, clear}`. Support the `?for=recruiters` parameter as an override that also writes the cookie, giving shareable pre-filtered links. **Do not call `cookies()` in a server component on any content page** — it opts the route into dynamic rendering and forfeits ISR. This is the invariant.

**Dependencies:** P0.T3.S5
**Effort:** M / 4 hrs
**Risk Flags:** The failure is silent: reading the cookie server-side works perfectly in development and quietly disables static generation everywhere. Add a build-output check that content routes are marked static.
**Acceptance Criteria:**
- Category persists across sessions and navigation
- `?for=` sets category and writes the cookie
- `next build` reports content routes as static, not dynamic

### P1.T6.S3: Port the relevance resolver to the client

**Description:** Implement the same pure resolution function in TypeScript so the client applies highlight and dim.

**Implementation Hints:** `lib/relevance.ts` mirroring `is_relevant` exactly. Consumes the tag map from P1.T3.S3, shipped in the page payload. Because both sides are pure functions over plain data, they are directly comparable — add a shared fixture asserting identical output for the same inputs, so drift between the two implementations surfaces as a failing test rather than as a page that highlights the wrong things.

**Dependencies:** P1.T3.S3, P1.T6.S2
**Effort:** M / 3 hrs
**Risk Flags:** Two implementations of one rule will diverge unless something checks. The shared fixture is that check.
**Acceptance Criteria:**
- Client output matches server output on a shared fixture set
- Highlight applies within one frame of hydration

### P1.T6.S4: Establish the data fetching and caching layer

**Description:** Set up server-side fetching with cache tags aligned to the revalidation webhook.

**Implementation Hints:** `lib/api.ts` wrapping `fetch` with `next: { tags: ['timeline'], revalidate: 3600 }`. Tag names must match exactly what the backend sends — mismatched tags mean revalidation silently does nothing. Define them as shared constants generated from one source rather than typed as string literals in two places.

**Dependencies:** P1.T6.S1, P1.T4.S1
**Effort:** M / 3 hrs
**Risk Flags:** A tag typo produces a site that appears to work but never updates — and looks exactly like a caching problem.
**Acceptance Criteria:**
- Timeline data fetched server-side with correct tags
- Admin edit surfaces publicly within seconds
- Tag constants are shared, not duplicated string literals

---

## Task P1.T7: Timeline Public Experience & Tile Contract

**Feature:** F13, F21 (partial) · **Effort:** XL / 3–4 days · **Dependencies:** P1.T6 · **Risk:** Medium

Per `dependency-map.md` §8, the tile contract is established here rather than in Phase 3 — turning F21's ten hard dependencies into soft ones.

### P1.T7.S1: Build the timeline page

**Description:** Render the unified chronological timeline as a server component with highlight and dim applied client-side.

**Implementation Hints:** `app/timeline/page.tsx` as an RSC fetching entries and the tag map, passing both to a client component that applies relevance. Vertical chronological layout, education and experience interleaved by date with visual distinction by kind. Markdown summaries via `react-markdown` with `rehype-sanitize`. Dimmed entries drop opacity and lose visual weight but remain fully readable and selectable — everyone sees everything, only emphasis changes.

**Dependencies:** P1.T6.S3, P1.T6.S4
**Effort:** L / 1–2 days
**Risk Flags:** Dimming must not reduce contrast below WCAG AA. A dimmed entry is still content someone may want to read.
**Acceptance Criteria:**
- `curl` returns all entries in server HTML
- Switching category changes highlighting with no navigation
- Dimmed text meets AA contrast

### P1.T7.S2: Implement filter chips

**Description:** Add the interactive topic filter chips from PDF Feature 5, filtering the timeline by tag independently of audience highlighting.

**Implementation Hints:** Client-side filtering over already-loaded data — no refetch. Multi-select with OR semantics within the set. Reflect state in the URL (`?tags=education,consulting`) for shareability, but keep `rel="canonical"` pointing at the bare path so filtered views don't fragment indexing.

**Dependencies:** P1.T7.S1
**Effort:** M / 4 hrs
**Risk Flags:** Filtering and audience highlighting are independent axes and will be confused if presented similarly. Make them visually distinct.
**Acceptance Criteria:**
- Selecting chips filters entries instantly
- URL reflects selection; canonical stays bare
- Clearing restores all entries

### P1.T7.S3: Build the OverviewIntro model and default row

**Description:** Implement the per-audience overview header — the most-read copy on the site.

**Implementation Hints:** Feature slice `app/features/overview/`. `OverviewIntro`: `audience` (unique, including a `default` row), `headline`, `body` (markdown), `hero_image_key`, `cta_label`, `cta_url`. Seed all six rows in a migration so the page is never empty. Server-render the `default` row into HTML; ship all six in the payload; swap client-side on hydration per the architectural decision.

**Dependencies:** P1.T1.S4, P1.T5.S3
**Effort:** M / 4 hrs
**Risk Flags:** A missing `default` row means crawlers and first-time visitors get an empty header. Enforce its existence at the database level or in the seed.
**Acceptance Criteria:**
- Six rows present after migration
- `curl` on `/` returns the default headline and body
- Returning visitors see their audience variant after hydration

### P1.T7.S4: Define the tile contract and render the timeline tile

**Description:** Establish the tile interface every Phase 2 content feature implements, and prove it with the first tile.

**Implementation Hints:** A `Tile` interface — `id`, `title`, `summary`, `href`, `audiences` (which audiences see it), `priority` (ordering), `isEmpty` (omit when the feature has no content). Grid layout as in the GRIDZ reference: `OverviewIntro` full-width at top, tiles below. **Omission, not dimming** — a tile irrelevant to the current audience is absent, unlike Timeline entries which dim. Document the contract in `docs/conventions.md`; each Phase 2 feature contributes its tile as the final sub-task of its own track.

**Dependencies:** P1.T7.S3
**Effort:** L / 1 day
**Risk Flags:** This contract determines whether Phase 2's tracks stay independent. If it is under-specified, nine features will each extend it differently and F21 becomes the big-bang integration §8 exists to prevent.
**Acceptance Criteria:**
- Timeline tile renders with latest-entry summary
- Tile disappears entirely when no published entries exist
- Contract documented with a worked example

### P1.T7.S5: Build the persistent HUD

**Description:** Implement the compact category switcher and scroll indicator, enabling instant context switching from any page.

**Implementation Hints:** Fixed bottom-right, in the root layout so it persists across navigation. Compact selector plus scroll percentage. Switching is **instant — no animation, no navigation** — it updates context, which re-runs client-side relevance. Include a "show everything" reset returning to the default view. The audio control mounts here in Phase 2; leave the slot.

**Dependencies:** P1.T6.S2, P1.T7.S1
**Effort:** M / 4 hrs
**Risk Flags:** The intro animation plays once per session and must never replay on switch. Guard it explicitly.
**Acceptance Criteria:**
- HUD persists across all pages
- Switching re-highlights instantly without navigation or animation
- Reset restores the unfiltered default view

---

## Task P1.T8: Admin Shell & Timeline CRUD

**Feature:** F10 · **Effort:** L / 2–3 days · **Dependencies:** P1.T2, P1.T5 · **Risk:** Low

### P1.T8.S1: Build the login flow

**Description:** Implement the two-step password-then-OTP login UI.

**Implementation Hints:** React Router routes `/login` and `/login/verify`. Password step posts and, on success, advances to OTP entry. Show remaining attempts and expiry countdown — an OTP screen with no feedback is where people get locked out of their own portal. Handle 429 with a clear "too many attempts, wait N minutes" rather than a generic error.

**Dependencies:** P1.T2.S4
**Effort:** M / 4 hrs
**Acceptance Criteria:**
- Correct password then correct OTP grants access
- Expired OTP shows a specific message with a resend option
- Rate limiting surfaces a clear wait time

### P1.T8.S2: Implement the auth guard and layout

**Description:** Ensure no admin route renders without a valid session, and build the shell every CRUD screen sits inside.

**Implementation Hints:** A route wrapper checking session via a `/api/v1/admin/me` call, redirecting to `/login` on 401. TanStack Query with a global 401 handler so any expired-session response redirects rather than surfacing an error toast per request. Sidebar navigation, content area, toast notifications.

**Dependencies:** P1.T8.S1
**Effort:** M / 4 hrs
**Risk Flags:** Client-side guards are UX, not security — the API is the real boundary. Never let a guard imply an endpoint needn't be protected.
**Acceptance Criteria:**
- Direct navigation to any admin route without a session redirects to login
- Session expiry mid-session redirects cleanly

### P1.T8.S3: Build Timeline CRUD screens

**Description:** Implement the list, create and edit screens — the template Phase 2 copies nine times.

**Implementation Hints:** List with status badges and kind filter. Form with all fields, tag multi-select, audience override checkboxes, status selector revealing a `publish_at` picker when Scheduled is chosen, and a markdown editor with preview. Optimistic updates via TanStack Query mutations. Because nine features will copy this, factor the reusable pieces — `TagSelect`, `AudienceOverrideSelect`, `PublishStatusField`, `MarkdownField` — into shared components now rather than after the third copy.

**Dependencies:** P1.T8.S2, P1.T5.S4
**Effort:** L / 1–2 days
**Risk Flags:** The shared-component extraction is the highest-leverage decision in this task. Skipping it means nine copies of a status selector that then need nine edits.
**Acceptance Criteria:**
- Full CRUD works with validation errors surfaced inline
- Scheduled entries accept a future `publish_at`
- Saving triggers revalidation and the public page updates
- Shared field components live in `admin/src/components/fields/`

### P1.T8.S4: Build the audience-tag mapping matrix

**Description:** Implement the screen for editing which topic tags make content relevant to each audience.

**Implementation Hints:** A checkbox grid — audiences as columns, topic tags as rows. Batch save rather than per-cell requests. Include tag management (create, rename, delete) on the same screen, with delete blocked when a tag is in use rather than cascading silently.

**Dependencies:** P1.T8.S2, P1.T3.S3
**Effort:** M / 4 hrs
**Risk Flags:** A cascading tag delete would silently unhighlight content across the whole site with no record of what changed.
**Acceptance Criteria:**
- Matrix loads current mapping and saves changes in one request
- Deleting an in-use tag is blocked with a clear message
- Saving invalidates the cached map endpoint

---

## Phase 1 Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| `cookies()` in a server component silently disables ISR | High | **Critical** | Stated invariant; build-output check in P1.T6.S2 |
| Revalidation tag mismatch — site never updates | Medium | High | Shared tag constants (P1.T6.S4) |
| Draft content leaks to a public endpoint | Medium | **Critical** | `public_filter` as the only sanctioned path; reusable leak test |
| Server and client relevance implementations diverge | Medium | Medium | Shared fixture asserting parity (P1.T6.S3) |
| Admin CRUD not factored before Phase 2 copies it | High | Medium | Shared field components mandated in P1.T8.S3 |
| Tile contract under-specified | Medium | High | Documented with worked example (P1.T7.S4) |
| OTP lockout with no recovery path | Low | High | Attempt feedback, resend, rate-limit messaging |
| N+1 queries on timeline list | Medium | Low | Eager loading plus query-count assertion |

---

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
