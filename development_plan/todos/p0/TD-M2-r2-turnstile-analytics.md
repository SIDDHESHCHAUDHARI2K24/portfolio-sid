# TD-M2: R2 Bucket + Turnstile Widget + Web Analytics

**Phase:** P0 · **Wave:** 1 · **Executor:** user (agent verifies after) · **Effort:** S (1 hr)
**Source:** development-plan-P0.md → P0.T1.S3, P0.T1.S4, P0.T1.S5
**Depends on:** TD-M1 (custom domain step) · **Blocks:** TD-08 (R2 parity), TD-M4 (env wiring)

## Purpose
Production object storage, bot mitigation, and crawler-visibility analytics.
All three are account-level features independent of the zone; only the R2
custom domain needs the active zone.

## Paths
- Modify: `development_plan/handoff/env-vars-registry.md` (references only — never values)
- Reference: Railway backend/frontend env vars (wired in TD-M4)

## Steps (user)
1. R2: create bucket `portfolio-media`
2. R2: create an API token scoped **Object Read & Write to that bucket only** — never an account-wide token; note the S3 endpoint `https://<account-id>.r2.cloudflarestorage.com`
3. R2: attach custom domain `media.siddhesh-chaudhari.com` (zone Active per TD-M1) — `r2.dev` URLs are explicitly not for production traffic
4. Turnstile: create a widget in **Managed mode**; allowed hostnames: `siddhesh-chaudhari.com`, `*.up.railway.app`, `localhost`
5. Web Analytics: enable for the site and obtain the beacon token; verify at setup whether the beacon requires the proxied zone (injection into app/layout.tsx lands with TD-33)
6. Record every credential in `handoff/env-vars-registry.md` as references only (e.g. `R2_ACCESS_KEY_ID → Railway backend env`): R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_ENDPOINT_URL, R2_BUCKET, TURNSTILE_SITE_KEY (public, frontend), TURNSTILE_SECRET_KEY, CF_WEB_ANALYTICS_TOKEN
7. Actual values go ONLY into Railway env vars (TD-M4) — never git, never the registry file

## Steps (agent, after user confirms)
8. Run the Verify commands; confirm registry entries exist without values

## Tests
- A test object uploads and downloads via the S3 API with the endpoint URL (`aws s3 --endpoint-url` or equivalent)
- `media.siddhesh-chaudhari.com` serves the test object
- No literal key appears anywhere in the repo

## Acceptance Criteria
- [ ] Bucket exists; a test object round-trips via the S3 API
- [ ] API token is bucket-scoped; custom domain media.siddhesh-chaudhari.com attached
- [ ] Turnstile widget in Managed mode with all three hostnames registered
- [ ] Beacon token obtained; all credentials referenced in env-vars-registry.md, values in Railway only

## Verify (agent runs after user completes steps)
`dig +short media.siddhesh-chaudhari.com && grep -c "R2_" development_plan/handoff/env-vars-registry.md && grep -c "TURNSTILE_" development_plan/handoff/env-vars-registry.md`

## Commit
`docs: env-vars registry entries for R2/Turnstile/Analytics (references only)`

## Invariants
- Bucket-scoped tokens only; account-wide R2 tokens prohibited
- r2.dev public URLs are never the production media path
- Hostname mismatch is the classic silent Turnstile failure — register all three hostnames
