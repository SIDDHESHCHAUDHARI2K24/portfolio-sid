# Portfolio — Master To-Do Index

**Project:** Audience-segmented portfolio platform (siddhesh-chaudhari.com)
**Repo:** github.com/SIDDHESHCHAUDHARI2K24/portfolio-sid (public)
**Sources:** `development_plan/development-plan-P0..P3.md`, `overall_context/tech-stack-analysis.md`, `overall_context/dependency-map.md`
**Status board legend:** `[ ]` pending · `[~]` in progress · `[x]` done · `[!]` blocked

## Fixed facts

- Domain: `siddhesh-chaudhari.com` — registered via Cloudflare Domains, NS already delegated (verified)
- Stack: Next.js App Router (frontend), Vite+React (admin), FastAPI+SQLAlchemy2 async+Alembic (backend), Postgres 16, R2/MinIO, Railway, Cloudflare (CDN/Tunnel/Access/Turnstile/Analytics), Resend
- Package manager: **npm** (per-app OpenAPI typegen; pnpm workspaces rejected)
- Local: macOS, node 24, uv, docker (running), railway CLI (logged in), codegraph 1.5.0, graphify CLI
- Agents to wire: opencode, Claude Code, Codex CLI, cursor-agent (no blackbox-cli)
- Secrets policy: env vars only. Railway env vars + GitHub `production` environment secrets. Never git. `opencode.json` is gitignored (contains a provider key)

## Waves & To-Do index

### Wave 0 — bootstrap
| ID | Title | Exec | Deps | Status |
|---|---|---|---|---|
| TD-00 | Repo init + git hygiene + secrets guardrails | agent | — | [x] |
| TD-01 | Agent tooling: caveman, graphify, codegraph, superpowers | agent | TD-00 | [x] |
| TD-02 | Canonical docs set + conventions + pointer files | agent | TD-00 | [x] |
| TD-M1 | Verify Cloudflare zone active; record renewal/WHOIS | user | — | [~] domain bought + NS delegated; zone-Active check + renewal record pending |

### Wave 1 — scaffolds (fully parallel)
| ID | Title | Exec | Deps | Status |
|---|---|---|---|---|
| TD-03 | Backend scaffold: uv + FastAPI factory + core/ | agent | TD-00 | [x] |
| TD-04 | Next.js scaffold + overlay invariant + noindex default | agent | TD-00 | [x] |
| TD-05 | Admin SPA scaffold (Vite+React+TS) | agent | TD-00 | [x] |
| TD-06 | Docker Compose: Postgres 16 + MinIO + bucket init | agent | TD-00 | [x] |
| TD-M2 | R2 bucket + Turnstile widget + Web Analytics | user | TD-M1 | [ ] |

### Wave 2 — backend core
| ID | Title | Exec | Deps | Status |
|---|---|---|---|---|
| TD-07 | Async Alembic + models registry | agent | TD-03, TD-06 | [x] |
| TD-08 | StorageAdapter (R2/MinIO, content-hashed keys) | agent | TD-03, TD-06, TD-M2 | [x] MinIO/local verified; R2 creds pending TD-M2 |
| TD-09 | Multi-stage backend Dockerfile (admin+API one container) | agent | TD-03, TD-05 | [x] |
| TD-M3 | Resend domain verify: SPF/DKIM/DMARC | user | TD-M1 | [ ] |

### Wave 3 — design
| ID | Title | Exec | Deps | Status |
|---|---|---|---|---|
| TD-10 | Stitch MCP (env expansion) + DESIGN.md export (+openpencil optional) | paired | TD-00 | [~] .mcp.json committed (${STITCH_API_KEY}); design pass pending |
| TD-11 | Design tokens → Tailwind/shadcn both apps | agent | TD-10, TD-04, TD-05 | [ ] |

### Wave 4 — CI/CD + infra deploy
| ID | Title | Exec | Deps | Status |
|---|---|---|---|---|
| TD-12 | CI: ruff/mypy/ESLint/tsc + unit tests (codegraph-scoped) | agent | TD-03..05, TD-01 | [ ] |
| TD-13 | CI: OpenAPI drift + Alembic single-head | agent | TD-12, TD-07 | [ ] |
| TD-14 | react-doctor install+baseline+PR gate; Playwright E2E; SSR curl check in CI | agent | TD-12, TD-09 | [ ] |
| TD-M4 | Railway: Postgres + backend/frontend/cron services | paired | TD-09, TD-M2 | [~] railway CLI logged in; services not provisioned |
| TD-M5 | Railway auto-deploy OFF + RAILWAY_TOKEN env secret | user | TD-M4 | [ ] |
| TD-M6 | Cloudflare Tunnel + Access (env-gated, single hostname) | paired | TD-M1, TD-M4 | [ ] |
| TD-15 | Deploy workflow + production environment approval | agent | TD-M5, TD-14 | [ ] |

**GATE-P0** — `p0/GATE-P0.md` exit checklist

