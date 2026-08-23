# HANDOFF — Session 3 (P0 design + P2 content tracks A–F)

**Written:** end of session 3 · **Next session:** P3 convergence (TD-31 → TD-36)
**Start here:** read this file, then `development_plan/todos/README.md` (master index), then the specific To-Do card you are executing.

---

## 1. What was done this session

**Scope:** Unblocked remaining P0 blockers (GitHub push, Stitch/DESIGN.md, design tokens), built TD-24 contention protocol foundation, then developed all 6 P2 content tracks (A–F) with backend slices, frontend pages, admin CRUD screens, tiles, and migrations.

**Commits (11, oldest → newest):**
```
20bcb0f chore: Stitch MCP verified + DESIGN.md dark palette tokens
3966c04 feat: design tokens — DESIGN.md mapped to Tailwind v4/shadcn dark theme
d1042b8 chore: contention protocol — regen script, registry checks, append zones
b07b351 feat(p2): projects backend slice — model, schemas, repository, service, router, tests
3341087 fix(p2): projects — tile wiring, attachment url, timeline anchor, chip clearing
827f852 feat(p2): intro sequence — Framer Motion animation + morph + ambient audio
732b072 fix(p2): intro — CSS tokens, sessionStorage skip, grid orientation
95bc643 feat(p2): skills + certifications — backend slices, frontend pages, admin CRUD, tiles, migration
91e3759 feat(p2): posts + thesis — themed pages, collections, tiles, migration
e286656 feat(p2): collections + prose — cover pipeline, books/anime, prose pages, tiles, migration
29cdbda feat(p2): resumes + forms — resume variants, anti-abuse endpoint, contact/dealflow, admin inbox
```

**Stats:** 161 files changed, +19,514 / −1,003. Pushed to GitHub.

---

## 2. Overall project completion status

### P0 — Foundations
| ID | Title | Status |
|---|---|---|
| TD-00..09 | Repo, agent tooling, docs, scaffolds, Docker, Alembic, Storage, Dockerfile | [x] Done (Session 1) |
| TD-10 | Stitch MCP + DESIGN.md | [x] Done (Session 3) |
| TD-11 | Design tokens → Tailwind/shadcn | [x] Done (Session 3) |
| TD-12..15 | CI: lint, tests, contract checks, E2E, deploy | [ ] Pending — blocked on CI setup |
| TD-M1..M6 | Manual infra (domain, R2, Resend, Railway, Tunnel) | [~]/[ ] User-executed |

### P1 — Backend Spine
| ID | Title | Status |
|---|---|---|
| TD-16..19 | Core data, admin auth, relevance engine, publishing | [x] Done (Sessions 1-2) |
| TD-20 | Timeline backend | [x] Done (Session 2) |
| TD-21 | Frontend shell + typegen | [x] Done (Session 2) |
| TD-22 | Timeline public + tile contract | [x] Done (Session 2) |
| TD-23 | Admin shell + CRUD | [x] Done (Session 2) |
| GATE-P1 | P1 exit checklist | [x] Verified (Session 2) |

### P2 — Content Tracks
| ID | Title | Status |
|---|---|---|
| TD-24 | Contention protocol | [x] Done (Session 3) |
| TD-25 | Track A — Projects | [x] Done (Session 3) |
| TD-26 | Track B — Skills + Certifications | [x] Done (Session 3) |
| TD-27 | Track C — Thesis + Posts | [x] Done (Session 3) |
| TD-28 | Track D — Collections + ProsePages | [x] Done (Session 3) |
| TD-29 | Track E — Resume + Forms | [x] Done (Session 3) |
| TD-30 | Track F — Intro Sequence + Ambient Audio | [x] Done (Session 3) |
| GATE-P2 | P2 exit checklist | [ ] Pending |

### P3 — Convergence
| ID | Title | Status |
|---|---|---|
| TD-31..36 | Overview, SEO, analytics, re-skin, a11y, launch | [ ] All pending |

