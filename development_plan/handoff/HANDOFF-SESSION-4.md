# HANDOFF — Session 4 (P3 convergence: TD-31 → TD-36)

**Written:** end of session 4 · **Next session:** TD-36 Launch (manual tasks + user input)
**Start here:** read this file, then `development_plan/todos/README.md`.

---

## 1. What was done this session

**Scope:** Closed GATE-P2 gaps (4 missing admin CRUD screens), completed all P3 convergence tasks (TD-31–TD-35), integrated GlitchTip error tracking, wrote Playwright critical journeys.

**Commits:** Not yet committed (user to commit after review).

**Stats:** ~40 files created, ~60 files modified. All 171 backend tests pass. Ruff clean. Mypy clean. Frontend/admin TSC clean.

---

## 2. Overall project completion status

### GATE-P2 → CLOSED
| ID | Title | Status |
|---|---|---|
| GATE-P2 | 13 exit criteria | [x] Verified this session |
| — | Posts admin CRUD (list + form) | [x] Built |
| — | Thesis admin CRUD (list + form) | [x] Built |
| — | Resumes admin CRUD (list + form) | [x] Built |
| — | Overview admin CRUD (list + form) | [x] Built |
| — | Sidebar nav (all 13 items) | [x] Fixed |
| — | Ruff/mypy issues (14 total) | [x] Fixed |
| — | OpenAPI + typegen refreshed | [x] Done |

### P3 Convergence
| ID | Title | Status |
|---|---|---|
| TD-31 | Overview completion (arrangement, pinning, empty states, hero) | [x] Done |
| TD-32 | SEO (JSON-LD live data, sitemap/robots, canonical, llms.txt, SSR suite) | [x] Done |
| TD-33 | Crawler analytics (beacon, CrawlerHit, admin panel) | [x] Done |
| TD-34 | Design pass (audit, visual regression, DESIGN.md v2, intro/HUD polish) | [x] Done |
| TD-35 | A11y & perf (audit report, keyboard fix, payload budget, react-doctor) | [x] Done |
| TD-36.S3 | GlitchTip error tracking (FastAPI + Next.js) | [x] Done |
| TD-36.S5 | Playwright critical journeys (5 flows) | [x] Done |
| TD-36 | Launch (S1, S2, S4, S6) | [ ] **NEXT SESSION** |

---

## 3. Key architectural decisions

### GlitchTip instead of Sentry
Chose **GlitchTip** (glitchtip.com) over Sentry for error tracking:
- **Open-source** (MIT), self-hostable on Railway
- **Sentry SDK compatible** — uses the same `sentry-sdk` Python and `@sentry/nextjs` NPM packages
- **Lightweight** — single Django+Postgres container vs Sentry's 20+ services
- Free tier: 1,000 events/month hosted; unlimited self-hosted

**Integration:** `GLITCHTIP_DSN` env var in both backend (`app/core/glitchtip.py`) and frontend (`sentry.*.config.ts`). Both apps skip init when DSN is unset.

### Visual regression
Playwright configured with 3 breakpoints (mobile/tablet/desktop). 12 of 13 pages captured as baseline screenshots in `frontend/tests/visual/home.spec.ts-snapshots/`.

---

## 4. State snapshot

```
Backend:  ruff ✅ · mypy ✅ · 171 tests ✅
Frontend: TSC ✅ · Playwright configured · Sentry configs ready
Admin:    TSC ✅ · 13 sidebar nav items · All 11 form mutations with cache invalidation
Alembic:  1 head (4d50231ae3d7 — crawler_hits table)
codegraph: 268 files, 2,865+ nodes
```

### New files created this session (~40)
- `admin/src/routes/posts/PostList.tsx`, `PostForm.tsx`
- `admin/src/routes/thesis/ThesisList.tsx`, `ThesisForm.tsx`
- `admin/src/routes/resumes/ResumeList.tsx`, `ResumeForm.tsx`
- `admin/src/routes/overview/OverviewList.tsx`, `OverviewForm.tsx`
- `admin/src/routes/crawlers/CrawlerHits.tsx`
- `admin/src/components/fields/CollectionsSelect.tsx`
- `frontend/config/tileArrangement.ts`
- `frontend/lib/jsonld.ts`
- `frontend/app/sitemap.ts`, `robots.ts`, `llms.txt/route.ts`
- `frontend/sentry.client.config.ts`, `sentry.server.config.ts`, `sentry.edge.config.ts`
- `frontend/playwright.config.ts`
- `frontend/tests/visual/home.spec.ts`
- `frontend/tests/accessibility/a11y.spec.ts`, `keyboard.spec.ts`
- `frontend/tests/journeys/critical.spec.ts`
- `backend/app/features/crawlers/` (full feature slice)
- `backend/app/core/glitchtip.py`
- `backend/alembic/versions/7f3ad874fddf_add_is_pinned_*.py`
- `backend/alembic/versions/4d50231ae3d7_add_crawler_hits_*.py`
- `docs/a11y-perf-audit.md`
- `docs/DESIGN.md` (v2.0 — refined from visual analysis)

