# Spec Catalog — Session 1 (Initial Build-Out, Phases P0–P3)

**Purpose:** Single index of every specification executed during the initial build-out. Canonical execution cards live in `development_plan/todos/`; this catalog maps each to its outcome and evidence so future sessions can trace any feature from plan → commit → verification without archaeology.

**How to read:** Each row points at the original card (the spec), the commit(s) that landed it, and where its verification evidence lives. Post-development narrative: `docs/post-development/session-1/post-development-report.md`. Session handoffs: `docs/handoff/HANDOFF-SESSION-{1..4}.md`.

---

## P0 — Foundations

| Card | Title | Status | Commit(s) |
|---|---|---|---|
| `todos/p0/TD-00-repo-init.md` .. `TD-09-backend-dockerfile.md` | Repo hygiene, agent tooling, canonical docs, backend/frontend/admin scaffolds, Docker Compose, async Alembic, StorageAdapter (R2/MinIO/local), multi-stage backend image | Done | `65d9f4a`, `48f14d5`, `65aaef7` |
| `todos/p0/TD-10-stitch-design.md` | Stitch MCP + DESIGN.md dark tokens | Done (tokens sourced from approved brief; Stitch visual pass deferred) | `20bcb0f` |
| `todos/p0/TD-11-design-tokens.md` | Design tokens → Tailwind v4/shadcn both apps | Done | `3966c04` |
| `todos/p0/TD-12..15` | CI quality / contract / E2E / deploy workflows | **Re-opened as session-2 specs** — see `docs/specs/session-2/S2_T05_*` and `S2_T06_*` (cards exist but no workflows had been written) |
| `todos/p0/TD-M1..M6` | Manual infra (Cloudflare zone, R2/Turnstile, Resend, Railway, Tunnel/Access) | User-executed; mostly pending — see `docs/handoff/manual-checklists.md` |

## P1 — Backend Spine

| Card | Title | Status | Commit(s) |
|---|---|---|---|
| `todos/p1/TD-16-core-data.md` .. `TD-19-publishing-revalidation.md` | Core mixins/enums/TopicTag, admin auth (Argon2+OTP+lockout), relevance engine (`audience_tag_map` + pure resolver), publishing/revalidation/cron/public_filter | Done | `65aaef7`, `9809b44`, `b8acd40` |
| `todos/p1/TD-20-timeline-backend.md` | Timeline feature slice | Done | `b47bf02` |
| `todos/p1/TD-21-frontend-shell-typegen.md` | Frontend shell, OpenAPI typegen, category cookie, relevance parity | Done | `b47bf02` |
| `todos/p1/TD-22-timeline-public-tile.md` | Timeline page, filter chips, OverviewIntro, tile contract, HUD | Done | `b47bf02` |
| `todos/p1/TD-23-admin-shell-crud.md` | Admin shell: login/guard, Timeline CRUD, tag-map matrix | Done | `b47bf02` |
| `todos/p1/GATE-P1.md` | P1 exit checklist | Verified | Session 2 |

## P2 — Content Tracks

| Card | Track | Status | Commit(s) |
|---|---|---|---|
| `todos/p2/TD-24-contention-protocol.md` | Merge queue, regen script, registry checks, append zones | Done | `d1042b8` |
| `todos/p2/TD-25-track-a-projects.md` | A — Projects (+attachments, timeline cross-link) | Done | `b07b351`, `3341087` |
| `todos/p2/TD-26-track-b-skills-certs.md` | B — Skills + Certifications | Done (real-device PDF fallback pending user) | `95bc643` |
| `todos/p2/TD-27-track-c-thesis-posts.md` | C — Thesis + Posts (3 themed pages; collections ≠ topic_tags) | Done | `91e3759` |
| `todos/p2/TD-28-track-d-collections-prose.md` | D — Collections + ProsePages (R2 cover pipeline) | Done | `e286656` |
| `todos/p2/TD-29-track-e-resume-forms.md` | E — Resume + Forms (honeypot→Turnstile→rate-limit→DB; Resend notify untested w/o live key) | Done | `29cdbda` |
| `todos/p2/TD-30-track-f-intro-audio.md` | F — Intro sequence + morph + ambient audio HUD | Done | `827f852`, `732b072` |
| `todos/p2/GATE-P2.md` | P2 exit checklist | Claimed closed session 4; **formal re-verification scheduled** — `docs/specs/session-2/S2_T04_*` |

## P3 — Convergence (built in original session 4, committed in current session 2)

| Card | Title | Status | Commit(s) |
|---|---|---|---|
| `todos/p3/TD-31-overview-completion.md` | Per-audience tile arrangement, pinning, empty states, hero | Code complete | `6a8dfde` |
| `todos/p3/TD-32-seo-discoverability.md` | JSON-LD live data, sitemap/robots/llms.txt, canonical metadata, SSR suite basis | Code complete (CI wiring in S2_T05/06) | `6a8dfde` |
| `todos/p3/TD-33-crawler-analytics.md` | CrawlerHit logging, classification, admin panel | Code complete | `6a8dfde` |
| `todos/p3/TD-34-reskin.md` | DESIGN.md v2, token audit, Playwright visual baselines | Code complete (full Stitch pass deferred) | `6a8dfde` |
| `todos/p3/TD-35-a11y-perf.md` | A11y audit doc, keyboard fixes, payload/react-doctor passes | Code complete (5 next/image conversions deferred) | `6a8dfde` |
| `todos/p3/TD-36-launch.md` | Domain cutover, Access, backup drill, content authoring | Pending — paired w/ user | — |
| `todos/p3/GATE-P3.md` | Launch gate | Pending | — |

---

## Verification snapshot after session-2 baseline (see `../session-2/S2_T01_20260822-2212_baseline-verification.md`)

169 pytest passed + 2 skipped · ruff clean · mypy clean (159 files) · exactly one Alembic head (`4d50231ae3d7`) · frontend/admin tsc clean · eslint 0 errors / 5 deferred warnings · OpenAPI + both `api.d.ts` regenerated.