---

## 3. What was developed this session (detail)

### Foundation (Tasks 1–4)

**TD-10 — Stitch MCP + DESIGN.md** (`docs/DESIGN.md`):
- Verified `.mcp.json` HTTP connectivity to stitch.googleapis.com
- Created DESIGN.md with complete dark theme tokens (8 colours, 7 type scale levels, 3 font families, spacing/radius/grid, motion rules)
- All colours from `overall_context/ui-design-brief.md` §4-6: amber `#E8B34B` for relevance ONLY

**TD-11 — Design tokens → Tailwind/shadcn** (`frontend/app/globals.css`, `admin/src/index.css`):
- Replaced shadcn default light-mode `:root` values with dark theme hex values
- Removed `.dark` block entirely (dark-only site)
- Set `--radius: 4px`, mapped 8 colour tokens, 3 font families
- Added `--font-display` (Archivo Black/Space Grotesk) and `--font-mono` (JetBrains Mono)
- `--primary` is achromatic (`#F2F2F0` — text colour), amber via `--relevant` only
- Hex-literal guard rule appended to `docs/conventions.md`

**TD-24 — Contention protocol:**
- `scripts/regen_migration.sh` — rebase guard, clean-tree guard, branch-migration deletion, autogenerate, single-head assertion
- `scripts/check_registries.py` — verifies every feature model imported in `models_registry.py` and every router in `app/app.py`
- `APPEND-ZONE-START`/`END` sentinels in all 4 contention files: `models_registry.py`, `app/app.py`, `frontend/lib/tiles.ts`, `frontend/lib/cacheTags.ts`
- Merge queue rules already in `docs/conventions.md` §77-78

### P2 Content Tracks (Tasks 5–9)

**Track A — Projects** (`backend/app/features/projects/`, `frontend/app/projects/`, admin):
- `Project` model: UUID, title, slug (unique), summary, description (markdown), `timeline_entry_id` FK (nullable, `ondelete="SET NULL"`), `video_url`, `topic_tags` M2M, `audience_override` ARRAY
- `ProjectAttachment`: one-to-many, kind (PDF/PPT/IMAGE), storage_key, label, sort_order
- Public pages: list (RSC + client relevance) + detail (`/projects/[slug]` with markdown, YouTube `youtube-nocookie.com`, attachment list)
- Cross-link: `/timeline#entry-{id}` — scroll-to, highlight, clears filter chips
- Admin: CRUD reusing shared P1 field components, experience picker from timeline endpoint
- Tile: Recruiters/Techies/Investors/Founders, omitted Personal/empty
- 12 integration tests

**Track F — Intro Sequence + Ambient Audio** (`frontend/components/intro/`, `frontend/components/audio/`):
- **F.T1 Intro:** 6 adjectives (CURIOUS→BOLD) accumulating at ~450ms intervals, 6 squares filling 2×3 grid, ~3s total, `cubic-bezier(0.16, 1, 0.3, 1)` easing, decorative counter in JetBrains Mono
- **F.T2 Morph:** Framer Motion `layoutId` linking loader squares → category selector tiles, continuous motion, both states mounted through transition
- **F.T3 Guards:** `sessionStorage` bypass for returning visitors, `useReducedMotion()` skip, click/Escape skip, **overlay invariant** — intro is `position: fixed` overlay ABOVE server-rendered content, NEVER conditional replacement
- **F.T4 Audio:** `<audio>` element in root layout (preserved across navigation), `sessionStorage` persistence, restore without auto-resume, off by default, HUD controls (play/pause, volume, track switch)