### Migration chain (single linear)
```
base → d902650351c6 → fb100e58ff80 → cf9af7fc8db5 → fe8ef9031bfb
  → 4fc2a3dab90d → 06695a8acd9c → 762e5fa92af4 → fbcad7943a73
  → 089089797167 → 7f3ad874fddf (is_pinned) → 4d50231ae3d7 (crawler_hits, HEAD)
```

---

## 5. What is pending — NEXT SESSION

### Block A — Manual infra (user-executed)
| ID | Task | Checklist |
|---|---|---|
| TD-M1 | Cloudflare zone verification | `handoff/manual-checklists.md` |
| TD-M2 | R2 bucket + Turnstile + Web Analytics | `handoff/manual-checklists.md` |
| TD-M3 | Resend domain verification | `handoff/manual-checklists.md` |
| TD-M4 | Railway services provisioning | `handoff/manual-checklists.md` |
| TD-M5 | Railway auto-deploy OFF + token | `handoff/manual-checklists.md` |
| TD-M6 | Cloudflare Tunnel + Access | `handoff/manual-checklists.md` |

### Block B — TD-36 Launch (paired)
| Step | Task | Owner |
|---|---|---|
| TD-36.S1 | Domain cutover → TLS → flip NEXT_PUBLIC_INDEXABLE → submit sitemap | User + agent |
| TD-36.S2 | Enable Cloudflare Access (single-hostname) | User |
| TD-36.S4 | Backup restore drill → scratch DB | User |
| TD-36.S6 | Real content authoring (see `content-authoring-checklist.md`) | User |
| — | Provision GlitchTip instance → set GLITCHTIP_DSN | User |

### Block C — Verification (agent, after content authored)
| Task | Command |
|---|---|
| Run Playwright visual baseline | `cd frontend && npx playwright test tests/visual/ --update-snapshots` |
| Run Playwright critical journeys | `cd frontend && npx playwright test tests/journeys/` |
| Run a11y tests | `cd frontend && npx playwright test tests/accessibility/` |

---

## 6. New env vars

| Var | Where | Purpose |
|---|---|---|
| `GLITCHTIP_DSN` | Backend + Frontend | GlitchTip error tracking DSN (Sentry SDK compatible) |
| `NEXT_PUBLIC_GLITCHTIP_DSN` | Frontend | Client-side GlitchTip DSN |
| `NEXT_PUBLIC_CF_BEACON_TOKEN` | Frontend | Cloudflare Web Analytics beacon token (TD-33) |

---

## 7. Lessons from this session

1. **Stitch MCP tools not available** — the HTTP MCP server at `stitch.googleapis.com/mcp` is configured but tools weren't loaded. Manual design analysis via screenshots + vision model worked as fallback.

2. **Admin CRUD gaps from Session 3** — Posts, Thesis, Resumes, and Overview had backend APIs but no admin UI. Built them following the existing TimelineForm/TimelineList patterns with shared field components.

3. **Query invalidation was missing** — All 11 admin form mutations lacked `queryClient.invalidateQueries()`. Added in all files.

4. **Sentry self-hosted is ~20 services** — impractical for a portfolio site. GlitchTip is a single Django container that accepts Sentry SDKs natively. Same code, lighter infra.

5. **Visual regression needs content** — baseline screenshots captured intro overlay rather than actual page content because DB is empty. Re-capture after content authoring (TD-36.S6).

---

## 8. Execution protocol for next session

1. Read this handoff → `todos/README.md` → P3 cards → `docs/conventions.md`
2. Execute manual tasks TD-M1..M6 (user) — checklists at `handoff/manual-checklists.md`
3. TD-36.S1: Point domain at Railway services, verify TLS, flip `NEXT_PUBLIC_INDEXABLE`
4. TD-36.S2: Enable Cloudflare Access (single-hostname for admin + /api/*)
5. TD-36.S4: Verify Railway Postgres backup policy, test restore
6. TD-36.S6: Author real content via admin UI (use `content-authoring-checklist.md`)
7. Provision GlitchTip: self-hosted on Railway or hosted free tier → set `GLITCHTIP_DSN`
8. Agent: run Playwright journeys + a11y tests + re-capture visual baseline
9. Commit all pending changes with conventional commits

---

## 9. Documents for next session

1. **This handoff** — `development_plan/handoff/HANDOFF-SESSION-4.md`
2. **Manual checklists** — `development_plan/handoff/manual-checklists.md`
3. **Content authoring checklist** — `development_plan/handoff/content-authoring-checklist.md`
4. **Env vars registry** — `development_plan/handoff/env-vars-registry.md`
5. **DESIGN.md v2** — `docs/DESIGN.md`
6. **A11y/Perf audit** — `docs/a11y-perf-audit.md`
7. **Conventions** — `docs/conventions.md`
8. **P3 development plan** — `development_plan/development-plan-P3.md`
9. **Handoff Session 3** — `development_plan/handoff/HANDOFF-SESSION-3.md` (for prior context)
