# Post-Development Recap — 2026-08-30 (Resume Canon + Timeline Detail + pgBouncer)

**Session type:** build · **Approach:** sub-agent driven, `superpowers:*` loop `brainstorm→plan→execute→code→test→review→verify→commit`, `react-doctor` on frontend, `verification-before-completion`

## What shipped this session
1. **Resume consolidation (superset, D1–D9):** variant widened `TECH/BUSINESS`→6-string, `resume_canon.json` (11 tags, 14 timeline incl umbrella+Feenix Sports, 5 projects, 43 skills, 6 resumes, 6 intros), `seed_resumes.py` idempotent, `.gitignore resumes/*.pdf`, openapi + admin/frontend types regenerated
2. **Contact audience filtering + hide Show everything (D2):** `ContactResumes.tsx` client filtering by `useCategory`, `IntroOverlay` 5 tiles, `HUD` button removed, `default` retained for crawler SSR only
3. **Timeline detail Option 2:** fixed public-filter leak, new `GET /timeline/{id}/projects`, RSC `app/timeline/[id]/page.tsx` with markdown + projects grid + JSON-LD, list title linked, sitemap extended
4. **pgBouncer (Point 1):** `pgbouncer` sidecar `6432` (transaction, 100/20/5), `config.py` `database_pool_size/max_overflow/pgbouncer_enabled`, `database.py` tuned `QueuePool` + `pool_pre_ping`, docs in `LOCAL.md:1a` + `conventions.md: connection pooling`

## Verification tally
- `uv run --project backend ruff check backend/app` → All checks passed
- `uv run --project backend pytest .../timeline .../projects .../resumes` → 42 passed; seed helpers 9 passed; timeline+projects detail 27 passed; pgbouncer config 8 passed (sub-agent logs)
- `npm run build --prefix frontend` → 20 pages, `○ /contact` static, `ƒ /timeline/[id]`, `○ /sitemap.xml`
- `npm run build --prefix admin` → 1993 modules, gzip 143 KB
- `alembic heads` → `869fc8d8c856 (head)` single head; `docker compose config` valid; `seed_resumes.py --dry-run` → 6 PDFs hashed, idempotent
- `grep -R Show\ everything frontend` → 0 hits; `grep -R cookies() frontend/app/timeline/[id]` → 0 hits

## Files changed (36 vs HEAD)
Tracked + untracked: `.gitignore, alembic/869fc8d8c856, app/core, app/features/*, openapi.json, docker-compose.yml, LOCAL.md, docs/conventions.md, frontend/app/contact, frontend/app/timeline/[id], frontend/app/sitemap.ts, frontend/components/*, frontend/config/tileArrangement.ts, frontend/lib/jsonld.ts, frontend/src/api.d.ts, admin/src/api.d.ts, backend/scripts/*, docs/specs/*, resumes/.gitkeep` — see `git diff --stat HEAD` + `git status`.

## How to use (local → admin edits → production)
> User: "Add the experience. I will edit all the experiences or timeline points later if some changes are needed. I need the data inside the portals to see what all things are working."
- Local DB already seeded: visit `http://localhost:3000/timeline`, `/timeline/{id}`, `/projects`, `/contact` (filtered demo), admin `http://localhost:5200/timeline` and `…/resumes` (6 variants). Edit timeline highlights/projects/skills in admin — changes revalidate Next tags and surface within seconds.
- Production (after you set 5 secrets + Railway link):
  ```bash
  railway run --service backend -- uv run python backend/scripts/seed_resumes.py --canon backend/scripts/resume_canon.json --dry-run
  railway run --service backend -- uv run python backend/scripts/seed_resumes.py --canon backend/scripts/resume_canon.json
  # verify: curl /api/v1/resumes | jq; curl /api/v1/timeline | jq; bash scripts/check_ssr.sh --all https://frontend-production-38ac.up.railway.app
  ```
  Media at `https://admin.siddhesh-chaudhari.com/media/resumes/*` via Volume `/data` + `MEDIA_BASE_URL`.

## Infra still pending (per HANDOFF-RAILWAY-INFRA-PLAN.md:33, not reordered)
TD-M3 Resend DNS, TD-M4 secrets (5 values), TD-M5 auto-deploy off + `RAILWAY_TOKEN` prod env secret, TD-M6 admin custom domain `admin.siddhesh-chaudhari.com` + `CF_ACCESS_ENABLED=false`, TD-36 GlitchTip + restore drill + `NEXT_PUBLIC_INDEXABLE` flip, Umami hosting decision. Secrets pause blocks nothing for local admin review but blocks production login/email.

## Open questions now asked (reply inline)
- Timeline detail: UUID vs slug, list→detail vs expand, umbrella detail visibility — see `docs/specs/timeline-detail/POST-DEVELOPMENT.md: Open items 1–6` and `docs/specs/timeline-detail/PLAN.md:3`
- Contact reset: with `Show everything` hidden, category persists until cookie expiry/manual clear — confirm desired or propose hidden reset route.

## Post-development docs per your rule
- `docs/specs/resume-consolidation/POST-DEVELOPMENT.md:1`, `docs/specs/timeline-detail/POST-DEVELOPMENT.md:1`, this recap `docs/handoff/POST-DEVELOPMENT-RECAP-2026-08-30.md:1`, `docs/specs/resume-consolidation/PLAN.md:1` + `backend/scripts/resume_canon.json:1` as canon review artifact.
