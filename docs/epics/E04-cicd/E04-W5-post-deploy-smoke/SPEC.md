# E04-W5: Automatic post-deploy smoke check

**Epic:** E04 CI/CD hardening · **Ticket:** E04-W5 · **Depends on:** none (trigger depends on the W4 choice)

## Purpose

Nothing checks production after a native deploy. The E03 frontend failure was found by hand.

## Goal

Every production deploy is followed by an automatic, read-only check of backend health and the key public pages, reported as a GitHub run.

## Reference files

- `.github/workflows/deploy.yml` (`health` job)
- `frontend/app/` routes; `backend/app/features/health/`
- `docs/DEPLOYMENT.md`

## Functionality

- New `scripts/smoke.sh <site-url> <admin-url>`: GET requests only, each with `curl --retry 8 --retry-delay 10 --retry-all-errors`.
  - `<admin-url>/api/v1/health` returns 200.
  - `<site-url>/`, `/books`, `/anime-manga`, `/how-i-use-ai` and `/sitemap.xml` return 200.
  - `<site-url>/writing/does-not-exist` returns 404 (proves the app, not an error page, answered).
  - Prints one line per check; exits non-zero on the first failure.
- New `.github/workflows/smoke.yml`:
  - Triggers: `deployment_status` (state `success`, environment `production`) and `workflow_dispatch`. With W4 Option B it is called from `deploy.yml` instead.
  - Concurrency group `smoke` with `cancel-in-progress: true`, so one run covers a burst of service deploys.
  - Waits 60 s before the first check so the last service can finish rolling.
  - No secrets needed; URLs are the public domains.
- `deploy.yml` `health` job calls the same script.

## Edge cases

- Confirm first that Railway posts GitHub deployment statuses for this repo (Deployments tab). If not, fallback trigger: `workflow_run` after CI on `main`, then poll the site until the served build changes or 15 minutes pass. Stop and ask before building the fallback.
- A deploy of `cron` alone triggers a run; the checks still pass, which is harmless.
- Cloudflare proxying (E03-W6 Part B) does not change the checks.

## Testing

- Run `scripts/smoke.sh https://siddhesh-chaudhari.com https://admin.siddhesh-chaudhari.com` locally: all pass.
- Run it against the local stack (`http://localhost:24730`, `http://localhost:24752`): all pass with seeded data.
- Point it at a wrong host: it fails with a clear line.
- After merge: the next deploy produces a green smoke run.

## Acceptance criteria

- [x] `scripts/smoke.sh` passes against production and the local stack, and fails on a bad host.
- [ ] `smoke.yml` runs automatically after a production deploy and reports pass or fail.
- [x] `deploy.yml` uses the script.
- [x] `docs/DEPLOYMENT.md` documents the smoke check and how to run it by hand.

## Rollback

Delete `smoke.yml`; restore the inline health step in `deploy.yml`.