**Track B — Skills + Certifications** (`backend/app/features/skills/`, `backend/app/features/certifications/`):
- **Skills:** SkillSection enum (LANGUAGES/TOOLS/FRAMEWORKS/AI/BUSINESS), name, icon_slug, icon_key, sort_order. **NO topic_tags, NO audience_override** — everyone sees everything. Icon chain: Simple Icons CDN → R2 fallback → initial-letter placeholder
- **Certifications:** CertKind (TECHNICAL/BUSINESS), title, issuer, issued/expires date, credential_url, file_key/type. topic_tags M2M + audience_override ARRAY. Mobile PDF fallback: detect inline failure, show "Open PDF" link
- Tiles: Skills (all except Personal), Certs (Recruiters/Founders/Investors/Techies)
- 14 combined tests

**Track C — Thesis + Posts** (`backend/app/features/posts/`, `backend/app/features/thesis/`):
- **Posts:** PostPlatform enum, PostCollection enum ARRAY (TECH_RABBITHOLE/HOW_I_USE_AI/VC_FOR_FOUNDERS), topic_tags M2M — **collections (routing) ≠ topic_tags (relevance)**, enforced as separate relationships
- Three themed pages share ONE `PostList` component: `/tech-rabbithole`, `/how-i-use-ai`, `/vc-for-founders`
- External links with `rel="noopener noreferrer"`
- **Thesis:** title, summary, drive_url (links out — NEVER iframe), topic_tags, override
- 4 tiles: Tech Rabbithole (all 5 audiences), How I Use AI (4 audiences), VC for Founders (Founders), Investment Thesis (Investors)
- 12 combined tests

**Track D — Collections + ProsePages** (`backend/app/features/collections/`, `backend/app/features/prose/`):
- **CollectionItem:** BOOK/ANIME/MANHWA, section (books only), cover_key, external_source (OPEN_LIBRARY/JIKAN/MANUAL), status. NO topic_tags — Personal-only
- **Cover pipeline** (`collections/covers.py`): Open Library search API → download cover → store to R2 (content-hashed key). Jikan v4 for anime/manga. Validate content-type + cap size. NEVER hotlink — R2 URLs only at render time
- **ProsePage:** slug (unique), title, body (markdown), group enum (HOBBIES/WORK_VIEWS/INVESTOR_INTRO), CTA. react-markdown + remark-gfm + rehype-sanitize. `group` ≠ relevance (same separation as Post.collections)
- 5 tiles: Books + Anime & Manhwa (Personal), Hobbies (Personal), Work Views (Recruiters+Techies), Investor Intro (Founders)
- 12 combined tests

**Track E — Resume + Forms** (`backend/app/features/resumes/`, `backend/app/features/forms/`):
- **Resume:** TECH/BUSINESS variants, file_key (R2), is_active. Mapping: Recruiters+Techies → tech, Investors+Founders → business, default shows BOTH
- **FormSubmission:** CONTACT/DEALFLOW, payload JSONB, consent_text SNAPSHOT, submitter_email, ip_address, user_agent, is_read
- **Anti-abuse endpoint** (`POST /api/v1/forms/{form_type}`): honeypot → Turnstile `/siteverify` → rate limit → DB write. Generic success response regardless of outcome. Resend notification fire-and-forget
- Turnstile helper at `backend/app/core/turnstile.py`
- Contact page: email as plain DOM text, JSON-LD `Person`, LinkedIn, Cal.com, resume PDFs
- Dealflow page: consent-gated form with Turnstile
- Admin inbox: filterable, CSV export, read/unread toggle
- Tiles: Contact (all audiences, priority 10), Dealflow (Investors)
- 12 combined tests

---

## 4. Deviations from existing design

### Design adaptations
1. **Tailwind v4 instead of v3 `tailwind.config.ts`** — Both apps use Tailwind v4 CSS-based config (`@theme inline` blocks). The plan assumed v3 config file. Tokens mapped via CSS custom properties and shadcn variable names in `@theme inline` blocks. No functional difference.

2. **No separate `tailwind.config.ts` files exist** — Tokens defined directly in `globals.css` and `index.css` via the Tailwind v4 `@theme inline` directive.

