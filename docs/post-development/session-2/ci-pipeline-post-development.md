# S2_T05 / S2_T06 — CI Pipeline Post-Development

**Specs:** `docs/specs/session-2/S2_T05_20260822-2212_ci-quality-contract.md`, `S2_T06_20260822-2212_ci-e2e-deploy.md`
**Commits:** `fda09a0` (quality+contract), `2b4685a` (e2e+deploy)

## What was built

| File | Contents |
|---|---|
| `.github/workflows/ci.yml` | 4 jobs: backend (ruff→mypy→pytest→single-head vs postgres:16 service), frontend (tsc→eslint `--max-warnings=5`→vitest), admin (tsc→oxlint), contract (OpenAPI regen + `git diff --exit-code` + `check_registries.py`) |
| `.github/workflows/e2e.yml` | Full-stack job: postgres service → uv sync → `alembic upgrade head` → uvicorn :8000 readiness-gated by curl loop → `next build` → chromium via playwright → journeys+a11y suites; traces uploaded on failure |
| `.github/workflows/deploy.yml` | `production` environment-gated Railway deploy with dry-run dispatch default until TD-M4/M5 complete |
| `frontend/vitest.config.mts` | include/exclude split so Playwright specs under `tests/` are never swallowed by vitest's default glob |
| `frontend/config/tileArrangement.test.ts` | TD-31 card contract tests: per-audience ordering, contact-first, default completeness, personal exclusions |

## Deviations from cards (decisions recorded)

1. **Visual pixel suites excluded from CI e2e for now.** Baselines are darwin-captured and pre-content (original session 4 noted they captured the intro overlay, not pages). Running them on linux runners would fail spuriously. They remain a local gate; linux baseline regeneration is scheduled after content authoring (TD-36.S6).
2. **Warning budgets pinned to today's verified counts** (`--max-warnings=5` frontend) rather than zero, so gates start green and tighten later instead of starting red and being ignored.
3. **Deploy workflow ships before infra exists**, gated behind manual dispatch dry-run + the `production` environment approval — flipping it live later needs zero code changes.
4. **E2E uses `STORAGE_KIND=local`** to avoid a MinIO service dependency; boto3/MinIO parity is already covered by unit tests.

## Verification evidence

- Every gate command executed locally against the committed tree during S2_T01/T04: ruff clean · mypy clean (159 files) · pytest 169 passed + 2 skipped · alembic single head · tsc ×2 clean · eslint 0 errors / exactly 5 budgeted warnings · oxlint warnings-only · vitest 14/14 · OpenAPI regen produces no diff · registries OK.
- Production build proven locally (`next build` against live backend): all 13 content routes static with ISR; SSR suite 13/13 + SEO assets 6/6 green via `scripts/check_ssr.sh`.
- YAML validated for all three workflows.
- ⏳ **First remote CI/E2E runs blocked on push auth**: current keychain credential (`feenix-sid-2k26`) gets HTTP 403 on `SIDDHESHCHAUDHARI2K24/portfolio-sid`. User must add that account as collaborator, switch origin to SSH, or supply a fine-grained PAT. Break-test (deliberate red PR) scheduled immediately after first successful push.

## Remaining
- Tighten lint warning budgets to 0 after the TD-35 next/image conversions.
- Add linux visual baselines + enable visual suite in e2e.yml after content authoring.
- Set `RAILWAY_TOKEN` secret on the `production` environment (user).
