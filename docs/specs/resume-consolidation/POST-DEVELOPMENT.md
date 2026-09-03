# Post-Development — Resume Consolidation (2026-08-30)

**Scope:** D1–D9 + pgBouncer (Point 1) + superset canon seed. Build mode, sub-agent driven, `verification-before-completion`.

## Decisions recorded
- **D1 A:** `resumes.variant` `ENUM(TECH|BUSINESS)` → `VARCHAR(50)` `String` with 6-string allowlist (`business, generic, vc, ai_consultant, ai_workflow, product_engineer`). Migration `869fc8d8c856_widen_resume_variant_to_string.py:50`, `down_revision=4d50231ae3d7`, single head.
- **D2:** Contact shows filtered resumes per audience via `ResumeAudienceMap`; `default` shows all 6 for crawlers; `Show everything` removed from HUD + intro selector (crawler `default` remains but not user-selectable). `ContactTile:9` already `audiences=[]` → visible to all.
- **D3:** Feenix Sports `2026-07–Present` added as separate published, `is_pinned=true`, merged bullets from 3 AI/Product PDFs.
- **D4:** Umbrella `Purdue Data Mine — Umbrella 2024-08–2026-05` retained (`[Umbrella]` prefix, `sort_order=20`, publishable, deletable via admin) + 4 split client entries + Feenix Sports.
- **D5 superset:** 14 timeline entries (2 edu + 12 exp) highlights deduped across 6 PDFs; 5 projects; 43 skills; lineage noted in `resume_canon.json: _meta`.
- **D6:** Full skills superset (43 rows, 5 sections) per PDFs, section mapping preserved, `subsection` for grouping.
- **D7:** Projects seeded with `timeline_entry_id_key` → UUID resolution; Option 2 timeline detail lives in `docs/specs/timeline-detail/`.
- **D8:** `resumes/*.pdf` gitignored, `resumes/.gitkeep` tracked; storage+DB source of truth.
- **D9 gate:** `backend/scripts/resume_canon.json` is canonical input; `seed_resumes.py --dry-run` before write.
- **Point 1 pgBouncer:** approved, sidecar on `6432`, pool `10/5`, `pool_pre_ping`, `NullPool` avoided.

## Artifacts
- `backend/scripts/resume_canon.json:1` — single source of truth (11 topic_tags, 14 timeline inc umbrella, 5 projects, 43 skills, 6 resumes, 6 overview_intros)
- `backend/scripts/seed_resumes.py:1` — idempotent UPSERT (content-hash `resumes/{variant}-{sha12}.pdf` via `get_storage().put`, topic-tag upsert, timeline `key`→natural tuple, projects `slug`, skills `name+section`, overview `audience`; flags `--pdfs-only/--canon-only/--dry-run`; revalidation `[timeline,projects,skills,resumes,overview,relevance]`)
- `backend/app/features/resumes/models.py:12` — `ALLOWED_VARIANTS/VARIANT_LABELS`, `String(50)`
- `backend/app/features/resumes/schemas.py:1`, `service.py:12`, `repository.py:12` — allowlist validators, string unwrap
- `backend/alembic/versions/869fc8d8c856_*` — `VARCHAR(50) USING LOWER(...)`, `DROP TYPE resume_variant`
- `admin/src/routes/resumes/ResumeForm.tsx:31` / `ResumeList.tsx:9` — 6 variant options, badge labels; `frontend/app/contact/page.tsx:1` + `ContactResumes.tsx:1` — audience-filtered grid, RSC static (no `cookies()`); `frontend/lib/cacheTags.ts:19` unchanged (RESUMES)
- `backend/openapi.json:1` regenerated, `frontend/src/api.d.ts:916` + `admin/src/api.d.ts` regenerated
- `.gitignore:4` — `resumes/*.pdf` + `!resumes/.gitkeep`

## Local verification (real Postgres, no mocks per conventions 5)
- `uv run --project backend python backend/scripts/seed_resumes.py --canon backend/scripts/resume_canon.json --dry-run` → 11 tags, 14 timeline, 5 projects, 43 skills, 6 resumes, 6 intros; real run → 6 PDFs to `.storage/resumes/*` `140–188KB`, DB `20 topic_tags, 34 timeline (14+20 E2E), 6 projects, 43 skills, 6 resumes`, revalidation fired
- `uv run --project backend pytest backend/app/features/resumes backend/app/features/timeline backend/app/features/projects -q` → **42 passed**
- `uv run --project backend pytest backend/app/features/resumes/tests/test_seed_resumes.py -q` → **9 passed** (hash determinism, key format, allowlist, idempotent upsert)
- `uv run --project backend ruff check backend/app` → **All checks passed** (after E501/F841 fixes)
- `npm run build --prefix frontend` → **20 pages**, `○ /contact` static, no `cookies()` in RSC
- `npm run build --prefix admin` → **1993 modules, gzip 143KB**
- `alembic heads` → `869fc8d8c856 (head)` single head; `docker compose config` valid

## Production seeding (repeat after secrets set)
```bash
railway link  # project awake-success, env production
railway run --service backend -- uv run python backend/scripts/seed_resumes.py --canon backend/scripts/resume_canon.json --dry-run
railway run --service backend -- uv run python backend/scripts/seed_resumes.py --canon backend/scripts/resume_canon.json
curl -s https://backend-production-7a2a.up.railway.app/api/v1/resumes | jq '.[].variant'
curl -s https://backend-production-7a2a.up.railway.app/api/v1/timeline | jq 'length'
curl -s https://frontend-production-38ac.up.railway.app/contact | grep -i pdf
bash scripts/check_ssr.sh --all https://frontend-production-38ac.up.railway.app
```
Volume is at `/data` → `/media` serves PDFs as absolute `file_url` (`MEDIA_BASE_URL=https://admin.siddhesh-chaudhari.com`); bridge `NEXT_PUBLIC_API_BASE_URL` reverts after DNS cutover per `SESSION-HANDOFF` §4.

## Follow-ups (admin-editable)
- Feenix Sports bullets / umbrella visibility are admin-editable; user will triage via admin portal.
- Remaining D7 timeline detail is in `docs/specs/timeline-detail/POST-DEVELOPMENT.md`.
