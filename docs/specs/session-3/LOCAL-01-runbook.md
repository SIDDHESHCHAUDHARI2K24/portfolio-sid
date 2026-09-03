# LOCAL-01: Local Dev Runbook + Smoke Test

**Phase:** Session 3 (pre-launch prep) · **Executor:** agent · **Effort:** M
**Depends on:** TD-06 (compose), TD-09 (backend image), TD-12/14 (CI parity)
**Blocks:** user local manual testing (M1–M10)

## Purpose

Give the user a single, copy-paste path to boot the **entire** stack on a
Mac with **no R2 / Resend / Turnstile secrets**, then a scripted smoke test that
proves every public route is crawler-readable and the admin login page renders.
Mirrors `.github/workflows/e2e.yml` env so "it works in CI" and "it works on my
laptop" are the same run.

Storage uses `STORAGE_KIND=local` (disk) and the Cloudflare **always-passes**
Turnstile testing key `1x00000000000000000000AA`, exactly like the e2e
workflow. The admin OTP journey is covered by a dev-only endpoint
(`GET /api/v1/auth/dev/otp`, `ENVIRONMENT=development` only) — see A4 / TD-36.S5.

## Paths

- Create: `docs/specs/session-3/LOCAL-01-runbook.md` (this card)
- Create: `LOCAL.md` (the runbook the user actually follows)
- Reference: `scripts/check_ssr.sh`, `docker-compose.yml`, `backend/.env.example`,
  `frontend/.env.example`

## Steps

1. `docker compose up -d` — Postgres 16 + MinIO + bucket init (TD-06).
2. `backend/.env` (gitignored) with `STORAGE_KIND=local`, mock Turnstile key,
   generated `ADMIN_PASSWORD_HASH`. See `LOCAL.md`.
3. `uv run alembic upgrade head` then `uv run python scripts/seed_e2e.py`.
4. Backend: `uv run uvicorn app.app:create_app --factory --port 8000`.
5. Frontend: `npm run dev` (→ :3000). Admin: `npm run dev` (→ :5200).
6. Smoke: `bash scripts/check_ssr.sh --all http://localhost:3000` (13/13),
   `bash scripts/check_ssr.sh --seo http://localhost:3000` (6/6),
   `curl -sf http://localhost:8000/api/v1/health`, and confirm
   `http://localhost:5200/login` renders ("Admin Login").

## Tests / Acceptance

- [x] `docker compose up -d` brings Postgres + MinIO healthy
- [x] backend boots with `STORAGE_KIND=local` + mock Turnstile, `/health` 200
- [x] frontend :3000 + admin :5200 boot with no secrets
- [x] `check_ssr.sh --all` 13/13, `--seo` 6/6
- [x] admin login page renders

## Verify

```
docker compose up -d
cd backend && uv run alembic upgrade head && uv run python scripts/seed_e2e.py
uv run uvicorn app.app:create_app --factory --port 8000 &   # :8000
cd frontend && npm run dev &                                # :3000
cd admin && npm run dev &                                   # :5200
bash scripts/check_ssr.sh --all http://localhost:3000 && echo SSR_OK
bash scripts/check_ssr.sh --seo http://localhost:3000 && echo SEO_OK
curl -sf http://localhost:8000/api/v1/health && echo BACKEND_OK
curl -sf http://localhost:5200/login && echo ADMIN_OK
```

## Commit

`docs(local): LOCAL-01 runbook + smoke-test verification (no secrets)`

## Invariants

- Never commit `.env`; the runbook only references gitignored local files.
- `STORAGE_KIND=local` is dev-only — production stays `s3` (R2).
- `CORS_ALLOW_ORIGINS` stays empty in prod; the runbook's dev value
  (`http://localhost:5200`) is a deliberate local divergence, never committed.
- SSR still wins: the homepage serves the full overview in HTML regardless of
  the intro overlay (conventions invariant #1) — `check_ssr.sh` is the proof.
