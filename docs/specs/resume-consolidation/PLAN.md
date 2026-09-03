# Plan: Resume Consolidation → Admin + Frontend

**Date:** 2026-08-30 · **Status:** DRAFT — awaiting clearance per your "get things cleared" gate
**Source PDFs:** 6 files in `resumes/` (business, generic, vc, ai_consultant, ai_workflow_engineer, product_engineer) — extracted via `pymupdf` (see analysis below)
**Goal:** Every common role is consolidated once, every resume-specific bullet is preserved in the canonical record, everything is entered via admin-portable structures (DB, not just PDFs), and surfaced on the correct frontend pages per audience.

---

## 1. What the 6 resumes actually contain (extracted canon)

### 11.1 Common skeleton (present in all 6 with same employer + dates, different title/bullets)

| Canonical role | Dates | Shared title drift | Why it matters |
|---|---|---|---|
| **PwC (PricewaterhouseCoopers)** — Mumbai | July 2022 – July 2024 | Technology Consultant (Product Owner) everywhere | 3 clients, 27 workflows, 48 features, 100K–3M invoices/yr, 40% KPI, <$4 cost/invoice, 6 workshops, 32 docs, 6 QA dashboards 120 defects — unanimous |
| **Evonik** (Data Mine) | Jan 2025 – May 2025 | TPM / TPM & Product Developer / Data Scientist & Product Owner | 30 min → <1 min (96%), 870K-row PostgreSQL+FastAPI, 12 features, private-cloud adoption |
| **Microsoft** (Data Mine) | Aug 2024 – Dec 2024 | Software Engineer / Data Scientist & Product Owner | 1,000 images + 240 videos, 4 LLMs, +40% over RoBERTa, 1–2 h saved, auto-translate, PySpark/Databricks |
| **Boxsy** (Data Mine) | Aug 2025 – Dec 2025 | TPM / Data Scientist & Product Owner | 14 people, 3 sub-teams, 6 CRM/DB integrations, 7 AI agents, 4 OKRs, 30+ stories, Jira–GitHub–Vercel CI/CD |
| **Launch Factory** | Aug 2025 – Dec 2025 | Venture Intern / VC & Venture Studio Intern | Scout Data/Productivity, diligence, 5+ portfolio startups, CRM + n8n/Python automations |
| **Feenix Group** (Data Mine) | Aug 2025 – May 2026 | Product Engineer / TPM & Product Developer / Data Scientist & Product Owner | ads platform, 6-feature roadmap, React+FastAPI+Lua+LangGraph, analytics, multi-format delivery |
| **Purdue** (MS Eng Mgmt) | Aug 2024 – May 2026 | same + VJTI 2018–2022 Mech, GPA 3.6 | unanimous |
| **Venture Fund / Gaus / ELI / Boilermaker** | 2024–2025 | Project Lead / Strategy Consultant / Venture Associate | Gaus YC S25 7 people, Fund 5 people diligence, ELI 42 events $40K–90K, Boilermaker 12 opps 13 domains |

### 1.2 Resume-specific points (only in some PDFs — the "gaps" we must NOT drop)

| Resume | Exclusive / emphasized bullets (must be merged into canon) |
|---|---|
| **Business** (TPM/Consultant/VC lens) | Purdue Data Mine umbrella role Jan24–May26 framing; 11-sprint Boxsy roadmap wording; Evonik "11 sprint-based roadmap features, data scraping/architecture"; Gaus + Boilermaker only together here and VC resume |
| **Generic** (Product Builder, `github.com/SIDDHESHCHAUDHARI2K24`) | Feenix Group specifics: "requirements workshops → 6 features (accessories/ads/interaction)", arch/UI/UX agentic flows, prototype React/FastAPI/Lua automating 4 streams; Boxsy KPI tracked dev speed + AI accuracy; agentic job-application platform at Purdue elective |
| **VC** | Adds investment thesis link + product proposal link in summary; Purdue VC networking note (Bay Area/Midwest scouting); same Gaus/Fund/ELI/Boilermaker block as Business |
| **AI Consultant** (`July 2026 – Present` Feenix Sports row appears) | **New employer: Feenix Sports Product Engineer July 2026–Present** — self-serve ads 0.5M–2M impressions 6 titles/2 studios, 1 of 2 eng, prod support/incident; Launch Factory deep: n8n stack Pitchbook/Crunchbase/S&P IQ/Notion, enrichment+LLM memos+CRM write-back, **20 min/company**; Selected engagements as condensed block |
| **AI Workflow Engineer** | Same Feenix Sports but as **event-tracking service** on Railway 0.5M–2M, CRM models/dashboards, AI NPC + companion SDKs over authenticated APIs; Launch Factory adds **sourcing automation Product Hunt/communities LLM classification scoring vs thesis weekly**, templates+SOPs; Evonik schema+ingestion 870K wording; Integration/Services skill taxonomy (REST, webhooks, OAuth, rate limiting, retries) |
| **Product Engineer** | Same Feenix Sports but as **scaled ads tracking algorithm** 0.5M–2M, building AI NPC/social bots, **Fortnite/Unreal extension**, **IP & compliance for tech transfer Purdue+IU** + CRM revenue dashboards; Boxsy Jira–GitHub–Vercel pipeline explicit; Evonik isolating 3 pain-points (CSV/role-based/saved matrix) |