### Wave 5 — P1 data/auth (TD-17/18/19 parallel after TD-16)
| ID | Title | Exec | Deps | Status |
|---|---|---|---|---|
| TD-16 | Core data: base/mixins, Audience, TopicTag, Publishable, registry+migration | agent | TD-07 | [x] |
| TD-17 | Admin auth: Argon2, OTP, Resend, session, lockout, Access JWT | agent | TD-16, TD-M3 | [x] live Resend send pending TD-M3 |
| TD-18 | Relevance engine: map table, pure resolver, endpoint, Postgres tests | agent | TD-16 | [x] |
| TD-19 | Publishing: revalidate route, triggers, scheduler cron, public_filter | agent | TD-16, TD-04 | [x] |

### Wave 6 — spine
| ID | Title | Exec | Deps | Status |
|---|---|---|---|---|
| TD-20 | Timeline backend slice (model→routers→tests) | agent | TD-16..19 | [ ] |
| TD-21 | Frontend shell: typegen, category cookie, relevance.ts parity, fetch layer | agent | TD-20, TD-19 | [ ] |
| TD-22 | Timeline page + chips + OverviewIntro + tile contract + HUD | agent | TD-21 | [ ] |
| TD-23 | Admin shell: login, guard, Timeline CRUD, tag-map matrix | agent | TD-17, TD-20 | [ ] |

**GATE-P1** — `p1/GATE-P1.md` exit checklist

### Wave 7 — P2 parallel tracks (TD-25..29 parallel; TD-24 first)
| ID | Title | Exec | Deps | Status |
|---|---|---|---|---|
| TD-24 | Contention protocol: regen script, registry checks, merge rules | agent | TD-13, TD-21, TD-22 | [ ] |
| TD-25 | Track A — Projects (critical path, merges first) | agent | TD-24 | [ ] |
| TD-26 | Track B — Skills + Certifications (real-mobile PDF test) | agent | TD-24 | [ ] |
| TD-27 | Track C — Thesis + Posts (collections ≠ topic tags) | agent | TD-24 | [ ] |
| TD-28 | Track D — Collections + ProsePages (cover pipeline) | agent | TD-24 | [ ] |
| TD-29 | Track E — Resume + Forms | agent | TD-24 | [ ] |
| TD-30 | Track F — Intro sequence + ambient audio | agent | F.T1: TD-11; rest: TD-22 | [ ] |

**GATE-P2** — `p2/GATE-P2.md` exit checklist

### Wave 8 — P3 convergence
| ID | Title | Exec | Deps | Status |
|---|---|---|---|---|
| TD-31 | Overview completion: arrangement, pinning, empty states, hero | agent | GATE-P2 | [ ] |
| TD-32 | SEO: JSON-LD live data, sitemap/robots AI allow, canonical, llms.txt, curl suite CI | agent | TD-31 | [ ] |
| TD-33 | Crawler analytics: beacon, CrawlerHit, admin panel | agent | TD-32 | [ ] |
| TD-34 | Re-skin: Stitch full design, token swap + leak audit, visual regression | agent | TD-31 | [ ] |
| TD-35 | A11y & perf: AA incl. dimmed, keyboard/SR, CWV, react-doctor full | agent | TD-34 | [ ] |
| TD-36 | Launch: cutover, Access on, Sentry, restore drill, journeys, content | paired | all | [ ] |

**GATE-P3** — `p3/GATE-P3.md` exit checklist → LAUNCH

## Execution loop (per To-Do)

1. **brainstorm** — gap check vs card; small decisions recorded on card; big gaps → ask user
2. **plan** — refine steps (writing-plans)
3. **execute** — subagents where parallelism is dependency-safe (subagent-driven-development)
4. **code** — TDD: failing test first; checklist maintained
5. **test** — card acceptance criteria + ruff/mypy/eslint/tsc; react-doctor on frontend
6. **code review** — requesting-code-review
7. **verify** — verification-before-completion: evidence before claims
8. **commit** — conventional commit, one per To-Do (or per sub-task if large)

Same error 3× → stop, systematic-debugging, then re-plan.

## Parallelism & merge rules

- Wave 1 (TD-03..06), Wave 5 (TD-17/18/19), Wave 7 (TD-25..29) are the parallel fan-outs; disjoint file sets
- P2 merge queue: Track A first (critical path), then completion order; one merge at a time; after each merge remaining branches rebase + run `scripts/regen_migration.sh` (TD-24)
- One migration per feature branch, always generated against current `origin/main`, never hand-edit `down_revision`
- Daily rebase cadence for in-flight tracks

## Test pyramid ownership

| Layer | Introduced |
|---|---|
| Unit: pytest+pytest-asyncio+httpx / Vitest+RTL | TD-03 / TD-04-05 |
| Integration: Postgres service container | TD-12 |
| Contract: OpenAPI drift, relevance parity fixture | TD-13, TD-21 |
| SSR curl suite (`scripts/check_ssr.sh`) | TD-04 → CI in TD-14 → all routes TD-32 |
| E2E: Playwright journeys | TD-14 → full journeys TD-36 |
| Visual regression screenshots | TD-34 |

## Card format

Every card: header (Phase/Wave/Executor/Effort/Source/Depends/Blocks) → Purpose → Paths → Steps → Tests → Acceptance Criteria → Verify → Commit → Invariants. Exemplar: `p0/TD-00-repo-init.md`.

## Handoff

`development_plan/handoff/` holds: env-var registry, manual checklists, content-authoring checklist, restore procedure, and per-session handoff docs (`HANDOFF-SESSION-N.md`).