3. **`bg-ink`/`bg-surface`/`bg-surface-raised` → shadcn names** — Initial Track F used design-spec CSS class names (`bg-ink`) that had no corresponding tokens. Fixed to use existing shadcn class names (`bg-background`, `bg-card`, `bg-secondary`) which already map to the same hex values.

4. **`CategorySelector.tsx` removed — inlined into `IntroOverlay.tsx`** — Initial implementation had a separate component that was never imported. Consolidated into single file to remove dead code.

### Parked findings (deferred with rulings)
1. **Stitch prompt generation skipped (TD-10)** — DESIGN.md tokens sourced from user-approved `overall_context/ui-design-brief.md` §4-6. Stitch visual refinement deferred to component implementation (Track F).

2. **Drag-to-reorder not implemented (TD-26 Skills admin)** — Manual `sort_order` number inputs are functional. Drag library (dnd-kit, react-beautiful-dnd) deferred as disproportionate complexity for P2.

---

## 5. Documents referred

| Document | Path | Purpose |
|---|---|---|
| Handoff Session 1 | `development_plan/handoff/HANDOFF-SESSION-1.md` | State after P1 completion |
| Handoff Session 2 | `development_plan/handoff/HANDOFF-SESSION-2.md` | State after Wave 6 + GATE-P1 |
| Development Plan P2 | `development_plan/development-plan-P2.md` | Full P2 track specifications |
| Development Plan P3 | `development_plan/development-plan-P3.md` | P3 convergence tasks |
| Master To-Do Index | `development_plan/todos/README.md` | All To-Do cards index |
| TD-10 card | `development_plan/todos/p0/TD-10-stitch-design.md` | Stitch MCP + DESIGN.md |
| TD-11 card | `development_plan/todos/p0/TD-11-design-tokens.md` | Design tokens to Tailwind |
| TD-24 card | `development_plan/todos/p2/TD-24-contention-protocol.md` | Contention protocol |
| TD-25 card | `development_plan/todos/p2/TD-25-track-a-projects.md` | Track A spec |
| TD-26 card | `development_plan/todos/p2/TD-26-track-b-skills-certs.md` | Track B spec |
| TD-27 card | `development_plan/todos/p2/TD-27-track-c-thesis-posts.md` | Track C spec |
| TD-28 card | `development_plan/todos/p2/TD-28-track-d-collections-prose.md` | Track D spec |
| TD-29 card | `development_plan/todos/p2/TD-29-track-e-resume-forms.md` | Track E spec |
| TD-30 card | `development_plan/todos/p2/TD-30-track-f-intro-audio.md` | Track F spec |
| GATE-P2 card | `development_plan/todos/p2/GATE-P2.md` | P2 exit checklist |
| UI Design Brief | `overall_context/ui-design-brief.md` | Design tokens, colour, typography, motion, layout |
| Tech Stack Analysis | `overall_context/tech-stack-analysis.md` | Technology decisions |
| Dependency Map | `overall_context/dependency-map.md` | Feature relationships |
| Conventions | `docs/conventions.md` | All 15 invariants + contention protocol + tile contract |
| DESIGN.md | `docs/DESIGN.md` | Design tokens (created this session) |
| Execution Plan | `docs/superpowers/plans/2026-08-09-p2-execution.md` | Session execution plan |
| SDD Ledger | `.superpowers/sdd/2026-08-09-p2-execution/progress.md` | Per-task completion + parked findings |

---

## 6. What is pending

### Block A — P0 CI/Infra (user + agent)
| ID | Title | Status |
|---|---|---|
| TD-12 | CI: ruff/mypy/ESLint/tsc + tests | [ ] |
| TD-13 | CI: OpenAPI drift + Alembic single-head | [ ] |
| TD-14 | CI: react-doctor + Playwright E2E + SSR curl | [ ] |
| TD-15 | Deploy workflow | [ ] |
| TD-M1..M6 | Manual infra (domain zone-active, R2, Resend, Railway, Tunnel) | [~]/[ ] User-executed |

