# Graph Report - Portfolio  (2026-09-02)

## Corpus Check
- 514 files · ~314,950 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 4383 nodes · 7927 edges · 345 communities (303 shown, 42 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 222 edges (avg confidence: 0.53)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `6501c1d2`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Settings
- overview/endpoints/router.py
- forms/endpoints/router.py
- Audience
- public_filter
- apiFetch
- projects/service.py
- posts/service.py
- app/page.tsx
- certifications/service.py
- test_crawlers.py
- Development Plan — Phase 0: Foundations
- Development Plan — Phase 0: Foundations
- react
- resumes/endpoints/router.py
- ProjectList.tsx
- contact/endpoints/router.py
- skills/endpoints/router.py
- Development Plan — Phase 2: Parallel Replication
- Development Plan — Phase 2: Parallel Replication
- Development Plan — Phase 3: Integration, Discoverability & Launch
- Development Plan — Phase 3: Integration, Discoverability & Launch
- test_storage.py
- 4. Gaps Identified
- 4. Gaps Identified
- IntroOverlay.tsx
- HANDOFF — Session 3 (P0 design + P2 content tracks A–F)
- test_static_mount.py
- CollectionsForm.tsx
- apiFetch
- conftest.py
- FakeAsyncClient
- CategoryProvider.tsx
- card.tsx
- collections/endpoints/router.py
- compilerOptions
- get_settings
- UI Design Brief — Audience-Segmented Portfolio
- app.py
- package.json
- Invariants
- compilerOptions
- What You Must Do When Invoked
- What You Must Do When Invoked
- What You Must Do When Invoked
- auth/endpoints/router.py
- relevance/service.py
- timeline/endpoints/router.py
- devDependencies
- test_projects.py
- PublishStatus
- admin/components.json
- frontend/components.json
- test_relevance.py
- test_timeline.py
- dependencies
- A11y & Performance Audit Report
- compilerOptions
- HANDOFF — Session 2 (P1 Wave 6 completion through GATE-P1)
- HANDOFF — Session 4 (P3 convergence: TD-31 → TD-36)
- test_posts.py
- Dependency Map — Audience-Segmented Portfolio Platform
- Dependency Map — Audience-Segmented Portfolio Platform
- §2 Runbook (phases 1–10)
- test_prose.py
- test_auth.py
- Waves & To-Do index
- DESIGN.md — Portfolio Dark Theme (Refined)
- dependencies
- devDependencies
- Railway Infra Bootstrap — Session Handoff
- skills/page.tsx
- database.py
- Railway configuration
- 2. Gaps vs. existing models/admin/frontend
- HANDOFF — Session 1 (P0 foundations + P1 backend spine through TD-19)
- [id]/page.tsx
- src/components/ui/button.tsx
- clsx
- email.py
- Content Authoring Checklist (TD-36 / P3.T6.S6)
- thesis/endpoints/router.py
- test_change_password.py
- CertsClient.tsx
- auth/service.py
- test_core_models.py
- Post-Development Report — Initial Build-Out (Phases P0–P3)
- Global Constraints
- projects/[slug]/page.tsx
- TD-M1: Verify Cloudflare Zone Active + Renewal/WHOIS Record
- TD-M2: R2 Bucket + Turnstile Widget + Web Analytics
- TD-M3: Resend Domain Verification — SPF/DKIM/DMARC
- TD-M5: Railway Auto-Deploy OFF + RAILWAY_TOKEN Env Secret
- TD-19: Publishing & Revalidation — Route, Triggers, Scheduler Cron, public_filter Enforcement
- TD-21: Frontend Shell & Contract Tooling — Typegen, Category Cookie, Relevance Parity, Fetch Layer
- TD-23: Admin Shell & Timeline CRUD — Login, Guard, CRUD Screens, Tag-Map Matrix
- scripts
- .oxlintrc.json
- Design — portfolio-sid-v2 Clean Railway Deployment
- revalidate
- TD-00: Repo Init + Git Hygiene + Secrets Guardrails
- TD-01: Agent Tooling — Graphify, CodeGraph, Superpowers
- TD-02: Canonical Docs Set + Conventions + Pointer Files
- TD-03: Backend Scaffold — uv + FastAPI Factory + core/
- TD-04: Next.js Scaffold + Overlay Invariant + noindex Default
- TD-05: Admin SPA Scaffold (Vite + React + TS)
- TD-06: Docker Compose — Postgres 16 + MinIO + Bucket Init
- TD-07: Async Alembic + Models Registry
- TD-08: StorageAdapter — R2/MinIO, Content-Hashed Keys
- TD-09: Multi-Stage Backend Dockerfile (Admin + API, One Container)
- TD-10: Stitch MCP (Env Expansion) + DESIGN.md Export
- TD-11: Design Tokens → Tailwind/shadcn in Both Apps
- TD-12: CI — Lint/Typecheck + Unit Tests (Codegraph-Scoped)
- TD-13: CI — OpenAPI Drift + Alembic Single-Head
- TD-14: react-doctor (Baseline + PR Gate) + Playwright E2E + SSR Check
- TD-15: Deploy Workflow + Production Environment Approval
- TD-M4: Railway — Postgres + Backend/Frontend/Cron Services
- TD-M6: Cloudflare Tunnel + Access (Env-Gated, Single Hostname)
- TD-16: Core Data Foundations — Base/Mixins, Audience, TopicTag, Publishable, Registry + Migration
- TD-17: Admin Auth & Anti-Abuse — Argon2, OTP, Resend, Session, Lockout, Access JWT
- TD-18: Relevance Engine — Map Table, Pure Resolver, Map Endpoint, Postgres Tests
- TD-20: Timeline Backend Slice — Model → Schemas → Repository/Service → Routers → Tests
- TD-22: Timeline Public Experience — Page, Filter Chips, OverviewIntro, Tile Contract, HUD
- TD-24: Contention Protocol — Regen Script, Registry Checks, Merge Rules
- TD-25: Track A — Projects (Critical Path, Merges First)
- TD-26: Track B — Skills + Certifications
- TD-27: Track C — Investment Thesis + Posts
- TD-28: Track D — Collections + Prose Pages
- TD-29: Track E — Resume + Forms
- TD-30: Track F — Intro Sequence + Ambient Audio
- TD-31: Overview Completion — Arrangement, Pinning, Empty States, Hero
- TD-32: SEO & Discoverability — JSON-LD, Sitemap/Robots, Canonical, llms.txt, SSR Suite
- TD-33: Crawler Analytics — Beacon, CrawlerHit, Admin Panel
- TD-34: Design Pass & Re-skin — Stitch Tokens, Leak Audit, Visual Regression
- TD-35: Accessibility & Performance — AA, Keyboard/SR, CWV, react-doctor
- TD-36: Launch — Cutover, Access, Sentry, Restore Drill, Journeys, Content
- S2_T03 — Documentation Restructure & Cleanup
- S2_T05 — CI Pipeline: Quality Gates + Contract Checks
- S2_T07 — Docstrings (Public API Surface) + Per-Feature Documentation
- S2_T09 — Session Handoff + Registry Updates
- Handoff — Admin Private + Build Failures (next session)
- graphify reference: extra exports and benchmark
- graphify reference: extra exports and benchmark
- Env Vars Registry
- S2_T02 — Commit Uncommitted P3 Work + Credential Hygiene
- S2_T04 — GATE-P2 Formal Verification
- S2_T06 — CI: E2E Journeys, react-doctor Gate, Deploy Workflow
- S2_T08 — Post-Development Documentation (Session-2 Tasks)
- contact/page.tsx
- graphify reference: extra exports and benchmark
- ThesisForm.tsx
- cf9af7fc8db5_relevance_audience_tag_map.py
- Task P1.T2: Admin Authentication & Anti-Abuse
- GATE-P1: Phase 1 Exit Gate
- Task P1.T2: Admin Authentication & Anti-Abuse
- Auth — password + email OTP sign-in for the single admin
- Certifications — Issued credentials with kind split and R2-backed files
- Collections — Books, anime, and manhwa with a download-once R2 cover pipeline
- Forms — public contact and dealflow intake behind layered anti-abuse
- Overview — per-audience homepage intro rows
- Posts — External writing links routed to themed pages by collection
- Projects — Portfolio projects with file attachments and timeline cross-links
- Prose — Markdown pages organized by an explicit editorial group enum
- Relevance — audience-to-topic-tag map powering per-audience content filtering
- Skills — Flat ordered skill inventory, always publicly visible
- Thesis — Investment thesis entries linking out to Google Drive documents
- Timeline — unified education and experience entries with publish lifecycle
- Manual Checklists (user-executed To-Dos)
- 4. Per-task detail (each tags every document to consult)
- dealflow/page.tsx
- 2. Remaining tasks (priority order — do not reorder, pause for User where noted)
- 4fc2a3dab90d_overview_intro_model_and_seeds.py
- posts/endpoints/router.py
- Postgres Backup & Restore Procedure (TD-36 / gap G12)
- Spec Catalog — Session 1 (Initial Build-Out, Phases P0–P3)
- S2_T01 — Baseline Verification of Uncommitted P3 Work
- check_registries.py
- scripts
- admin/src/api.d.ts
- graphify reference: query, path, explain
- graphify reference: query, path, explain
- Development Plan — Phase 1: The Vertical Spine
- Task P1.T5: Timeline Backend Slice
- Task P1.T7: Timeline Public Experience & Tile Contract
- Development Plan — Phase 1: The Vertical Spine
- Task P1.T5: Timeline Backend Slice
- Task P1.T7: Timeline Public Experience & Tile Contract
- frontend/src/api.d.ts
- graphify reference: query, path, explain
- check_ssr.sh
- admin/package.json
- admin/tsconfig.json
- Task P1.T1: Core Data Foundations
- Task P1.T3: Relevance Engine
- Task P1.T4: Publishing Workflow & Revalidation
- Task P1.T6: Frontend Shell & Contract Tooling
- Task P1.T8: Admin Shell & Timeline CRUD
- GATE-P3: Phase 3 Exit Gate — Launch
- Task P1.T1: Core Data Foundations
- Task P1.T3: Relevance Engine
- Task P1.T4: Publishing Workflow & Revalidation
- Task P1.T6: Frontend Shell & Contract Tooling
- Task P1.T8: Admin Shell & Timeline CRUD
- GATE-P2 Verification Evidence
- frontend/components/ui/button.tsx
- React + TypeScript + Vite
- AGENTS.md
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native CLAUDE.md integration
- graphify reference: incremental update and cluster-only
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native CLAUDE.md integration
- graphify reference: incremental update and cluster-only
- GATE-P0: Phase 0 Exit Checklist
- GATE-P2 — Phase 2 Exit Gate
- frontend/README.md
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native CLAUDE.md integration
- graphify reference: incremental update and cluster-only
- .__table_args__
- Execution model (sub-agent dispatch)
- CLAUDE.md
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- revalidate/route.ts
- next.config.ts
- graphify.js
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- React Doctor
- layout.tsx
- resumes/service.py
- react-dom
- react-router-dom
- @tanstack/react-query
- features/__init__.py
- relevance/endpoints/__init__.py
- relevance/tests/__init__.py
- .claude/CLAUDE.md
- .claude/skills/graphify/references/extraction-spec.md
- .codex/skills/graphify/references/extraction-spec.md
- handoff/README.md
- framer-motion
- frontend/AGENTS.md
- eslint.config.mjs
- clsx
- next
- react-dom
- react-markdown
- vitest
- postcss.config.mjs
- a11y.spec.ts
- home.spec.ts
- .mcp.json
- .opencode/skills/graphify/references/extraction-spec.md
- regen_migration.sh
- portfolio-backend
- React Doctor
- 3. Per-task plan (agent vs user, pause points, verify)
- React Doctor
- 2. Proposed design — Timeline Detail Page (Option 2)
- LOCAL.md — Run the whole stack without any cloud secrets
- test_seed_resumes.py
- DbSession
- Handoff — Cloudflare Removal & Revised Launch Plan
- _classify_agent
- HANDOFF — Session 5 (Engagement Session 2: Rescue, CI, Docs Architecture)
- Post-Development Recap — 2026-08-30 (Resume Canon + Timeline Detail + pgBouncer)
- LOCAL-01: Local Dev Runbook + Smoke Test
- relevance/repository.py
- env.py
- Crawlers — AI-crawler hit analytics without storing IP addresses
- Resumes — audience-variant resume registry over object storage keys
- React Doctor Baseline
- Plan — Email Provider Abstraction (Deferred, Keep Resend)
- Post-Development — Timeline Detail + Reverse Project Linking (Option 2)
- test_scheduler.py
- Session Prompt — Railway Infra & Hosting (Cloudflare-removal follow-up)
- S2_T07 — Docstrings & Feature Docs Post-Development
- Post-Development — Resume Consolidation (2026-08-30)
- anime-manga/page.tsx
- S2_T05 / S2_T06 — CI Pipeline Post-Development
- Session-2 Summary — What Shipped
- src/lib/api.ts
- 869fc8d8c856_widen_resume_variant_to_string.py
- DEPLOYMENT.md — Architecture, Runbook & Troubleshooting
- @fontsource-variable/geist
- features/README.md
- doctor.config.ts
- replace_map
- test_skills.py
- CertsForm.tsx
- Handoff — Steady State (2026-09-03)
- POST-DEPLOYMENT — portfolio-sid-v2
- cc8619b8d037_contact_profile_model_and_default_seed.py
- lucide-react
- tileArrangement.ts
- clean_relevance_tables

## God Nodes (most connected - your core abstractions)
1. `Settings` - 97 edges
2. `apiFetch()` - 63 edges
3. `Audience` - 63 edges
4. `revalidate()` - 60 edges
5. `Base` - 56 edges
6. `TopicTag` - 55 edges
7. `UUIDMixin` - 53 edges
8. `TimestampMixin` - 53 edges
9. `react` - 50 edges
10. `PublishStatus` - 50 edges

## Surprising Connections (you probably didn't know these)
- `create_app()` --indirect_call--> `crawler_middleware()`  [INFERRED]
  backend/app/app.py → backend/app/features/crawlers/middleware.py
- `test_duplicate_audience_tag_pair_rejected()` --calls--> `session_factory()`  [INFERRED]
  backend/app/features/relevance/tests/test_relevance.py → backend/app/conftest.py
- `_seed_all_states()` --calls--> `session_factory()`  [INFERRED]
  backend/app/tests/test_scheduler.py → backend/app/conftest.py
- `test_scheduler_promotes_due_entries_only()` --calls--> `session_factory()`  [INFERRED]
  backend/app/tests/test_scheduler.py → backend/app/conftest.py
- `_write_hit()` --indirect_call--> `session()`  [INFERRED]
  backend/app/features/crawlers/middleware.py → backend/app/conftest.py

## Import Cycles
- None detected.

## Communities (345 total, 42 thin omitted)

### Community 0 - "Settings"
Cohesion: 0.11
Nodes (25): field_validator, Settings, build_engine(), AsyncEngine, Create the async engine from ``settings``. See module docstring for…, MonkeyPatch, PgBouncer pool-tuning regression tests (no DB required). Verifies ``Settings``…, The module-level engine in app.core.database respects Settings tuning. (+17 more)

### Community 1 - "overview/endpoints/router.py"
Cohesion: 0.08
Nodes (60): create(), delete(), get_admin(), get_public(), list_admin(), list_public(), DbSession, delete (+52 more)

### Community 2 - "forms/endpoints/router.py"
Cohesion: 0.08
Nodes (55): _check_rate_limit(), export_csv(), get_admin(), list_admin(), AsyncSession, DbSession, get, patch (+47 more)

### Community 3 - "Audience"
Cohesion: 0.10
Nodes (62): Audience, Shared enums. ``DEFAULT_AUDIENCE`` is a Python-only sentinel for the…, Base, PublishableMixin, Declarative base, shared mixins, and core models. Every feature slice imports…, UUID primary key. Never a string column (index efficiency, rejects malformed…, UTC timestamps (stored timezone-aware, rendered viewer-local)., Manual ordering for lists (Books, Skills, Certifications...). (+54 more)

### Community 4 - "public_filter"
Cohesion: 0.10
Nodes (49): public_filter(), Any, Published rows, plus scheduled rows whose ``publish_at`` has passed., create(), delete(), get_admin(), get_by_slug(), list_admin() (+41 more)

### Community 5 - "apiFetch"
Cohesion: 0.06
Nodes (40): BooksClient(), Item, SECTION_CONFIG, Item, metadata, Cert, metadata, HowIUseAiPage() (+32 more)

### Community 6 - "projects/service.py"
Cohesion: 0.09
Nodes (51): create(), delete(), get_admin(), get_public(), list_admin(), list_public(), DbSession, delete (+43 more)

### Community 7 - "posts/service.py"
Cohesion: 0.21
Nodes (25): PostCollection, create(), delete(), get(), list_admin(), list_by_collection(), list_public(), AsyncSession (+17 more)

### Community 8 - "app/page.tsx"
Cohesion: 0.08
Nodes (38): Cert, CollectionItem, Entry, Home(), Intro, metadata, PostItem, ProjectItem (+30 more)

### Community 9 - "certifications/service.py"
Cohesion: 0.11
Nodes (43): create(), delete(), get_admin(), get_public(), list_admin(), list_public(), DbSession, delete (+35 more)

### Community 10 - "test_crawlers.py"
Cohesion: 0.16
Nodes (19): crawler_middleware(), _hash_ip(), async_sessionmaker, AsyncSession, Request, Response, FastAPI middleware: log AI crawler visits as fire-and-forget records. Never…, _write_hit() (+11 more)

### Community 11 - "Development Plan — Phase 0: Foundations"
Cohesion: 0.04
Nodes (47): Development Plan — Phase 0: Foundations, Exit Checklist, P0.T1.S1: Register the domain, P0.T1.S2: Delegate nameservers to Cloudflare, P0.T1.S3: Provision R2 bucket and API credentials, P0.T1.S4: Configure Turnstile widget, P0.T1.S5: Enable Cloudflare Web Analytics, P0.T1.S6: Verify the Resend sending domain (+39 more)

### Community 12 - "Development Plan — Phase 0: Foundations"
Cohesion: 0.04
Nodes (47): Development Plan — Phase 0: Foundations, Exit Checklist, P0.T1.S1: Register the domain, P0.T1.S2: Delegate nameservers to Cloudflare, P0.T1.S3: Provision R2 bucket and API credentials, P0.T1.S4: Configure Turnstile widget, P0.T1.S5: Enable Cloudflare Web Analytics, P0.T1.S6: Verify the Resend sending domain (+39 more)

### Community 13 - "react"
Cohesion: 0.08
Nodes (57): AudienceOverrideSelect(), AudienceOverrideSelectProps, AUDIENCES, COLLECTIONS, CollectionsSelect(), CollectionsSelectProps, MarkdownField(), MarkdownFieldProps (+49 more)

### Community 14 - "resumes/endpoints/router.py"
Cohesion: 0.16
Nodes (20): create(), delete(), get_admin(), list_admin(), list_public(), DbSession, delete, get (+12 more)

### Community 15 - "ProjectList.tsx"
Cohesion: 0.40
Nodes (4): statusColors, AttachmentRef, Project, TagRef

### Community 16 - "contact/endpoints/router.py"
Cohesion: 0.15
Nodes (22): get_admin(), get_public(), DbSession, get, put, ContactProfile routers: public read-only, admin get/update singleton., update(), get() (+14 more)

### Community 17 - "skills/endpoints/router.py"
Cohesion: 0.12
Nodes (38): create(), delete(), get_admin(), list_admin(), list_public(), DbSession, delete, get (+30 more)

### Community 18 - "Development Plan — Phase 2: Parallel Replication"
Cohesion: 0.05
Nodes (40): A.T1: Model projects with experience linkage and media, A.T2: Build API, service and admin CRUD, A.T3: Build the public projects page, A.T4: Register the projects tile, B.T1: Model and build skills, B.T2: Skills API, page and admin, B.T3: Model and build certifications, B.T4: Certifications page with expand-to-view (+32 more)

### Community 19 - "Development Plan — Phase 2: Parallel Replication"
Cohesion: 0.05
Nodes (40): A.T1: Model projects with experience linkage and media, A.T2: Build API, service and admin CRUD, A.T3: Build the public projects page, A.T4: Register the projects tile, B.T1: Model and build skills, B.T2: Skills API, page and admin, B.T3: Model and build certifications, B.T4: Certifications page with expand-to-view (+32 more)

### Community 20 - "Development Plan — Phase 3: Integration, Discoverability & Launch"
Cohesion: 0.05
Nodes (39): Development Plan — Phase 3: Integration, Discoverability & Launch, Exit Checklist, P3.T1.S1: Define per-audience tile arrangement, P3.T1.S2: Implement latest-content selection and pinning, P3.T1.S3: Verify empty-state behaviour, P3.T1.S4: Add hero image support to OverviewIntro, P3.T2.S1: Generate the Person JSON-LD from live data, P3.T2.S2: Build sitemap and robots (+31 more)

### Community 21 - "Development Plan — Phase 3: Integration, Discoverability & Launch"
Cohesion: 0.05
Nodes (39): Development Plan — Phase 3: Integration, Discoverability & Launch, Exit Checklist, P3.T1.S1: Define per-audience tile arrangement, P3.T1.S2: Implement latest-content selection and pinning, P3.T1.S3: Verify empty-state behaviour, P3.T1.S4: Add hero image support to OverviewIntro, P3.T2.S1: Generate the Person JSON-LD from live data, P3.T2.S2: Build sitemap and robots (+31 more)

### Community 22 - "test_storage.py"
Cohesion: 0.05
Nodes (50): ABC, get_storage_adapter(), content_hashed_key(), get_storage(), LocalDiskStorage, Path, S3-compatible object storage (Cloudflare R2 / local MinIO) plus local-disk…, Factory selected by ``settings.storage_kind``: ``s3`` (default) or ``local``. (+42 more)

### Community 23 - "4. Gaps Identified"
Cohesion: 0.05
Nodes (36): 1. Purpose, 2.1 Application Layer, 2.2 Data & Storage, 2.3 Infrastructure & Third-Party, 2. Stack Components, 3.1 Discoverability & SEO — *the constraint that shaped the stack*, 3.2 Content Domain, 3.3 Interaction & Presentation (+28 more)

### Community 24 - "4. Gaps Identified"
Cohesion: 0.05
Nodes (36): 1. Purpose, 2.1 Application Layer, 2.2 Data & Storage, 2.3 Infrastructure & Third-Party, 2. Stack Components, 3.1 Discoverability & SEO — *the constraint that shaped the stack*, 3.2 Content Domain, 3.3 Interaction & Presentation (+28 more)

### Community 25 - "IntroOverlay.tsx"
Cohesion: 0.39
Nodes (6): CATEGORY_TILES, CategoryTile, ease, IntroPlayer(), IntroPlayerProps, WORDS

### Community 26 - "HANDOFF — Session 3 (P0 design + P2 content tracks A–F)"
Cohesion: 0.06
Nodes (33): 10. Lessons learned from errors, 1. What was done this session, 2. Overall project completion status, 3. What was developed this session (detail), 4. Deviations from existing design, 5. Documents referred, 6. What is pending, 7. Issues needing attention (first priority) (+25 more)

### Community 27 - "test_static_mount.py"
Cohesion: 0.27
Nodes (12): ASGITransport, fixture, MonkeyPatch, Path, static_app(), test_api_v1_health_still_200(), test_deep_route_returns_spa_index(), test_existing_static_file_served() (+4 more)

### Community 28 - "CollectionsForm.tsx"
Cohesion: 0.24
Nodes (9): CollectionsForm(), CoverLookupResult, emptyForm(), FormState, Item, KINDS, READ_STATUSES, SECTIONS (+1 more)

### Community 29 - "apiFetch"
Cohesion: 0.10
Nodes (30): AdminLayout(), NAV_ITEMS, AuthGuard(), apiFetch(), Certification, CertsList(), formatDate(), statusColors (+22 more)

### Community 30 - "conftest.py"
Cohesion: 0.17
Nodes (21): admin_settings(), _base_url(), clean_auth_tables(), client(), db_engine(), _ensure_test_database(), async_sessionmaker, AsyncClient (+13 more)

### Community 31 - "FakeAsyncClient"
Cohesion: 0.28
Nodes (4): FakeAsyncClient, FakeResponse, Any, Records the request; configurable status or exception.

### Community 32 - "CategoryProvider.tsx"
Cohesion: 0.08
Nodes (33): Entry, metadata, TagMapResponse, TimelinePage(), CategoryContext, CategoryProvider(), CategoryState, clearCookie() (+25 more)

### Community 33 - "card.tsx"
Cohesion: 0.26
Nodes (13): Card(), CardContent(), CardDescription(), CardFooter(), CardHeader(), CardTitle(), ApiError, ContactProfile (+5 more)

### Community 34 - "collections/endpoints/router.py"
Cohesion: 0.10
Nodes (49): cover_lookup(), create(), delete(), get_admin(), list_admin(), list_public(), DbSession, delete (+41 more)

### Community 35 - "compilerOptions"
Cohesion: 0.07
Nodes (28): compilerOptions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib, module (+20 more)

### Community 36 - "get_settings"
Cohesion: 0.17
Nodes (23): get_settings(), Application settings via pydantic-settings. Every field maps to an env var of…, clear_session_cookie(), _cookie_kwargs(), create_session_token(), Any, Response, Signed admin session cookies. ``itsdangerous.URLSafeTimedSerializer`` — one… (+15 more)

### Community 37 - "UI Design Brief — Audience-Segmented Portfolio"
Cohesion: 0.07
Nodes (27): 10. States and quality floor, 11. Stitch prompt pack, 12. What Stitch must not produce, 1. How to use this document, 2. Design thesis, 3. Fixed constraints, 4. Colour, 5. Typography (+19 more)

### Community 38 - "app.py"
Cohesion: 0.14
Nodes (19): api_v1_health(), _auth_error_handler(), create_app(), Exception, get, Request, _rate_limit_handler(), FastAPI application factory. (+11 more)

### Community 39 - "package.json"
Cohesion: 0.25
Nodes (7): description, devDependencies, railway, name, private, version, railway

### Community 40 - "Invariants"
Cohesion: 0.07
Nodes (28): 10. Relevance parity, 11. Revalidation tags are shared constants, 12. Design tokens only, 13. Noindex until launch, 14. Admin security posture, 15. Secrets, 1. Overlay, never replacement (Critical), 2. Category state lives in a cookie (+20 more)

### Community 41 - "compilerOptions"
Cohesion: 0.08
Nodes (24): compilerOptions, allowArbitraryExtensions, allowImportingTsExtensions, erasableSyntaxOnly, jsx, lib, module, moduleDetection (+16 more)

### Community 42 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 43 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 44 - "What You Must Do When Invoked"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 45 - "auth/endpoints/router.py"
Cohesion: 0.14
Nodes (22): change_password(), login(), logout(), me(), DbSession, get, post, Request (+14 more)

### Community 46 - "relevance/service.py"
Cohesion: 0.16
Nodes (21): create_tag(), patch, post, UUID, Relevance routes: public cached map, admin matrix read/replace, tag CRUD., rename_tag(), Relevance feature: audience-tag map, pure resolver, map endpoints., AdminMapUpdate (+13 more)

### Community 47 - "timeline/endpoints/router.py"
Cohesion: 0.10
Nodes (47): create(), delete(), get_admin(), get_public(), list_admin(), list_public(), list_public_projects(), DbSession (+39 more)

### Community 48 - "devDependencies"
Cohesion: 0.09
Nodes (23): @axe-core/playwright, eslint, eslint-config-next, devDependencies, @axe-core/playwright, eslint, eslint-config-next, @playwright/test (+15 more)

### Community 49 - "test_projects.py"
Cohesion: 0.22
Nodes (21): clean_projects_tables(), _login(), AsyncClient, AsyncEngine, AsyncSession, fixture, MonkeyPatch, Projects: full API suite with auth assertions, draft-leak guards, query-count… (+13 more)

### Community 50 - "PublishStatus"
Cohesion: 0.10
Nodes (34): Revalidation tag names (conventions invariant 11). One source for backend tag…, PublishStatus, Skills feature: one model grouped by section/subsection, no relevance logic.…, Skill, SkillSection, content_hash(), ensure_topic_tags(), main() (+26 more)

### Community 51 - "admin/components.json"
Cohesion: 0.09
Nodes (21): aliases, components, hooks, lib, ui, utils, iconLibrary, menuAccent (+13 more)

### Community 52 - "frontend/components.json"
Cohesion: 0.09
Nodes (21): aliases, components, hooks, lib, ui, utils, iconLibrary, menuAccent (+13 more)

### Community 53 - "test_relevance.py"
Cohesion: 0.20
Nodes (20): is_relevant(), _login(), AsyncClient, MonkeyPatch, Relevance: pure resolver unit cases + real-Postgres map persistence. Resolver…, Full auth flow with mocked email send (same pattern as test_auth)., test_admin_map_requires_session(), test_admin_put_invalid_audience_key_422() (+12 more)

### Community 54 - "test_timeline.py"
Cohesion: 0.11
Nodes (41): clean_certs_tables(), _login(), AsyncClient, AsyncEngine, AsyncSession, fixture, MonkeyPatch, Certifications: full API suite with auth, draft-leak guards, CRUD. (+33 more)

### Community 55 - "dependencies"
Cohesion: 0.10
Nodes (21): @base-ui/react, dependencies, @base-ui/react, class-variance-authority, lucide-react, react, rehype-sanitize, remark-gfm (+13 more)

### Community 56 - "A11y & Performance Audit Report"
Cohesion: 0.10
Nodes (20): 1. Payload Measurements, 2. React-Doctor Findings, 3. Contrast Hot Spots, 4. Visual Regression, 5. Recommendations, 6. Verification Commands, 7. Conclusion, A11y & Performance Audit Report (+12 more)

### Community 57 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, lib, module, moduleDetection, noEmit, noFallthroughCasesInSwitch (+11 more)

### Community 58 - "HANDOFF — Session 2 (P1 Wave 6 completion through GATE-P1)"
Cohesion: 0.10
Nodes (19): 10. Watch-list for P2/P3, 1. Snapshot, 2. What was developed (done To-Dos), 3. New capabilities summary, 4. Decisions taken this session, 5. Issues hit & resolutions (do not repeat), 6. REMAINING WORK — continue here next session, 7. File maps for quick orientation (+11 more)

### Community 59 - "HANDOFF — Session 4 (P3 convergence: TD-31 → TD-36)"
Cohesion: 0.10
Nodes (19): 1. What was done this session, 2. Overall project completion status, 3. Key architectural decisions, 4. State snapshot, 5. What is pending — NEXT SESSION, 6. New env vars, 7. Lessons from this session, 8. Execution protocol for next session (+11 more)

### Community 60 - "test_posts.py"
Cohesion: 0.23
Nodes (16): clean_posts_tables(), _login(), AsyncClient, AsyncEngine, AsyncSession, fixture, MonkeyPatch, Posts: full API suite with auth, draft-leak guards, collection routing, CRUD. (+8 more)

### Community 61 - "Dependency Map — Audience-Segmented Portfolio Platform"
Cohesion: 0.11
Nodes (18): 1. Purpose, 2. Feature Register, 3. Dependency Graph, 4. Foundation Layer, 5. Critical Path, 6. Parallelization Opportunities, 7. Shared Infrastructure, 8. Risk: The F21 Convergence (+10 more)

### Community 62 - "Dependency Map — Audience-Segmented Portfolio Platform"
Cohesion: 0.11
Nodes (18): 1. Purpose, 2. Feature Register, 3. Dependency Graph, 4. Foundation Layer, 5. Critical Path, 6. Parallelization Opportunities, 7. Shared Infrastructure, 8. Risk: The F21 Convergence (+10 more)

### Community 63 - "§2 Runbook (phases 1–10)"
Cohesion: 0.07
Nodes (29): §0 INVARIANT — this session MUST plan before executing, 1.1 Data path — ALL connections through pgbouncer, 1.2 Exposure matrix, 1.3 Volumes, 1.4 Env inventory (values harvested at §2 phase 1; placeholders only here — invariant #15), 1.5 GitHub wiring (both mechanisms — user decision), 1.6 Hard-won invariants (each one cost a real failure on 2026-08-31 — do not relearn), §1 Target system design (+21 more)

### Community 64 - "test_prose.py"
Cohesion: 0.29
Nodes (17): clean_prose(), _login(), AsyncClient, AsyncEngine, asyncio, AsyncSession, fixture, MonkeyPatch (+9 more)

### Community 65 - "test_auth.py"
Cohesion: 0.19
Nodes (26): cf_enabled(), injected_jwks(), _mock_send(), AsyncClient, AsyncSession, fixture, MonkeyPatch, Auth flow: login, OTP lifecycle, lockout, rate limit, Cloudflare Access. (+18 more)

### Community 66 - "Waves & To-Do index"
Cohesion: 0.11
Nodes (17): Card format, Execution loop (per To-Do), Fixed facts, Handoff, Parallelism & merge rules, Portfolio — Master To-Do Index, Test pyramid ownership, Wave 0 — bootstrap (+9 more)

### Community 67 - "DESIGN.md — Portfolio Dark Theme (Refined)"
Cohesion: 0.11
Nodes (17): Accessibility, Category Selector, Changelog, Colour Semantics, Colour Tokens, Component Patterns, DESIGN.md — Portfolio Dark Theme (Refined), Design Principles (+9 more)

### Community 68 - "dependencies"
Cohesion: 0.12
Nodes (17): dependencies, class-variance-authority, radix-ui, react, shadcn, tailwind-merge, tailwindcss, @tailwindcss/vite (+9 more)

### Community 69 - "devDependencies"
Cohesion: 0.12
Nodes (17): devDependencies, openapi-typescript, oxlint, @types/node, @types/react, @types/react-dom, typescript, vite (+9 more)

### Community 70 - "Railway Infra Bootstrap — Session Handoff"
Cohesion: 0.09
Nodes (22): 1. Services Created (CLI), 2. Environment Variables (CLI, `--skip-deploys`), 3. Volume, 4. Service Settings (via RAILWAY_TOKEN + GraphQL — CLI `environment edit` does NOT apply these), 5. Code Fixes Required to Deploy (all committed), 6. Verification, A. Secrets (Blocking admin login + email), B. Host Cutover (Custom Domain + DNS) (+14 more)

### Community 71 - "skills/page.tsx"
Cohesion: 0.14
Nodes (13): metadata, SECTION_CONFIG, Skill, Props, SkillIcon(), slugToUrl(), GroupedSkills, Props (+5 more)

### Community 72 - "database.py"
Cohesion: 0.11
Nodes (23): _fetch_jwks(), _get_jwks(), _jwks_url(), Request, Cloudflare Access JWT verification, gated on ``CF_ACCESS_ENABLED``. Defense in…, verify_cf_access(), get_session(), AsyncSession (+15 more)

### Community 73 - "Railway configuration"
Cohesion: 0.50
Nodes (3): Common commands, Notes, Railway configuration

### Community 74 - "2. Gaps vs. existing models/admin/frontend"
Cohesion: 0.09
Nodes (22): 11.1 Common skeleton (present in all 6 with same employer + dates, different title/bullets), 1.2 Resume-specific points (only in some PDFs — the "gaps" we must NOT drop), 1.3 Decision already visible, 1. What the 6 resumes actually contain (extracted canon), 2.1 Resume model — too narrow, 2.2 Timeline — no schema gap, but data consolidation + relevance wiring needed, 2.3 Projects — under-represented, 2.4 Skills — superset merge needed (+14 more)

### Community 75 - "HANDOFF — Session 1 (P0 foundations + P1 backend spine through TD-19)"
Cohesion: 0.13
Nodes (14): 1. Snapshot, 2. What was developed (done To-Dos), 3. Feature-based structure (ENFORCED — conventions invariant 5), 4. REMAINING P1 — continue here next session, 5. System decisions taken (explicit log), 6. Mistakes hit & resolutions (do not repeat), 7. BLOCKERS needing user action, 8. Execution protocol for the next session (+6 more)

### Community 76 - "[id]/page.tsx"
Cohesion: 0.11
Nodes (19): Props, ProsePage, ProsePageRoute(), ProseClient(), formatDate(), Project, Props, revalidate (+11 more)

### Community 77 - "src/components/ui/button.tsx"
Cohesion: 0.07
Nodes (37): Tag, TagSelect(), TagSelectProps, Badge(), Button(), buttonVariants, Item, KIND_LABELS (+29 more)

### Community 79 - "email.py"
Cohesion: 0.08
Nodes (49): EmailSendError, Exception, Email delivery via Resend. One client reused by OTP sign-in and (Phase 2) form…, Raised when an email cannot be delivered., send_email(), send_otp(), clean_collections(), _login() (+41 more)

### Community 80 - "Content Authoring Checklist (TD-36 / P3.T6.S6)"
Cohesion: 0.14
Nodes (13): Audience-tag matrix (admin → Tag Map), Certifications, Collections — books / anime / manhwa, Contact details, Content Authoring Checklist (TD-36 / P3.T6.S6), Done criteria, OverviewIntro — six rows (admin → Overview), Posts — at least a few per collection (3 collections) (+5 more)

### Community 81 - "thesis/endpoints/router.py"
Cohesion: 0.08
Nodes (56): create(), delete(), get_admin(), get_public(), list_admin(), list_public(), DbSession, delete (+48 more)

### Community 82 - "test_change_password.py"
Cohesion: 0.16
Nodes (20): main(), Admin CLI. Usage: ``uv run python -m app.cli hash-password [password]`` Prints…, hash_password(), Argon2id password hashing and verification. The admin password hash lives only…, Verified against when no admin hash is configured, so the endpoint cost is…, _timing_decoy_hash(), verify_password(), Auth feature slice: password login, hashed OTP, DB-backed lockout. (+12 more)

### Community 83 - "CertsClient.tsx"
Cohesion: 0.28
Nodes (7): Cert, CertCard(), CertsClient(), formatDate(), Props, CertViewer(), Props

### Community 85 - "auth/service.py"
Cohesion: 0.15
Nodes (22): dev_otp(), Dev-only: return the most recently issued OTP so the local e2e admin journey…, AuthError, change_password(), get_dev_last_code(), get_effective_password_hash(), _hash_code(), is_locked_out() (+14 more)

### Community 86 - "test_core_models.py"
Cohesion: 0.25
Nodes (12): Sanctioned query helpers (conventions invariant 8). ``public_filter`` is the…, AsyncSession, Core data foundations: mixins, timestamps, public_filter, TopicTag, enums., Scratch model exercising every mixin; lives only in the test DB., test_audience_enum_round_trip(), test_public_filter(), test_timestamps_auto_populate(), test_topic_tag_duplicate_slug_rejected() (+4 more)

### Community 87 - "Post-Development Report — Initial Build-Out (Phases P0–P3)"
Cohesion: 0.17
Nodes (11): Deviations & Parked Findings, Key Invariants Enforced, P0 — Foundations, P1 — Backend Spine, P2 — Content Tracks (six parallel tracks), P3 — Convergence, Post-Development Report — Initial Build-Out (Phases P0–P3), System Architecture (+3 more)

### Community 88 - "Global Constraints"
Cohesion: 0.17
Nodes (11): Global Constraints, P2 Execution Plan — Sessions 3+, Pre-dispatch checklist, Sub-agent: TD-25 (Track A — Projects), Sub-agent: TD-30 (Track F — Intro + Audio), Task 1: GitHub Authentication + Push Pending Commits, Task 2: TD-10 — Stitch MCP Verification + DESIGN.md Export, Task 3: TD-11 — Design Tokens → Tailwind/shadcn Both Apps (+3 more)

### Community 89 - "projects/[slug]/page.tsx"
Cohesion: 0.23
Nodes (10): ProjectPage(), Props, extractYouTubeId(), ProjectDetail(), Props, Props, AttachmentRef, Project (+2 more)

### Community 90 - "TD-M1: Verify Cloudflare Zone Active + Renewal/WHOIS Record"
Cohesion: 0.18
Nodes (10): Acceptance Criteria, Commit, Invariants, Paths, Purpose, Steps (agent, after user confirms), Steps (user), TD-M1: Verify Cloudflare Zone Active + Renewal/WHOIS Record (+2 more)

### Community 91 - "TD-M2: R2 Bucket + Turnstile Widget + Web Analytics"
Cohesion: 0.18
Nodes (10): Acceptance Criteria, Commit, Invariants, Paths, Purpose, Steps (agent, after user confirms), Steps (user), TD-M2: R2 Bucket + Turnstile Widget + Web Analytics (+2 more)

### Community 92 - "TD-M3: Resend Domain Verification — SPF/DKIM/DMARC"
Cohesion: 0.18
Nodes (10): Acceptance Criteria, Commit, Invariants, Paths, Purpose, Steps (agent, after user confirms), Steps (user), TD-M3: Resend Domain Verification — SPF/DKIM/DMARC (+2 more)

### Community 93 - "TD-M5: Railway Auto-Deploy OFF + RAILWAY_TOKEN Env Secret"
Cohesion: 0.18
Nodes (10): Acceptance Criteria, Commit, Invariants, Paths, Purpose, Steps (agent, after user confirms), Steps (user), TD-M5: Railway Auto-Deploy OFF + RAILWAY_TOKEN Env Secret (+2 more)

### Community 94 - "TD-19: Publishing & Revalidation — Route, Triggers, Scheduler Cron, public_filter Enforcement"
Cohesion: 0.18
Nodes (10): Acceptance Criteria, Commit, Environment, Invariants, Paths, Purpose, Steps, TD-19: Publishing & Revalidation — Route, Triggers, Scheduler Cron, public_filter Enforcement (+2 more)

### Community 95 - "TD-21: Frontend Shell & Contract Tooling — Typegen, Category Cookie, Relevance Parity, Fetch Layer"
Cohesion: 0.18
Nodes (10): Acceptance Criteria, Commit, Invariants, Notes, Paths, Purpose, Steps, TD-21: Frontend Shell & Contract Tooling — Typegen, Category Cookie, Relevance Parity, Fetch Layer (+2 more)

### Community 96 - "TD-23: Admin Shell & Timeline CRUD — Login, Guard, CRUD Screens, Tag-Map Matrix"
Cohesion: 0.18
Nodes (10): Acceptance Criteria, Commit, Invariants, Notes, Paths, Purpose, Steps, TD-23: Admin Shell & Timeline CRUD — Login, Guard, CRUD Screens, Tag-Map Matrix (+2 more)

### Community 97 - "scripts"
Cohesion: 0.18
Nodes (10): name, private, scripts, build, dev, lint, openapi:generate, start (+2 more)

### Community 98 - ".oxlintrc.json"
Cohesion: 0.20
Nodes (9): overrides, plugins, rules, react/only-export-components, react/rules-of-hooks, $schema, oxc, typescript (+1 more)

### Community 99 - "Design — portfolio-sid-v2 Clean Railway Deployment"
Cohesion: 0.12
Nodes (16): 1. Architecture, 2. Services & builds, 3. Env inventory, 4. Code changes (3 small commits, before any Railway mutation), 5. Phases (gates: record PASS/FAIL, never advance on FAIL), 6. Execution model, 7. User actions checklist (flag each when reached), 8. Decisions log (+8 more)

### Community 100 - "revalidate"
Cohesion: 0.18
Nodes (12): Post-commit cache revalidation client (conventions invariant 8). Call…, POST ``tags`` to the frontend revalidation webhook. Never raises., revalidate(), fake_httpx(), fixture, MonkeyPatch, Revalidation client: URL/header/payload contract; failures never raise., test_connection_failure_logs_error_and_does_not_raise() (+4 more)

### Community 101 - "TD-00: Repo Init + Git Hygiene + Secrets Guardrails"
Cohesion: 0.20
Nodes (9): Acceptance Criteria, Commit, Invariants, Paths, Purpose, Steps, TD-00: Repo Init + Git Hygiene + Secrets Guardrails, Tests (+1 more)

### Community 102 - "TD-01: Agent Tooling — Graphify, CodeGraph, Superpowers"
Cohesion: 0.20
Nodes (9): Acceptance Criteria, Commit, Invariants, Paths, Purpose, Steps, TD-01: Agent Tooling — Graphify, CodeGraph, Superpowers, Tests (+1 more)

### Community 103 - "TD-02: Canonical Docs Set + Conventions + Pointer Files"
Cohesion: 0.20
Nodes (9): Acceptance Criteria, Commit, Invariants, Paths, Purpose, Steps, TD-02: Canonical Docs Set + Conventions + Pointer Files, Tests (+1 more)

### Community 104 - "TD-03: Backend Scaffold — uv + FastAPI Factory + core/"
Cohesion: 0.20
Nodes (9): Acceptance Criteria, Commit, Invariants, Paths, Purpose, Steps, TD-03: Backend Scaffold — uv + FastAPI Factory + core/, Tests (+1 more)

### Community 105 - "TD-04: Next.js Scaffold + Overlay Invariant + noindex Default"
Cohesion: 0.20
Nodes (9): Acceptance Criteria, Commit, Invariants, Paths, Purpose, Steps, TD-04: Next.js Scaffold + Overlay Invariant + noindex Default, Tests (+1 more)

### Community 106 - "TD-05: Admin SPA Scaffold (Vite + React + TS)"
Cohesion: 0.20
Nodes (9): Acceptance Criteria, Commit, Invariants, Paths, Purpose, Steps, TD-05: Admin SPA Scaffold (Vite + React + TS), Tests (+1 more)

### Community 107 - "TD-06: Docker Compose — Postgres 16 + MinIO + Bucket Init"
Cohesion: 0.20
Nodes (9): Acceptance Criteria, Commit, Invariants, Paths, Purpose, Steps, TD-06: Docker Compose — Postgres 16 + MinIO + Bucket Init, Tests (+1 more)

### Community 108 - "TD-07: Async Alembic + Models Registry"
Cohesion: 0.20
Nodes (9): Acceptance Criteria, Commit, Invariants, Paths, Purpose, Steps, TD-07: Async Alembic + Models Registry, Tests (+1 more)

### Community 109 - "TD-08: StorageAdapter — R2/MinIO, Content-Hashed Keys"
Cohesion: 0.20
Nodes (9): Acceptance Criteria, Commit, Invariants, Paths, Purpose, Steps, TD-08: StorageAdapter — R2/MinIO, Content-Hashed Keys, Tests (+1 more)

### Community 110 - "TD-09: Multi-Stage Backend Dockerfile (Admin + API, One Container)"
Cohesion: 0.20
Nodes (9): Acceptance Criteria, Commit, Invariants, Paths, Purpose, Steps, TD-09: Multi-Stage Backend Dockerfile (Admin + API, One Container), Tests (+1 more)

### Community 111 - "TD-10: Stitch MCP (Env Expansion) + DESIGN.md Export"
Cohesion: 0.20
Nodes (9): Acceptance Criteria, Commit, Invariants, Paths, Purpose, Steps, TD-10: Stitch MCP (Env Expansion) + DESIGN.md Export, Tests (+1 more)

### Community 112 - "TD-11: Design Tokens → Tailwind/shadcn in Both Apps"
Cohesion: 0.20
Nodes (9): Acceptance Criteria, Commit, Invariants, Paths, Purpose, Steps, TD-11: Design Tokens → Tailwind/shadcn in Both Apps, Tests (+1 more)

### Community 113 - "TD-12: CI — Lint/Typecheck + Unit Tests (Codegraph-Scoped)"
Cohesion: 0.20
Nodes (9): Acceptance Criteria, Commit, Invariants, Paths, Purpose, Steps, TD-12: CI — Lint/Typecheck + Unit Tests (Codegraph-Scoped), Tests (+1 more)

### Community 114 - "TD-13: CI — OpenAPI Drift + Alembic Single-Head"
Cohesion: 0.20
Nodes (9): Acceptance Criteria, Commit, Invariants, Paths, Purpose, Steps, TD-13: CI — OpenAPI Drift + Alembic Single-Head, Tests (+1 more)

### Community 115 - "TD-14: react-doctor (Baseline + PR Gate) + Playwright E2E + SSR Check"
Cohesion: 0.20
Nodes (9): Acceptance Criteria, Commit, Invariants, Paths, Purpose, Steps, TD-14: react-doctor (Baseline + PR Gate) + Playwright E2E + SSR Check, Tests (+1 more)

### Community 116 - "TD-15: Deploy Workflow + Production Environment Approval"
Cohesion: 0.20
Nodes (9): Acceptance Criteria, Commit, Invariants, Paths, Purpose, Steps, TD-15: Deploy Workflow + Production Environment Approval, Tests (+1 more)

### Community 117 - "TD-M4: Railway — Postgres + Backend/Frontend/Cron Services"
Cohesion: 0.20
Nodes (9): Acceptance Criteria, Commit, Invariants, Paths, Purpose, Steps, TD-M4: Railway — Postgres + Backend/Frontend/Cron Services, Tests (+1 more)

### Community 118 - "TD-M6: Cloudflare Tunnel + Access (Env-Gated, Single Hostname)"
Cohesion: 0.20
Nodes (9): Acceptance Criteria, Commit, Invariants, Paths, Purpose, Steps, TD-M6: Cloudflare Tunnel + Access (Env-Gated, Single Hostname), Tests (+1 more)

### Community 119 - "TD-16: Core Data Foundations — Base/Mixins, Audience, TopicTag, Publishable, Registry + Migration"
Cohesion: 0.20
Nodes (9): Acceptance Criteria, Commit, Invariants, Paths, Purpose, Steps, TD-16: Core Data Foundations — Base/Mixins, Audience, TopicTag, Publishable, Registry + Migration, Tests (+1 more)

### Community 120 - "TD-17: Admin Auth & Anti-Abuse — Argon2, OTP, Resend, Session, Lockout, Access JWT"
Cohesion: 0.20
Nodes (9): Acceptance Criteria, Commit, Invariants, Paths, Purpose, Steps, TD-17: Admin Auth & Anti-Abuse — Argon2, OTP, Resend, Session, Lockout, Access JWT, Tests (+1 more)

### Community 121 - "TD-18: Relevance Engine — Map Table, Pure Resolver, Map Endpoint, Postgres Tests"
Cohesion: 0.20
Nodes (9): Acceptance Criteria, Commit, Invariants, Paths, Purpose, Steps, TD-18: Relevance Engine — Map Table, Pure Resolver, Map Endpoint, Postgres Tests, Tests (+1 more)

### Community 122 - "TD-20: Timeline Backend Slice — Model → Schemas → Repository/Service → Routers → Tests"
Cohesion: 0.20
Nodes (9): Acceptance Criteria, Commit, Invariants, Paths, Purpose, Steps, TD-20: Timeline Backend Slice — Model → Schemas → Repository/Service → Routers → Tests, Tests (+1 more)

### Community 123 - "TD-22: Timeline Public Experience — Page, Filter Chips, OverviewIntro, Tile Contract, HUD"
Cohesion: 0.20
Nodes (9): Acceptance Criteria, Commit, Invariants, Paths, Purpose, Steps, TD-22: Timeline Public Experience — Page, Filter Chips, OverviewIntro, Tile Contract, HUD, Tests (+1 more)

### Community 124 - "TD-24: Contention Protocol — Regen Script, Registry Checks, Merge Rules"
Cohesion: 0.20
Nodes (9): Acceptance Criteria, Commit, Invariants, Paths, Purpose, Steps, TD-24: Contention Protocol — Regen Script, Registry Checks, Merge Rules, Tests (+1 more)

### Community 125 - "TD-25: Track A — Projects (Critical Path, Merges First)"
Cohesion: 0.20
Nodes (9): Acceptance Criteria, Commit, Invariants, Paths, Purpose, Steps, TD-25: Track A — Projects (Critical Path, Merges First), Tests (+1 more)

### Community 126 - "TD-26: Track B — Skills + Certifications"
Cohesion: 0.20
Nodes (9): Acceptance Criteria, Commit, Invariants, Paths, Purpose, Steps, TD-26: Track B — Skills + Certifications, Tests (+1 more)

### Community 127 - "TD-27: Track C — Investment Thesis + Posts"
Cohesion: 0.20
Nodes (9): Acceptance Criteria, Commit, Invariants, Paths, Purpose, Steps, TD-27: Track C — Investment Thesis + Posts, Tests (+1 more)

### Community 128 - "TD-28: Track D — Collections + Prose Pages"
Cohesion: 0.20
Nodes (9): Acceptance Criteria, Commit, Invariants, Paths, Purpose, Steps, TD-28: Track D — Collections + Prose Pages, Tests (+1 more)

### Community 129 - "TD-29: Track E — Resume + Forms"
Cohesion: 0.20
Nodes (9): Acceptance Criteria, Commit, Invariants, Paths, Purpose, Steps, TD-29: Track E — Resume + Forms, Tests (+1 more)

### Community 130 - "TD-30: Track F — Intro Sequence + Ambient Audio"
Cohesion: 0.20
Nodes (9): Acceptance Criteria, Commit, Invariants, Paths, Purpose, Steps, TD-30: Track F — Intro Sequence + Ambient Audio, Tests (+1 more)

### Community 131 - "TD-31: Overview Completion — Arrangement, Pinning, Empty States, Hero"
Cohesion: 0.20
Nodes (9): Acceptance Criteria, Commit, Invariants, Paths, Purpose, Steps, TD-31: Overview Completion — Arrangement, Pinning, Empty States, Hero, Tests (+1 more)

### Community 132 - "TD-32: SEO & Discoverability — JSON-LD, Sitemap/Robots, Canonical, llms.txt, SSR Suite"
Cohesion: 0.20
Nodes (9): Acceptance Criteria, Commit, Invariants, Paths, Purpose, Steps, TD-32: SEO & Discoverability — JSON-LD, Sitemap/Robots, Canonical, llms.txt, SSR Suite, Tests (+1 more)

### Community 133 - "TD-33: Crawler Analytics — Beacon, CrawlerHit, Admin Panel"
Cohesion: 0.20
Nodes (9): Acceptance Criteria, Commit, Invariants, Paths, Purpose, Steps, TD-33: Crawler Analytics — Beacon, CrawlerHit, Admin Panel, Tests (+1 more)

### Community 134 - "TD-34: Design Pass & Re-skin — Stitch Tokens, Leak Audit, Visual Regression"
Cohesion: 0.20
Nodes (9): Acceptance Criteria, Commit, Invariants, Paths, Purpose, Steps, TD-34: Design Pass & Re-skin — Stitch Tokens, Leak Audit, Visual Regression, Tests (+1 more)

### Community 135 - "TD-35: Accessibility & Performance — AA, Keyboard/SR, CWV, react-doctor"
Cohesion: 0.20
Nodes (9): Acceptance Criteria, Commit, Invariants, Paths, Purpose, Steps, TD-35: Accessibility & Performance — AA, Keyboard/SR, CWV, react-doctor, Tests (+1 more)

### Community 136 - "TD-36: Launch — Cutover, Access, Sentry, Restore Drill, Journeys, Content"
Cohesion: 0.20
Nodes (9): Acceptance Criteria, Commit, Invariants, Paths, Purpose, Steps, TD-36: Launch — Cutover, Access, Sentry, Restore Drill, Journeys, Content, Tests (+1 more)

### Community 137 - "S2_T03 — Documentation Restructure & Cleanup"
Cohesion: 0.20
Nodes (9): Acceptance Criteria (met), Data flow (documentation lifecycle), Dependencies, Functionality example, Purpose, References, S2_T03 — Documentation Restructure & Cleanup, Target structure (+1 more)

### Community 138 - "S2_T05 — CI Pipeline: Quality Gates + Contract Checks"
Cohesion: 0.20
Nodes (9): Dependencies, Environment decisions (recorded), Expected changes / where, Functionality example, Purpose, References, S2_T05 — CI Pipeline: Quality Gates + Contract Checks, Testing & acceptance criteria (+1 more)

### Community 139 - "S2_T07 — Docstrings (Public API Surface) + Per-Feature Documentation"
Cohesion: 0.20
Nodes (9): Dependencies, Expected changes / where, Feature doc template (`docs/features/<name>.md`), Functionality & example, Purpose, References, S2_T07 — Docstrings (Public API Surface) + Per-Feature Documentation, Testing & acceptance criteria (+1 more)

### Community 140 - "S2_T09 — Session Handoff + Registry Updates"
Cohesion: 0.20
Nodes (9): Dependencies, Expected changes / where, Functionality & example, Handoff content contract, Purpose, References, S2_T09 — Session Handoff + Registry Updates, Testing & acceptance criteria (+1 more)

### Community 141 - "Handoff — Admin Private + Build Failures (next session)"
Cohesion: 0.12
Nodes (15): 0. What is DONE (2026-08-31), 1. Current infra (TL;DR), 2. Remaining tasks (do not reorder — your 4 decisions), 3. Execution order (next session), 4. Specs to read, 5. Useful commands, 6. Git state at handoff, 7. Prompt for next session (+7 more)

### Community 142 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 143 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 144 - "Env Vars Registry"
Cohesion: 0.18
Nodes (10): Admin service (Railway, public), Backend service (Railway), Cron service (Railway), Dashboard-held values (not env vars), Env Vars Registry, Frontend service (Railway), GitHub environment secrets, Local `.env` (gitignored — mirrors `backend/.env.example`) (+2 more)

### Community 145 - "S2_T02 — Commit Uncommitted P3 Work + Credential Hygiene"
Cohesion: 0.22
Nodes (8): Acceptance Criteria (met), Commit plan & functionality, Dependencies, Expected changes / where, Purpose, References, S2_T02 — Commit Uncommitted P3 Work + Credential Hygiene, Security handling (user-approved decision)

### Community 146 - "S2_T04 — GATE-P2 Formal Verification"
Cohesion: 0.22
Nodes (8): Dependencies, Expected changes / where, Functionality & example, Purpose, References, S2_T04 — GATE-P2 Formal Verification, Testing & acceptance criteria, What to do

### Community 147 - "S2_T06 — CI: E2E Journeys, react-doctor Gate, Deploy Workflow"
Cohesion: 0.22
Nodes (8): Dependencies, Expected changes / where, Functionality example, Purpose, References, S2_T06 — CI: E2E Journeys, react-doctor Gate, Deploy Workflow, Testing & acceptance criteria, What to do

### Community 148 - "S2_T08 — Post-Development Documentation (Session-2 Tasks)"
Cohesion: 0.22
Nodes (8): Dependencies, Expected changes / where, Functionality & example, Purpose, References, S2_T08 — Post-Development Documentation (Session-2 Tasks), Testing & acceptance criteria, What to do

### Community 149 - "contact/page.tsx"
Cohesion: 0.15
Nodes (12): ContactResumes(), Resume, ResumeAudienceMap, VARIANT_LABELS, variantMatches(), Contact, FALLBACK_CONTACT, metadata (+4 more)

### Community 150 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 151 - "ThesisForm.tsx"
Cohesion: 0.36
Nodes (7): emptyForm(), FormState, TagRef, ThesisEntry, ThesisForm(), toDateInput(), toDatetimeLocal()

### Community 152 - "cf9af7fc8db5_relevance_audience_tag_map.py"
Cohesion: 0.43
Nodes (7): downgrade(), _map_row_id(), UUID, Delete seeded rows first (FK order), then drop the table., Upgrade schema, then seed: the feature must be demonstrable before any hand…, _tag_id(), upgrade()

### Community 153 - "Task P1.T2: Admin Authentication & Anti-Abuse"
Cohesion: 0.25
Nodes (8): P1.T2.S1: Password hashing and verification, P1.T2.S2: OTP generation, storage and verification, P1.T2.S3: Deliver OTP via Resend, P1.T2.S4: Session cookie issuance and validation, P1.T2.S5: Rate limiting and database-backed lockout, P1.T2.S6: Cloudflare Access JWT verification (env-gated), P1.T2.S7: Turnstile verification helper, Task P1.T2: Admin Authentication & Anti-Abuse

### Community 154 - "GATE-P1: Phase 1 Exit Gate"
Cohesion: 0.25
Nodes (7): Checklist → Card Map, Commit, Exit Checklist, GATE-P1: Phase 1 Exit Gate, On Failure, Purpose, Verification Commands

### Community 155 - "Task P1.T2: Admin Authentication & Anti-Abuse"
Cohesion: 0.25
Nodes (8): P1.T2.S1: Password hashing and verification, P1.T2.S2: OTP generation, storage and verification, P1.T2.S3: Deliver OTP via Resend, P1.T2.S4: Session cookie issuance and validation, P1.T2.S5: Rate limiting and database-backed lockout, P1.T2.S6: Cloudflare Access JWT verification (env-gated), P1.T2.S7: Turnstile verification helper, Task P1.T2: Admin Authentication & Anti-Abuse

### Community 156 - "Auth — password + email OTP sign-in for the single admin"
Cohesion: 0.25
Nodes (7): API Surface, Auth — password + email OTP sign-in for the single admin, Data Flow, Files To Reference, Functionality, Invariants, Purpose

### Community 157 - "Certifications — Issued credentials with kind split and R2-backed files"
Cohesion: 0.25
Nodes (7): API Surface, Certifications — Issued credentials with kind split and R2-backed files, Data Flow, Files To Reference, Functionality, Invariants, Purpose

### Community 158 - "Collections — Books, anime, and manhwa with a download-once R2 cover pipeline"
Cohesion: 0.25
Nodes (7): API Surface, Collections — Books, anime, and manhwa with a download-once R2 cover pipeline, Data Flow, Files To Reference, Functionality, Invariants, Purpose

### Community 159 - "Forms — public contact and dealflow intake behind layered anti-abuse"
Cohesion: 0.25
Nodes (7): API Surface, Data Flow, Files To Reference, Forms — public contact and dealflow intake behind layered anti-abuse, Functionality, Invariants, Purpose

### Community 160 - "Overview — per-audience homepage intro rows"
Cohesion: 0.25
Nodes (7): API Surface, Data Flow, Files To Reference, Functionality, Invariants, Overview — per-audience homepage intro rows, Purpose

### Community 161 - "Posts — External writing links routed to themed pages by collection"
Cohesion: 0.25
Nodes (7): API Surface, Data Flow, Files To Reference, Functionality, Invariants, Posts — External writing links routed to themed pages by collection, Purpose

### Community 162 - "Projects — Portfolio projects with file attachments and timeline cross-links"
Cohesion: 0.25
Nodes (7): API Surface, Data Flow, Files To Reference, Functionality, Invariants, Projects — Portfolio projects with file attachments and timeline cross-links, Purpose

### Community 163 - "Prose — Markdown pages organized by an explicit editorial group enum"
Cohesion: 0.25
Nodes (7): API Surface, Data Flow, Files To Reference, Functionality, Invariants, Prose — Markdown pages organized by an explicit editorial group enum, Purpose

### Community 164 - "Relevance — audience-to-topic-tag map powering per-audience content filtering"
Cohesion: 0.25
Nodes (7): API Surface, Data Flow, Files To Reference, Functionality, Invariants, Purpose, Relevance — audience-to-topic-tag map powering per-audience content filtering

### Community 165 - "Skills — Flat ordered skill inventory, always publicly visible"
Cohesion: 0.25
Nodes (7): API Surface, Data Flow, Files To Reference, Functionality, Invariants, Purpose, Skills — Flat ordered skill inventory, always publicly visible

### Community 166 - "Thesis — Investment thesis entries linking out to Google Drive documents"
Cohesion: 0.25
Nodes (7): API Surface, Data Flow, Files To Reference, Functionality, Invariants, Purpose, Thesis — Investment thesis entries linking out to Google Drive documents

### Community 167 - "Timeline — unified education and experience entries with publish lifecycle"
Cohesion: 0.25
Nodes (7): API Surface, Data Flow, Files To Reference, Functionality, Invariants, Purpose, Timeline — unified education and experience entries with publish lifecycle

### Community 168 - "Manual Checklists (user-executed To-Dos)"
Cohesion: 0.25
Nodes (7): Manual Checklists (user-executed To-Dos), TD-M1 — Verify Cloudflare zone, TD-M2 — R2 bucket + Turnstile + Web Analytics, TD-M3 — Resend domain verification, TD-M4 — Railway project setup (paired), TD-M5 — GitHub: auto-deploy off + environment secret, TD-M6 — Cloudflare Tunnel + Access (paired)

### Community 169 - "4. Per-task detail (each tags every document to consult)"
Cohesion: 0.12
Nodes (15): 1. Spec existence audit (requirement: confirm each task has its own spec), 2. Ordering / dependency map, 3. Global invariants to preserve while touching infra (`docs/conventions.md`), 4. Per-task detail (each tags every document to consult), 5. Definition of Done for the manual session, 6. Next phase (after this handoff), Handoff — Manual Infra & Launch Tasks (TD-M1…M6, TD-36), ⚠ Revised plan (2026-08-28) — Cloudflare services removed (+7 more)

### Community 170 - "dealflow/page.tsx"
Cohesion: 0.40
Nodes (3): metadata, DealflowForm(), Props

### Community 171 - "2. Remaining tasks (priority order — do not reorder, pause for User where noted)"
Cohesion: 0.12
Nodes (15): 0. What is DONE (code phase, 2026-08-30 build session), 1. TL;DR — Current infra, 2. Remaining tasks (priority order — do not reorder, pause for User where noted), 3. Deferred features (not in this handoff's execution), 4. Useful commands (copy-paste), 5. Git state at handoff (2026-08-31), Bridge revert (tied to TD-M6), Handoff — Remaining Manual Tasks (next session) (+7 more)

### Community 172 - "4fc2a3dab90d_overview_intro_model_and_seeds.py"
Cohesion: 0.43
Nodes (6): downgrade(), _intro_id(), UUID, Delete seeded rows, then drop the table., Upgrade schema, then seed all six intro rows., upgrade()

### Community 173 - "posts/endpoints/router.py"
Cohesion: 0.19
Nodes (21): create(), delete(), get_admin(), get_public(), list_admin(), list_public(), DbSession, delete (+13 more)

### Community 174 - "Postgres Backup & Restore Procedure (TD-36 / gap G12)"
Cohesion: 0.29
Nodes (6): 1. Backup policy check (TD-M4 decision, re-verified at TD-36), 2. Weekly pg_dump cron to R2 (only if Railway backups are not automatic), 3. Restore drill — into scratch Docker Postgres, 4. Failure modes to expect, 5. Schedule, Postgres Backup & Restore Procedure (TD-36 / gap G12)

### Community 175 - "Spec Catalog — Session 1 (Initial Build-Out, Phases P0–P3)"
Cohesion: 0.29
Nodes (6): P0 — Foundations, P1 — Backend Spine, P2 — Content Tracks, P3 — Convergence (built in original session 4, committed in current session 2), Spec Catalog — Session 1 (Initial Build-Out, Phases P0–P3), Verification snapshot after session-2 baseline (see `../session-2/S2_T01_20260822-2212_baseline-verification.md`)

### Community 176 - "S2_T01 — Baseline Verification of Uncommitted P3 Work"
Cohesion: 0.29
Nodes (6): Acceptance Criteria (met), Dependencies, Purpose, References, S2_T01 — Baseline Verification of Uncommitted P3 Work, What Was Done & Where

### Community 177 - "check_registries.py"
Cohesion: 0.52
Nodes (6): check_models_registry(), check_router_registration(), extract_class_names(), find_feature_files(), main(), Path

### Community 178 - "scripts"
Cohesion: 0.33
Nodes (6): scripts, build, dev, lint, openapi:generate, preview

### Community 179 - "admin/src/api.d.ts"
Cohesion: 0.33
Nodes (5): components, $defs, operations, paths, webhooks

### Community 180 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 181 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 182 - "Development Plan — Phase 1: The Vertical Spine"
Cohesion: 0.33
Nodes (5): Development Plan — Phase 1: The Vertical Spine, Exit Checklist, Phase 1 Risk Register, Phase Overview, The Architectural Decision This Phase Must Settle

### Community 183 - "Task P1.T5: Timeline Backend Slice"
Cohesion: 0.33
Nodes (6): P1.T5.S1: Model the unified timeline entry, P1.T5.S2: Define Pydantic schemas, P1.T5.S3: Implement service and repository layers, P1.T5.S4: Build public and admin routers, P1.T5.S5: Test the slice, Task P1.T5: Timeline Backend Slice

### Community 184 - "Task P1.T7: Timeline Public Experience & Tile Contract"
Cohesion: 0.33
Nodes (6): P1.T7.S1: Build the timeline page, P1.T7.S2: Implement filter chips, P1.T7.S3: Build the OverviewIntro model and default row, P1.T7.S4: Define the tile contract and render the timeline tile, P1.T7.S5: Build the persistent HUD, Task P1.T7: Timeline Public Experience & Tile Contract

### Community 185 - "Development Plan — Phase 1: The Vertical Spine"
Cohesion: 0.33
Nodes (5): Development Plan — Phase 1: The Vertical Spine, Exit Checklist, Phase 1 Risk Register, Phase Overview, The Architectural Decision This Phase Must Settle

### Community 186 - "Task P1.T5: Timeline Backend Slice"
Cohesion: 0.33
Nodes (6): P1.T5.S1: Model the unified timeline entry, P1.T5.S2: Define Pydantic schemas, P1.T5.S3: Implement service and repository layers, P1.T5.S4: Build public and admin routers, P1.T5.S5: Test the slice, Task P1.T5: Timeline Backend Slice

### Community 187 - "Task P1.T7: Timeline Public Experience & Tile Contract"
Cohesion: 0.33
Nodes (6): P1.T7.S1: Build the timeline page, P1.T7.S2: Implement filter chips, P1.T7.S3: Build the OverviewIntro model and default row, P1.T7.S4: Define the tile contract and render the timeline tile, P1.T7.S5: Build the persistent HUD, Task P1.T7: Timeline Public Experience & Tile Contract

### Community 188 - "frontend/src/api.d.ts"
Cohesion: 0.33
Nodes (5): components, $defs, operations, paths, webhooks

### Community 189 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 190 - "check_ssr.sh"
Cohesion: 0.67
Nodes (5): check_all_routes(), check_http_200(), check_seo_assets(), check_url(), check_ssr.sh script

### Community 191 - "admin/package.json"
Cohesion: 0.40
Nodes (4): name, private, type, version

### Community 192 - "admin/tsconfig.json"
Cohesion: 0.40
Nodes (4): compilerOptions, paths, files, references

### Community 193 - "Task P1.T1: Core Data Foundations"
Cohesion: 0.40
Nodes (5): P1.T1.S1: Define base model and mixins, P1.T1.S2: Define the audience enum and topic tag schema, P1.T1.S3: Define the publishing mixin, P1.T1.S4: Build the models registry and first real migration, Task P1.T1: Core Data Foundations

### Community 194 - "Task P1.T3: Relevance Engine"
Cohesion: 0.40
Nodes (5): P1.T3.S1: Model the audience-tag mapping, P1.T3.S2: Implement relevance resolution, P1.T3.S3: Expose the tag map endpoint, P1.T3.S4: Test the resolution logic against a real database, Task P1.T3: Relevance Engine

### Community 195 - "Task P1.T4: Publishing Workflow & Revalidation"
Cohesion: 0.40
Nodes (5): P1.T4.S1: Build the revalidation route handler, P1.T4.S2: Trigger revalidation from content mutations, P1.T4.S3: Implement the scheduled-publish cron job, P1.T4.S4: Enforce the public filter across endpoints, Task P1.T4: Publishing Workflow & Revalidation

### Community 196 - "Task P1.T6: Frontend Shell & Contract Tooling"
Cohesion: 0.40
Nodes (5): P1.T6.S1: Wire OpenAPI type generation, P1.T6.S2: Implement the category cookie and context, P1.T6.S3: Port the relevance resolver to the client, P1.T6.S4: Establish the data fetching and caching layer, Task P1.T6: Frontend Shell & Contract Tooling

### Community 197 - "Task P1.T8: Admin Shell & Timeline CRUD"
Cohesion: 0.40
Nodes (5): P1.T8.S1: Build the login flow, P1.T8.S2: Implement the auth guard and layout, P1.T8.S3: Build Timeline CRUD screens, P1.T8.S4: Build the audience-tag mapping matrix, Task P1.T8: Admin Shell & Timeline CRUD

### Community 198 - "GATE-P3: Phase 3 Exit Gate — Launch"
Cohesion: 0.40
Nodes (4): After the gate, Exit Checklist, GATE-P3: Phase 3 Exit Gate — Launch, Prerequisites

### Community 199 - "Task P1.T1: Core Data Foundations"
Cohesion: 0.40
Nodes (5): P1.T1.S1: Define base model and mixins, P1.T1.S2: Define the audience enum and topic tag schema, P1.T1.S3: Define the publishing mixin, P1.T1.S4: Build the models registry and first real migration, Task P1.T1: Core Data Foundations

### Community 200 - "Task P1.T3: Relevance Engine"
Cohesion: 0.40
Nodes (5): P1.T3.S1: Model the audience-tag mapping, P1.T3.S2: Implement relevance resolution, P1.T3.S3: Expose the tag map endpoint, P1.T3.S4: Test the resolution logic against a real database, Task P1.T3: Relevance Engine

### Community 201 - "Task P1.T4: Publishing Workflow & Revalidation"
Cohesion: 0.40
Nodes (5): P1.T4.S1: Build the revalidation route handler, P1.T4.S2: Trigger revalidation from content mutations, P1.T4.S3: Implement the scheduled-publish cron job, P1.T4.S4: Enforce the public filter across endpoints, Task P1.T4: Publishing Workflow & Revalidation

### Community 202 - "Task P1.T6: Frontend Shell & Contract Tooling"
Cohesion: 0.40
Nodes (5): P1.T6.S1: Wire OpenAPI type generation, P1.T6.S2: Implement the category cookie and context, P1.T6.S3: Port the relevance resolver to the client, P1.T6.S4: Establish the data fetching and caching layer, Task P1.T6: Frontend Shell & Contract Tooling

### Community 203 - "Task P1.T8: Admin Shell & Timeline CRUD"
Cohesion: 0.40
Nodes (5): P1.T8.S1: Build the login flow, P1.T8.S2: Implement the auth guard and layout, P1.T8.S3: Build Timeline CRUD screens, P1.T8.S4: Build the audience-tag mapping matrix, Task P1.T8: Admin Shell & Timeline CRUD

### Community 204 - "GATE-P2 Verification Evidence"
Cohesion: 0.40
Nodes (4): GATE-P2 Verification Evidence, Production-build route audit (bonus evidence), Scripted results (this run), Verdict

### Community 205 - "frontend/components/ui/button.tsx"
Cohesion: 0.70
Nodes (3): Button(), buttonVariants, cn()

### Community 206 - "React + TypeScript + Vite"
Cohesion: 0.50
Nodes (3): Expanding the Oxlint configuration, React Compiler, React + TypeScript + Vite

### Community 207 - "AGENTS.md"
Cohesion: 0.50
Nodes (3): CodeGraph, graphify, Project: portfolio-sid

### Community 208 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 209 - "graphify reference: commit hook and native CLAUDE.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### Community 210 - "graphify reference: incremental update and cluster-only"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### Community 211 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 212 - "graphify reference: commit hook and native CLAUDE.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### Community 213 - "graphify reference: incremental update and cluster-only"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### Community 214 - "GATE-P0: Phase 0 Exit Checklist"
Cohesion: 0.50
Nodes (3): Exit Checklist, GATE-P0: Phase 0 Exit Checklist, Sign-off

### Community 215 - "GATE-P2 — Phase 2 Exit Gate"
Cohesion: 0.50
Nodes (3): Exit Checklist, GATE-P2 — Phase 2 Exit Gate, Sign-off

### Community 216 - "frontend/README.md"
Cohesion: 0.50
Nodes (3): Deploy on Vercel, Getting Started, Learn More

### Community 217 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 218 - "graphify reference: commit hook and native CLAUDE.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### Community 219 - "graphify reference: incremental update and cluster-only"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### Community 231 - "Execution model (sub-agent dispatch)"
Cohesion: 0.12
Nodes (15): DoD checklist (final), Execution model (sub-agent dispatch), Global Constraints, portfolio-sid-v2 Deployment Implementation Plan, Task 0: Pre-flight code commits (before any Railway mutation), Task 10 (Phase 10): Cutover + drill, Task 1 (Phase 1): Project skeleton + secrets prep, Task 2 (Phase 2): Data layer — pgbouncer (+7 more)

### Community 238 - "next.config.ts"
Cohesion: 0.33
Nodes (5): apiHost, nextConfig, RemotePattern, remotePatterns, sentryConfig

### Community 242 - "React Doctor"
Cohesion: 0.13
Nodes (13): Commands, Config shape, Decision guide, Educating the user, Explaining and configuring rules, Workflow, After making React code changes:, Command (+5 more)

### Community 243 - "layout.tsx"
Cohesion: 0.14
Nodes (17): geistMono, geistSans, metadata, AUDIO_TRACKS, AudioTrack, AudioContext, AudioControls, AudioProvider() (+9 more)

### Community 244 - "resumes/service.py"
Cohesion: 0.21
Nodes (21): create(), delete(), get(), list_active(), list_all(), AsyncSession, Resume, UUID (+13 more)

### Community 302 - "React Doctor"
Cohesion: 0.13
Nodes (13): Commands, Config shape, Decision guide, Educating the user, Explaining and configuring rules, Workflow, After making React code changes:, Command (+5 more)

### Community 303 - "3. Per-task plan (agent vs user, pause points, verify)"
Cohesion: 0.13
Nodes (14): 0. What is already DONE (this session, 2026-08-29), 1. Invariants you MUST preserve (conventions.md), 2. Execution order (do not reorder), 3. Per-task plan (agent vs user, pause points, verify), 4. Open items to resolve in this phase, 5. Commits, Handoff — Railway Infra & Hosting (post code-removal), Prepare for hosting (+6 more)

### Community 304 - "React Doctor"
Cohesion: 0.13
Nodes (13): Commands, Config shape, Decision guide, Educating the user, Explaining and configuring rules, Workflow, After making React code changes:, Command (+5 more)

### Community 305 - "2. Proposed design — Timeline Detail Page (Option 2)"
Cohesion: 0.14
Nodes (13): 1.1 Project → Timeline (exists, one-way), 1.2 Timeline → Projects (missing, the gap), 1.3 Audience / contact / "show all" (your D2), 1. Codegraph / grep evidence (current wiring), 2.1 Information architecture, 2.2 Backend changes, 2.3 Frontend changes, 2.4 Admin (+5 more)

### Community 306 - "LOCAL.md — Run the whole stack without any cloud secrets"
Cohesion: 0.15
Nodes (12): 0. Prerequisites, 1. Start infrastructure (Postgres + MinIO), 1a. PgBouncer — optional local sidecar (future agent load), 2. Backend env (gitignored — do NOT commit), 3. Migrate + seed, 4. Start the three servers (3 terminals, or background with `&`), 5. Smoke test (proves crawlers see content + admin renders), 6. What to click through (manual) (+4 more)

### Community 307 - "test_seed_resumes.py"
Cohesion: 0.14
Nodes (13): clean_resumes_and_tags(), AsyncEngine, AsyncSession, fixture, Seed-resumes helpers: hash determinism, idempotent upsert, variant allowlist.…, Direct model upsert by variant — seed logic idempotent (same key)., TopicTag upsert idempotent (second seed updates label)., Run seed_resume_pdfs twice with same fake PDF — count stays 1. (+5 more)

### Community 308 - "DbSession"
Cohesion: 0.16
Nodes (16): admin_get_map(), admin_update_map(), delete_tag(), get_map(), list_tags(), DbSession, delete, get (+8 more)

### Community 309 - "Handoff — Cloudflare Removal & Revised Launch Plan"
Cohesion: 0.17
Nodes (11): 1. Decision (locked), 2. Execution order (as directed), 3.1 Storage — backend-served `/media` + Railway Volume, 3.2 Turnstile → honeypot + rate-limit (backend already done), 3.3 Analytics — Cloudflare → Umami (self-hosted, env-gated), 3.4 Docs (planning, do alongside code), 3. Code prerequisites (exact edit map), 4. Revised infra task flow (next session) (+3 more)

### Community 311 - "HANDOFF — Session 5 (Engagement Session 2: Rescue, CI, Docs Architecture)"
Cohesion: 0.22
Nodes (8): 1. What happened this session, 2. Status board (post-session), 3. 🔴 Immediate blockers for next session, 4. Execution protocol for next session, 5. Documents for next session, 6. Local environment notes, 7. Lessons learned (new this session), HANDOFF — Session 5 (Engagement Session 2: Rescue, CI, Docs Architecture)

### Community 312 - "Post-Development Recap — 2026-08-30 (Resume Canon + Timeline Detail + pgBouncer)"
Cohesion: 0.22
Nodes (8): Files changed (36 vs HEAD), How to use (local → admin edits → production), Infra still pending (per HANDOFF-RAILWAY-INFRA-PLAN.md:33, not reordered), Open questions now asked (reply inline), Post-development docs per your rule, Post-Development Recap — 2026-08-30 (Resume Canon + Timeline Detail + pgBouncer), Verification tally, What shipped this session

### Community 313 - "LOCAL-01: Local Dev Runbook + Smoke Test"
Cohesion: 0.22
Nodes (8): Commit, Invariants, LOCAL-01: Local Dev Runbook + Smoke Test, Paths, Purpose, Steps, Tests / Acceptance, Verify

### Community 314 - "relevance/repository.py"
Cohesion: 0.32
Nodes (11): create_tag(), delete_tag(), get_tag(), list_map_rows(), list_tags(), AsyncSession, UUID, Relevance repository: tag-map reads and atomic replace. Never imports FastAPI… (+3 more)

### Community 315 - "env.py"
Cohesion: 0.24
Nodes (10): do_run_migrations(), Run migrations in 'offline' mode. This configures the context with just a URL…, Create an async engine and run migrations via run_sync. The engine reuses…, Run migrations in 'online' mode., run_async_migrations(), run_migrations_offline(), run_migrations_online(), pgbouncer_connect_args() (+2 more)

### Community 316 - "Crawlers — AI-crawler hit analytics without storing IP addresses"
Cohesion: 0.25
Nodes (7): API Surface, Crawlers — AI-crawler hit analytics without storing IP addresses, Data Flow, Files To Reference, Functionality, Invariants, Purpose

### Community 317 - "Resumes — audience-variant resume registry over object storage keys"
Cohesion: 0.25
Nodes (7): API Surface, Data Flow, Files To Reference, Functionality, Invariants, Purpose, Resumes — audience-variant resume registry over object storage keys

### Community 318 - "React Doctor Baseline"
Cohesion: 0.25
Nodes (7): `admin/` categories, `frontend/` categories, How to reproduce, React Doctor Baseline, Representative findings (warnings — backlog, not day-one failures), Summary, Updating this baseline

### Community 319 - "Plan — Email Provider Abstraction (Deferred, Keep Resend)"
Cohesion: 0.25
Nodes (7): Acceptance, Effort, Important note, Plan — Email Provider Abstraction (Deferred, Keep Resend), Scope (when implemented), Temporal (F29 voice agent), Why

### Community 320 - "Post-Development — Timeline Detail + Reverse Project Linking (Option 2)"
Cohesion: 0.25
Nodes (7): Backend, Changes, Codegraph evidence (rechecked before code), Frontend, Open items you are being asked about (per your "ask me more context"), Post-Development — Timeline Detail + Reverse Project Linking (Option 2), Verification

### Community 321 - "test_scheduler.py"
Cohesion: 0.07
Nodes (43): publishables(), Any, Register a publishable model for the scheduled-publish cron. APPEND-ONLY zone,…, Snapshot of registered ``(model, tag)`` pairs., register_publishable(), get_summary(), list_hits(), DbSession (+35 more)

### Community 322 - "Session Prompt — Railway Infra & Hosting (Cloudflare-removal follow-up)"
Cohesion: 0.29
Nodes (6): Execution order (do not reorder), For each task, structure as:, Open decisions to raise when reached, Required reading first (authoritative), Session Prompt — Railway Infra & Hosting (Cloudflare-removal follow-up), Workflow (follow the sub-agent loop for each task)

### Community 323 - "S2_T07 — Docstrings & Feature Docs Post-Development"
Cohesion: 0.29
Nodes (6): Decision recorded (with user-approved scope), Measured docstring state (audit before writing), Remaining, S2_T07 — Docstrings & Feature Docs Post-Development, Verification evidence, What was built

### Community 324 - "Post-Development — Resume Consolidation (2026-08-30)"
Cohesion: 0.29
Nodes (6): Artifacts, Decisions recorded, Follow-ups (admin-editable), Local verification (real Postgres, no mocks per conventions 5), Post-Development — Resume Consolidation (2026-08-30), Production seeding (repeat after secrets set)

### Community 325 - "anime-manga/page.tsx"
Cohesion: 0.33
Nodes (4): AnimeMangaClient(), Item, Item, metadata

### Community 326 - "S2_T05 / S2_T06 — CI Pipeline Post-Development"
Cohesion: 0.33
Nodes (5): Deviations from cards (decisions recorded), Remaining, S2_T05 / S2_T06 — CI Pipeline Post-Development, Verification evidence, What was built

### Community 327 - "Session-2 Summary — What Shipped"
Cohesion: 0.33
Nodes (5): Blockers / carries, Commits (this session, oldest → newest), Key decisions made this session, Session-2 Summary — What Shipped, Verification state at close

### Community 328 - "src/lib/api.ts"
Cohesion: 0.12
Nodes (15): App(), Select(), apiBase, AuthRedirect, setNavigate(), queryClient, Root(), FORM_TYPE_LABELS (+7 more)

### Community 329 - "869fc8d8c856_widen_resume_variant_to_string.py"
Cohesion: 0.40
Nodes (4): downgrade(), Widen resumes.variant from native enum to VARCHAR(50)., Best-effort revert to 2-value native enum (local rollback only)., upgrade()

### Community 331 - "DEPLOYMENT.md — Architecture, Runbook & Troubleshooting"
Cohesion: 0.20
Nodes (9): 1. Architecture, 2. Build matrix, 3. Env essentials, 4. Deploy paths, 5. Troubleshooting (symptom → cause → fix), 6. Verification gate suite (after any change), 7. Restore, 8. Secrets (+1 more)

### Community 335 - "replace_map"
Cohesion: 0.42
Nodes (9): load_tag_map(), Full audience → tag-slug map in ONE query. Loaded once per request; per-item…, Delete every row and insert the new mapping in ONE transaction. The caller…, replace_map(), _create_tags(), AsyncSession, test_load_tag_map_shape(), test_replace_map_old_rows_gone_new_present() (+1 more)

### Community 336 - "test_skills.py"
Cohesion: 0.24
Nodes (15): clean_skills_tables(), _login(), AsyncClient, AsyncEngine, AsyncSession, fixture, MonkeyPatch, Skills: API tests. Skills have no status, tags, or override logic. (+7 more)

### Community 337 - "CertsForm.tsx"
Cohesion: 0.36
Nodes (7): Certification, CertsForm(), emptyForm(), FormState, TagRef, toDateInput(), toDatetimeLocal()

### Community 338 - "Handoff — Steady State (2026-09-03)"
Cohesion: 0.29
Nodes (6): Current state, Deploy mechanisms (all three verified), Handoff — Steady State (2026-09-03), Key docs, Open items (future sessions), Secrets

### Community 339 - "POST-DEPLOYMENT — portfolio-sid-v2"
Cohesion: 0.18
Nodes (10): CI fallback (deploy.yml), Cutover, DoD checklist (final), Gates (recorded PASS/FAIL per phase), Hard-won lessons (all encoded in PLAN.md Global Constraints), Infrastructure as Code (adopted 2026-09-02), POST-DEPLOYMENT — portfolio-sid-v2, Restore drill (restore-procedure.md §3) (+2 more)

### Community 340 - "cc8619b8d037_contact_profile_model_and_default_seed.py"
Cohesion: 0.40
Nodes (4): downgrade(), Upgrade schema, then seed the singleton row., Delete the seeded row, then drop the table., upgrade()

### Community 343 - "clean_relevance_tables"
Cohesion: 0.67
Nodes (3): clean_relevance_tables(), AsyncEngine, fixture

## Knowledge Gaps
- **1931 isolated node(s):** `stitch`, `$schema`, `typescript`, `oxc`, `react/rules-of-hooks` (+1926 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **42 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `revalidate()` connect `revalidate` to `overview/endpoints/router.py`, `collections/endpoints/router.py`, `forms/endpoints/router.py`, `get_settings`, `public_filter`, `projects/service.py`, `test_scheduler.py`, `certifications/service.py`, `posts/endpoints/router.py`, `relevance/service.py`, `resumes/endpoints/router.py`, `contact/endpoints/router.py`, `skills/endpoints/router.py`, `thesis/endpoints/router.py`, `timeline/endpoints/router.py`, `DbSession`, `PublishStatus`?**
  _High betweenness centrality (0.014) - this node is a cross-community bridge._
- **Why does `Settings` connect `Settings` to `test_auth.py`, `forms/endpoints/router.py`, `get_settings`, `database.py`, `test_crawlers.py`, `email.py`, `test_skills.py`, `test_projects.py`, `thesis/endpoints/router.py`, `test_relevance.py`, `test_storage.py`, `test_timeline.py`, `_classify_agent`, `env.py`, `test_posts.py`, `conftest.py`?**
  _High betweenness centrality (0.012) - this node is a cross-community bridge._
- **Why does `PublishStatus` connect `PublishStatus` to `overview/endpoints/router.py`, `collections/endpoints/router.py`, `Audience`, `public_filter`, `test_scheduler.py`, `projects/service.py`, `posts/service.py`, `certifications/service.py`, `timeline/endpoints/router.py`, `test_projects.py`, `thesis/endpoints/router.py`, `test_timeline.py`, `test_core_models.py`, `test_posts.py`?**
  _High betweenness centrality (0.010) - this node is a cross-community bridge._
- **Are the 5 inferred relationships involving `Settings` (e.g. with `LocalDiskStorage` and `S3Storage`) actually correct?**
  _`Settings` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Are the 26 inferred relationships involving `Audience` (e.g. with `Base` and `PublishableMixin`) actually correct?**
  _`Audience` has 26 INFERRED edges - model-reasoned connections that need verification._
- **Are the 35 inferred relationships involving `Base` (e.g. with `Audience` and `PublishStatus`) actually correct?**
  _`Base` has 35 INFERRED edges - model-reasoned connections that need verification._
- **What connects `stitch`, `$schema`, `typescript` to the rest of the system?**
  _1931 weakly-connected nodes found - possible documentation gaps or missing edges._