**Skills drift:** Business/VC lean `Python/SQL/SAP ABAP/AWS/Databricks/PowerBI/Tableau/n8n/Zapier/Jira/Pitchbook`; Generic leans `Python/SAP/C++/TS/Lua/RAG/Pytest`; AI Consultant leans `n8n/LangGraph/MCP/Agentic workflows/evals/guardrails`; AI Workflow leans `TypeScript/FastAPI/PostgreSQL/Docker/Railway/Terraform/CI/CD`; Product Engineer leans `Figma/RAG/Pytest`. All must merge.

### 1.3 Decision already visible

* **Feenix Sports July 2026–Present** exists in only 3 PDFs but is the *current* role — it must be a distinct `TimelineEntry` (not merged into Feenix Group May 2026). Keeping it as one canonical entry with a superset of the 3 variant bullets preserves chronology and avoids duplication.
* **Purdue Data Mine umbrella** (Business/VC) collapses 4 clients into one timeline row in those PDFs, but Generic/AI/* split them — canonical needs the **split** (one timeline row per client/period) so relevance, tags, and project cross-links are addressable. The umbrella becomes admin convenience, not a DB row.

---

## 2. Gaps vs. existing models/admin/frontend

### 2.1 Resume model — too narrow

`backend/app/features/resumes/models.py:12` — `ResumeVariant` is a Postgres native enum with only `TECH`/`BUSINESS`. Six PDFs map to at least **6 intents**: `business`, `generic`, `vc`, `ai_consultant`, `ai_workflow_engineer`, `product_engineer`. Two-value enum forces lossy collapse (VC → business, AI* → tech). Admin currently supports exactly 2 rows before semantics break; `is_pinned`/`status` missing (unlike other content). Frontend `frontend/app/contact/page.tsx:37` does `find(r => r.variant === "tech")` / `"business"` only — 4 variants would be invisible/download-unlinked even if seeded.

**Invariant risk:** Postgres native enum requires `ALTER TYPE` to add values (`docs/conventions.md:7`). Existing rows pin the type.

### 2.2 Timeline — no schema gap, but data consolidation + relevance wiring needed

`TimelineEntry` (`backend/app/features/timeline/models.py:49`) already has `highlights: JSONB`, `topic_tags` M2M, `audience_override: ARRAY(Audience)`, `PublishableMixin` with `is_pinned`. That is sufficient — the gap is **data completeness** and **tag map population**: the audience mapping for each consolidated role needs to be set so recruiters/techies/investors/founders highlighting (`core/relevance.py`) and tile logic are correct. Existing topics are likely seeded minimally; new tags for `agentic-ai`, `venture-capital`, `adtech`, `sap-erp`, etc. may be absent.

### 2.3 Projects — under-represented

`backend/app/features/projects/models.py:1` expects a first-class `Project` per shippable system. Today only the Data Mine umbrella exists as timeline rows. Canonical should yield at least: **Feenix ads platform** (main), **Boxsy investor-startup matching**, **Evonik affinity matrix**, **Microsoft sentiment pipeline** (as separate projects with `timeline_entry_id` cross-link + topic tags). Without them, `/projects` and the `buildProjectsTile` show an incomplete portfolio.

### 2.4 Skills — superset merge needed

`SkillSection` enum (`backend/app/features/skills/models.py:15`: LANGUAGES/TOOLS/FRAMEWORKS/AI/BUSINESS) fits, but payload is fragmented across PDFs. Business-only skills (`SAP ABAP`, `SAS`, `Zapier`, `S&P IQ`) and AI-specific ones (`MCP`, `LangGraph`, `vector search`, `evals`) need to coexist as one admin-manageable superset. No schema change unless we want a new section value — keep mapping to existing 5.

### 2.5 OverviewIntro — opportunity, not gap

`OverviewIntro` (`backend/app/features/overview/models.py:17`) ships per-audience headline/body already (6 rows: default/recruiters/techies/investors/founders/personal). The 6 resume summaries are per-lens copy that maps naturally to those rows — we should propose overwriting/expanding that copy from the PDFs rather than inventing a new model.

### 2.6 Ingestion path — missing

No `scripts/seed_resumes.py` exists. `scripts/seed_e2e.py:1` is the only seeder and only writes `E2E Seed*` rows. Uploading PDFs today is manual via Admin UI per file; storing them needs `StorageAdapter` (`app/core/storage.py:119` already handles `/media` vs MinIO via `MEDIA_BASE_URL`) with content-hashed keys (`{variant}-{sha256[:12]}.pdf`). No canonical JSON artifact checked in, so re-seed is non-deterministic and review requires re-reading PDFs.

---

## 3. Proposed changes (what sub-agents will build AFTER you clear gaps)

### 3.1 Canonical artifact (single source of truth for review)

`backend/scripts/resume_canon.json` — hand-edited once from the analysis above, reviewed by you, then the only input sub-agents may ingest. Shape:

```json
{
  "timeline_entries": [
    {
      "kind": "education",
      "title": "M.S. Engineering Management (Product / Data)",
      "organisation": "Purdue University",
      "location": "West Lafayette, IN",
      "start_date": "2024-08-01",
      "end_date": "2026-05-31",
      "summary": "GPA 3.6… built agentic AI job-application platform …",
      "highlights": ["built agentic AI platform …", "Coursework: Corporate Consulting …"],
      "audience_override": [],
      "tag_slugs": ["engineering", "product-management"],
      "is_pinned": false,
      "status": "published"
    }
  ],
  "projects": [
    {
      "title": "Feenix — Programmatic In-Game Ads Platform",
      "slug": "feenix-ads-platform",
      "summary": "Self-serve ads on Roblox … 0.5M–2M impressions 6 titles/2 studios",
      "description": "Scoped 6-feature roadmap … React/FastAPI/Lua/LangGraph …",
      "timeline_entry_id": null,
      "tag_slugs": ["adtech", "agentic-ai", "platform-engineering"],
      "is_pinned": true,
      "status": "published"
    }
  ],
  "skills": [
    {"name": "SAP ABAP", "section": "business", "subsection": "ERP & Data Pipelines", "icon_slug": "sap", "sort_order": 10}
  ],
  "resumes": [
    {"variant": "business", "label": "Business / TPM Resume", "source_pdf": "Siddhesh Chaudhari Business Resume.pdf"},
    {"variant": "generic", "label": "Product Builder Resume", "source_pdf": "Siddhesh Chaudhari Resume.pdf"},
    {"variant": "vc", "label": "Venture Capital Resume", "source_pdf": "Siddhesh Chaudhari VC Resume.pdf"},
    {"variant": "ai_consultant", "label": "AI Consultant Resume", "source_pdf": "Siddhesh_Chaudhari_AI_Consultant_Resume.pdf"},
    {"variant": "ai_workflow", "label": "AI Workflow Engineer Resume", "source_pdf": "Siddhesh_Chaudhari_AI_Workflow_Engineer_Resume.pdf"},
    {"variant": "product_engineer", "label": "Product Engineer Resume", "source_pdf": "Siddhesh_Chaudhari___Product_Engineer_Resume.pdf"}
  ],
  "overview_intros": [
    {"audience": "recruiters", "headline": "…", "body": "…"},
    {"audience": "investors", "headline": "…", "body": "…"}
  ]
}
```

You review this JSON, not 6 PDFs. Invariant: JSON is the only ingester input; PDFs supply resume binaries only.

### 3.2 Backend: resume variant widening

**Option A (preferred, forward-compatible):** migrate `resumes.variant` from native enum to plain `String` (or keep enum but widen). Recommended: `variant: Mapped[str] = mapped_column(String(50), nullable=False)` plus a service-level allowlist of the 6 values above + any future ones (no DB enum to ALTER). Migration generated via `scripts/regen_migration.sh` after rebase.

**Option B (strict enum):** `ALTER TYPE resume_variant ADD VALUE 'ai_consultant', ...` in the migration's `upgrade()` and document in `conventions.md:7` manual-ALTER note.

**Ask you to choose.** Default if unanswered: **A** (string).

Additional `Resume` columns (optional — pending your answer on Q-states):
- `audience: str | None` or reuse `variant` — controls which audience sees which download on `/contact` (today it's hardcoded `find(r.variant === "tech")`).
- `sort_order: int` + `PublishableMixin` parity is *not* needed (resumes are always visible), but `is_active` stays.
- Add `description: str | None` to show per-variant blurb on frontend without re-parsing PDFs.

### 3.3 Backend: ingestion scripts

* `backend/scripts/seed_resumes.py` — idempotent UPSERT per canonical record, guarded by `source_pdf` hash / `title+organisation+start_date` dedupe, writes via service/repository layers (not raw SQL), triggers revalidation tags `[timeline, projects, skills, resumes, overview]`. Two modes:
  * `--pdfs-only` — upload PDFs via `get_storage().put(key, data, "application/pdf")` with key `resumes/{variant}-{hash[:12]}.pdf`, then upsert `Resume(file_key=key)`.
  * `--canon backend/scripts/resume_canon.json` — seed Timeline/Project/Skill/Overview rows + ensure TopicTags exist.

* `backend/scripts/seed_e2e.py` stays untouched; new seeder is separate so e2e fixture remains deterministic.

Tests per ingestion path use **real Postgres** (`conventions.md:5` repo never mocks DB for query logic) + MinIO or local disk adapter.

### 3.4 Frontend: surface consolidated data

No new routes. Changes:
* `/timeline` — chronological unified list already consumes `TimelineEntry`; superset highlights render via `TimelineClient:1`. No code change beyond data.
* `/projects` — new project cards cross-linked to timeline entries (uses `ProjectsTile` / detail `app/projects/[slug]/page.tsx:1` already).
* `/skills` — sectioned display already groups by `section/subsection`; superset renders as more rows.
* `/contact` — expand from 2 `find()` calls (`frontend/app/contact/page.tsx:38`) to a **grid of all 6 resume downloads**, grouped by audience intent, with `file_url` resolved via backend (`resumes/file_url:1` already absolute env-aware per `HANDOFF-RAILWAY-INFRA-PLAN.md:16`).

### 3.5 Admin: data authority stays admin-editable

* `admin/src/features/resumes/ResumeList.tsx:1` + `ResumeForm.tsx:1` already support CRUD; widening variant to 6 values only requires adding options in the Select and displaying `file_url`.
* `admin/src/routes/timeline/TimelineForm.tsx:1` / `TimelineList.tsx:1` already enforce `highlights`, `topic_tags`, `audience_override`.
* `admin/src/routes/projects/ProjectForm.tsx:1` and skills forms are superset-ready.

No admin schema break — entries remain editable, ingested rows are just pre-filled.

### 3.6 Docs + verification

* Post-ingestion runbook `docs/handoff/RESUME-CONSOLIDATION.md` (source of truth for which bullet came from which PDF, and why Feenix Sports is a separate row).
* Commits conventional (`feat(backend): broaden resume variant`, `feat(backend): seed consolidated canon`, `feat(frontend): render all resume variants`), one logical change per commit (`conventions.md` style).
* Verification: `pytest app/features/resumes app/features/timeline app/features/projects app/features/skills` (34+ existing), `npm run build` (clean tsc), `scripts/check_registries.py`, grep for ` variant` / hex literals remains clean, `curl /api/v1/timeline | jq 'length'`, `/api/v1/resumes | jq '.[].variant'`, `/contact` HTML contains all 6 PDFs.

---

## 4. Decisions I need you to clear before sub-agents start

Answer with `A/B/keep` or a sentence — I will record each decision explicitly in the plan so we do not revisit it.

**D1 — Resume variant representation** (models gate)
* [ ] **A (recommended):** widen `resumes.variant` to `String` with 6 string values (`business`, `generic`, `vc`, `ai_consultant`, `ai_workflow`, `product_engineer`) — future-proof, no ALTER TYPE.
* [ ] **B:** keep Postgres native enum and `ALTER TYPE` to add the 4 new values.

**D2 — Resume audience mapping on `/contact`**
* Should each variant be tied to an audience for filtered display (e.g., `techies → ai_workflow + product_engineer`, `investors → vc + business`, `recruiters → business + generic`, `default → all`)? Or render all 6 for everyone? Current code shows only `tech`/`business` per audience.

**D3 — Feenix Sports as separate timeline entry**
* Confirm: keep **July 2026–Present Feenix Sports** as its own published `TimelineEntry` (EXPERIENCE) with merged bullets from the 3 AI/Product PDFs, even though it's dated after today. If you prefer it to stay as "future" and not publish yet, I will seed it as `scheduled`/`draft`.

**D4 — Purdue Data Mine umbrella**
* Keep the historical umbrella row (`Purdue Data Mine – All clients, Aug 2024–May 2026`) anywhere, or delete it in favor of the 4 split client entries (Feenix Group / Boxsy / Evonik / Microsoft)? My proposal: **delete umbrella, keep 4 splits** (Boxsy+Launch Factory keep their own dates).

**D5 — Highlights merge strategy**
* For each canonical role, I propose superset-merge: dedupe bullets, keep quantified impacts (`870K rows`, `0.5M–2M`, `20 min/company`, `3h→30min`, `40%`) from every PDF where they appear. Confirm, or prefer per-resume fidelity (one entry per PDF per role)?

**D6 — Skills superset policy**
* Seed **all** skills found across 6 PDFs as one unified skill list under the existing 5 sections (grouping by `subsection` where available). Anything not mappable stays in `subsection` text. Confirm, or want a triaged "keep only X" filter?

**D7 — Projects to seed**
* From canon I propose 4 projects: `feenix-ads-platform`, `boxsy-investor-startup-matching`, `evonik-affinity-matrix`, `microsoft-sentiment-pipeline`. Add `launch-factory-automation` as a 5th? Confirm which to include; tiles will auto-appear on `app/page.tsx:49` and on `/projects`.

**D8 — Ingestion split**
* PDFs go to storage now via `seed_resumes.py --pdfs-only`; you keep PDFs in `resumes/` **gitignored** (`*.pdf` already untracked enough) and storage+DB are the deployment source of truth. Confirm, or want PDFs checked into git/LFS so the Railway volume can be rebuilt from repo?

**D9 — Approval of canonical JSON**
* After you answer D1–D8, I will author `backend/scripts/resume_canon.json` for your review. Sub-agents will not write to DB until you approve that JSON (`verification-before-completion`). Confirm this gate.

---

## 5. What happens after clearance (sub-agent workflow as you prescribed)

> Loop per task: `brainstorm → plan → execute → code → test → code review → verify → commit`. Each stage uses `superpowers:*` as applicable; frontend steps add `react-doctor` per `docs/conventions.md`.

**Batch 1 — infra closeout (serial, paired):** secrets + volume + domain (you) → `railway variables` + redeploy (agents) → `verify` (scripts/check_ssr + /health). Does not block batch 2 beyond requiring DB reachability.

**Batch 2 — resume consolidation (parallel where dependencies allow, per `dependency-map.md:8` append-only protocol)**

| Sub-agent | Scope | Gate |
|---|---|---|
| `a-resume-variant` | `resumes` model migration + service/frontend/admin variant widening + OpenAPI regen (`frontend/src/api.d.ts:1` + `admin/src/api.d.ts:1`) + `ruff`/`mypy`/`tsc` | needs **D1** |
| `b-resume-pdfs` | `seed_resumes.py --pdfs-only` + storage_put with content-hash keys + tests vs real Postgres/MinIO, upload 6 PDFs to `/media/resumes/*` | needs **D1**, **D8** |
| `c-canon-timeline` | populate `resume_canon.json` timeline slice + seed via `timeline` service + tag upsert (`core/models.TopicTag:1`) | needs **D3–D5**, **D9** |
| `d-canon-projects` | populate projects slice + cross-links + `cacheTags.ts:PROJECTS` if needed | needs **D7**, **D9** |
| `e-canon-skills` | populate skills superset + Simple Icons preview path (`admin/src/routes/skills/SkillsForm.tsx:47`) | needs **D6**, **D9** |
| `f-frontend-contact` | render all resume variants on `/contact` + audience grouping if **D2** says filtered | needs **D2** + `b` |

Each writes its own `docs/specs/resume-consolidation/<task>/POST-DEVELOPMENT.md` before `commit`. `verify` before claims: `pytest`, `npm run build`, `check_registries.py`, `check_ssr.sh`, `git diff --stat` hygiene, manual `/contact` curl for PDFs.

**Batch 3 — prod seeding** (after Batch 2 green + secrets set): `railway run --service backend -- uv run python scripts/seed_resumes.py --canon backend/scripts/resume_canon.json` then `curl https://admin.siddhesh-chaudhari.com/api/v1/resumes` + frontend SSR pass.

---

## 6. How to respond to unblock

Reply with **one line per decision**, e.g.:

```
D1: A
D2: filtered per audience (specify mapping)
D3: yes separate entry, publish as published
D4: delete umbrella
D5: superset merge
D6: all skills superset
D7: 4 projects, skip launch-factory as standalone
D8: gitignore PDFs, storage is source of truth
D9: gate approved
```

Or call out any you want to revise — I will re-plan only that slice before starting sub-agents.