### Block B — P3 Convergence
| ID | Title | Effort | Deps |
|---|---|---|---|
| TD-31 | Overview completion (arrangement, pinning, empty states, hero) | M | GATE-P2 |
| TD-32 | SEO: JSON-LD live data, sitemap/robots, canonical, llms.txt, curl suite CI | L | TD-31 |
| TD-33 | Crawler analytics (beacon, CrawlerHit, admin panel) | M | TD-32 |
| TD-34 | Re-skin: Stitch full design, token swap + leak audit, visual regression | L | TD-31 |
| TD-35 | A11y + perf: AA contrast (dimmed), keyboard/SR, CWV, react-doctor full | M | TD-34 |
| TD-36 | Launch: cutover, Access on, Sentry, restore drill, journeys, content | L | all |

### Not started
- GATE-P2 exit checklist (requires all tracks merged + verified)
- GATE-P3 exit checklist (launch gate)

---

## 7. Issues needing attention (first priority)

### Code issues (minor, non-blocking)
1. **Ruff E501 (7 instances):** Line-length violations in auto-generated Alembic migration files (`089089797167_resumes_forms.py`). Fix with `ruff format` or manual line breaks.

2. **Mypy type annotations (7 instances):**
   - `app/features/forms/schemas.py:18` — Missing type args for `dict`
   - `app/features/forms/models.py:24` — Missing type args for `dict`
   - `app/features/collections/covers.py:87` — Returning Any, expected `str | None`
   - `app/features/posts/repository.py:31` — Incompatible type for `any()` filter
   - `app/features/forms/service.py:39` — Missing type args for generic `dict`
   - `app/features/forms/tests/test_forms.py:152` — Missing type annotation
   - `app/features/forms/endpoints/router.py:115` — Returning Any, expected `bool`
   All 7 are type-safety improvements, not logic errors. 155 tests pass.

### Blocker issues (none code-side)
- **Resend OTP still mocked** — `TD-M3` (Resend domain verification) not done
- **R2 credentials not configured** — `TD-M2` pending. StorageAdapter works with MinIO locally
- **Turnstile keys** — `NEXT_PUBLIC_TURNSTILE_SITE_KEY` and `TURNSTILE_SECRET_KEY` need config
- **Railway services not provisioned** — `TD-M4..M6` pending
- **GitHub auth used single-use PAT** — A personal access token was used for this session's push. It has been revoked; switch to SSH or a scoped fine-grained token for future sessions. (Token value removed from this document for security.)

### Deferred findings (from this session)
1. Drag-to-reorder not implemented for Skills admin (manual sort_order inputs work)
2. Admin file upload widget not implemented (file_key entered as text in forms)
3. Mobile PDF fallback needs real-device verification (code path exists, untested on phone)
4. Stitch design pass not executed (DESIGN.md from approved brief)
5. Attachment upload endpoint not implemented (metadata CRUD works, file upload missing)
6. Resend email notification in forms: fire-and-forget path exists but untested without live Resend

---

## 8. Documents needed for next session

Start with these, in order:
1. **This handoff** — `development_plan/handoff/HANDOFF-SESSION-3.md` (this file)
2. **Master index** — `development_plan/todos/README.md`
3. **P3 development plan** — `development_plan/development-plan-P3.md`
4. **P3 To-Do cards** — `development_plan/todos/p3/TD-31-*.md` through `TD-36-*.md`
5. **GATE-P2 checklist** — `development_plan/todos/p2/GATE-P2.md` (verify before P3)
6. **GATE-P3 checklist** — `development_plan/todos/p3/GATE-P3.md`
7. **Design tokens** — `docs/DESIGN.md` (dark palette reference)
8. **Conventions** — `docs/conventions.md` (all 15 invariants still in force)
9. **UI Design Brief** — `overall_context/ui-design-brief.md` (binding visual rules)
10. **Manual checklists** — `development_plan/handoff/manual-checklists.md` (TD-M1..M6)

