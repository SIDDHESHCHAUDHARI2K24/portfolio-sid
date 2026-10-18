# E04-W2: Frontend build retries the API through a backend restart

**Epic:** E04 CI/CD hardening · **Ticket:** E04-W2 · **Depends on:** none

## Purpose

On 2026-10-18 the frontend build failed because prerendering `/` got a 502 while the backend was restarting (it runs migrations at start). `apiFetch` makes one private attempt, one public-proxy attempt, and no retry.

## Goal

During `next build`, transient API failures are retried long enough to cover a backend restart. A real outage still fails the build, with a clear log line.

## Reference files

- `frontend/lib/api.ts` (`apiFetch`, `getFallbackServerBase`, `isPrivateNetworkError`)
- `frontend/app/writing/[slug]/page.tsx` (`generateStaticParams` already tolerates failure)
- `Dockerfile:13` (backend start: `alembic upgrade head` then uvicorn)

## Functionality

- Detect build time with `process.env.NEXT_PHASE === "phase-production-build"`.
- At build time only, retry a fetch on network errors and on HTTP 502, 503 and 504. Backoff: 2 s, 4 s, 8 s, 16 s, 30 s, 30 s (about 90 s total). Each retry logs `[apiFetch] build retry n/6 <path> <reason>`.
- Retries apply to whichever base is in use (the public proxy on Railway, the configured URL elsewhere).
- 4xx responses are never retried; 404 still flows to `notFound()` through `isNotFoundError`.
- Runtime (ISR revalidation, SSR) behaviour is unchanged: no added retries or latency for visitors.
- No empty-content fallback: a page that cannot get its data after the retries fails the build rather than caching an empty page for an hour.

## Edge cases

- Many pages prerender in parallel; each retries on its own. Total build time grows by at most about 90 s in the worst case.
- A 500 from the backend is a bug, not a restart; it is not retried.
- Local `npm run build` with no backend still fails, after the retries; the log says why.

## Testing

- Vitest: mock `fetch` to return 502 twice then 200; assert three calls and success at build phase; assert one call at runtime phase.
- Vitest: 404 at build phase is not retried; 500 is not retried.
- Manual: run `npm run build` against the local backend, stop the backend for 20 s during the build, restart it; the build succeeds and logs retries.

## Acceptance criteria

- [ ] Build-phase fetches retry 502/503/504 and network errors with the stated backoff.
- [ ] Runtime fetches make the same calls as before.
- [ ] Unit tests above pass; `npm run lint && npm test && npm run build` pass.
- [ ] The manual stop-and-restart build succeeds.

## Rollback

Revert the commit; `apiFetch` returns to a single attempt per base.