---

## 9. System design references

### Backend feature layout (14 features)
```
backend/app/features/
├── auth/            # login, OTP, session, lockout
├── certifications/  # cert entries (TECHNICAL/BUSINESS)
├── collections/     # books, anime, manhwa + cover pipeline
├── forms/           # contact + dealflow submissions, anti-abuse
├── overview/        # OverviewIntro (per-audience hero text)
├── posts/           # external link posts (3 themed pages)
├── projects/        # projects with timeline FK + attachments
├── prose/           # markdown prose pages (hobbies, work views, investor intro)
├── relevance/       # is_relevant resolver, audience_tag_map, tag CRUD
├── resumes/         # tech/business resume PDFs
├── skills/          # skills grouped by section (no relevance)
├── thesis/          # investment thesis (Drive links)
└── timeline/        # education/experience chronology
```

### State snapshot
- **Backend tests:** 155 passing (pyproject.toml: `testpaths = ["app"]`)
- **Alembic heads:** 1 (`089089797167`)
- **Registry check:** All features registered
- **Ruff:** 7 E501 (auto-gen migrations)
- **Mypy:** 7 type annotation gaps
- **Frontend TSC:** Clean
- **Admin TSC:** Clean
- **Local services:** `docker compose up -d` → Postgres :5432 + MinIO :9000
- **Frontend pages:** 13 content routes + homepage
- **Admin screens:** 7 feature CRUD screens + dashboard + login + tag map matrix
- **Tiles registered:** 14 tiles across 5 audiences
- **Key versions:** Next.js 16.3, Vite 8 + TS 6, FastAPI 0.141, SQLAlchemy 2.0.51, Tailwind v4, Framer Motion v13, uv 0.11, Python 3.13

### Migration chain (single linear)
```
base → d902650351c6 (core: enums, topic_tags)
  → fb100e58ff80 (auth: OTP, login_attempts)
  → cf9af7fc8db5 (relevance: audience_tag_map)
  → fe8ef9031bfb (timeline: entries + M2M)
  → 4fc2a3dab90d (overview: intro + seeds)
  → 06695a8acd9c (projects + attachments)
  → 762e5fa92af4 (skills + certifications)
  → fbcad7943a73 (collections + prose)
  → 089089797167 (head — resumes + forms)
```

---

## 10. Lessons learned from errors

### From Session 1 (do not repeat)
1. **`git mv` on uncommitted files fails** — commit first, then plain `mv`; git detects renames
2. **Parallel agents editing same file** causes phantom test failures — never dispatch two agents touching the same file
3. **Parallel autogenerate = multiple alembic heads** — serialize migration-generating tasks
4. **`sa.Enum(PythonEnum)` persists member NAMES by default** (`'DRAFT'` not `'draft'`) — use `values_callable=lambda obj: [e.value for e in obj]`
5. **Alembic autogenerate can't see enums with no columns yet** — hand-add CREATE TYPE, then `create_type=False`
6. **shadcn CLI v4 breaking changes** — `--base-color` flag gone, verify flags at runtime
7. **conftest imports break when moved** — import constants from `helpers.py`, never from `conftest`

### From Session 2 (do not repeat)
8. **MissingGreenlet: `updated_at` expired after flush** — explicitly set `updated_at = datetime.now(UTC)` before flush, AND serialize to dict before any async call
9. **MissingGreenlet: topic_tags uninitialized** — always set `entry.topic_tags = tags` in create; touch with `_ = entry.topic_tags` in update
10. **Enum mismatch: `.value` on string** — add `_s()` helper handling both `hasattr(v, "value")` and plain strings
11. **Test state leakage via session-scoped fixture** — function-scoped with teardown cleanup
12. **Alembic downgrade-to-base fails** — `DROP DATABASE portfolio WITH (FORCE)` then re-create
13. **Revalidation moved from service to router** — perform ORM + serialization in service, commit in service, revalidate in router after response build
14. **`from_attributes=True` triggers lazy-loads** — never use it; serialize ORM to dict in service, Pydantic from dict

### From Session 3 (do not repeat)
15. **Subagents create files but don't commit** — 4 of 9 implementation tasks required manual `git add` + `git commit` after the subagent reported DONE. Add explicit commit instructions to dispatch prompts; verify `git status --porcelain` after each subagent returns
16. **Tailwind v4 vs v3 config mismatch** — The plan assumed `tailwind.config.ts` but both apps use Tailwind v4 CSS-based config (`@theme inline`). Check actual config format in the codebase before writing dispatch prompts
17. **Design-spec CSS class names don't exist in shadcn** — `bg-ink`, `bg-surface`, `bg-surface-raised` mapped to shadcn equivalents (`bg-background`, `bg-card`, `bg-secondary`). Always verify class names resolve to actual CSS variables in `globals.css`
18. **OpenAPI + api.d.ts regeneration is consistently forgotten** — After any schema change, run `cd backend && python scripts/export_openapi.py`, then regenerate types in both frontend and admin. These files get stale silently
19. **Mypy type annotation gaps accumulate across features** — Current count: 7. Each new feature adds ~1-2 missing type-arg annotations. Consider adding `--strict` incrementally or fixing the existing 7 before starting P3

---

## Execution protocol for next session

1. Read this handoff → `todos/README.md` → P3 cards → `docs/conventions.md`
2. Begin with **GATE-P2 exit checklist** (`development_plan/todos/p2/GATE-P2.md`) — verify all 13 items before starting P3
3. P3 tasks are mostly sequential (convergence, not parallel): TD-31 → TD-32 → TD-33, TD-34 → TD-35, TD-36 last
4. Per-To-Do loop: brainstorm → plan → execute (subagents where file sets are disjoint) → code (TDD) → test → code review → verify → commit
5. **Session 2 patterns (see §10 above, items 8-14) are still mandatory** — dicts not ORM, revalidation in router, enum coercion, M2M init, `create_type=False`, no `from_attributes=True`
6. **Session 3 patterns (items 15-19) are also mandatory** — verify commits after subagent returns, check Tailwind config format, verify CSS class names resolve, regenerate OpenAPI types after schema changes
7. Backend commands from `backend/`; local services from repo root
8. Never commit secrets; `.env` files stay gitignored
9. Conventional commits: `feat(p3): ...`, `fix(p3): ...`, `chore: ...`

---

## Watch-list for P3

- **GATE-P2** must be verified before starting P3 — verify all 13 exit criteria
- **Tile contract** — P3.T1 (overview completion) depends on all 14 tiles being registered
- **Overlay invariant** — verify with `curl`, not eyes. This was the Critical risk in the P0 register
- **Dimmed content AA contrast** — P3.T5.1 measures composited values, not token values
- **`noindex` until domain cutover** — P3.T6.1 flips `NEXT_PUBLIC_INDEXABLE` only after custom domain verified
- **Revalidation tag parity** — backend `cache_tags.py` and frontend `cacheTags.ts` must stay in sync
- **OpenAPI + typegen** — regenerate after ANY schema change; commit `openapi.json` + both `api.d.ts` files together
- **Railway hostname must never be indexed** — keep `noindex` until domain live
- **Turnstile keys needed for form testing** — `TD-M2` pending
- **Run `scripts/regen_migration.sh` for each P3 track that adds models** — single head invariant
- **Never `cookies()` in content RSCs** — `next build` must report routes static
- **Do NOT overwrite `.vscode/settings.json`** — already has `python.envFile` pointing at root `.env`
