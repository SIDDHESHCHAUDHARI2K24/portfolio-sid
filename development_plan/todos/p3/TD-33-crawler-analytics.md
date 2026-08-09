# TD-33: Crawler Analytics — Beacon, CrawlerHit, Admin Panel

**Phase:** P3 · **Wave:** 8 · **Executor:** agent · **Effort:** M (1 day)
**Source:** development-plan-P3.md → P3.T3 (S1–S3)
**Depends on:** TD-32 · **Blocks:** TD-36

## Purpose
See *which* AI crawler read *what* — the measurement layer for the goal the
whole site exists for. Cloudflare Web Analytics for traffic and verified-bot
reporting, an origin-level `CrawlerHit` log for agent-level visibility, and
an admin panel that states its own limitations in the UI. Sits after TD-32
deliberately: measuring crawlers only makes sense once robots.txt explicitly
lets them in.

## Paths
- Modify: `frontend/app/layout.tsx` (beacon script), FastAPI app factory (middleware)
- Create: `CrawlerHit` model + Alembic migration, retention job in the cron service (TD-19), admin analytics panel
- Config: Web Analytics beacon token from TD-M2 (Railway env var)

## Steps
1. **P3.T3.S1 — Web Analytics beacon.** Add the script tag to the root layout using the TD-M2 token. Privacy-preserving, no cookies, no consent banner required — which is exactly why it was chosen over alternatives that would have forced one.
2. **P3.T3.S2 — origin hit logging.** FastAPI middleware records `user_agent`, `path`, `ip_hash`, `timestamp` into a `CrawlerHit` table. **Hash the IP** — there is no reason to store raw visitor IPs and every reason not to. Classify against known agents: GPTBot, ClaudeBot, PerplexityBot, CCBot, Google-Extended, Bytespider. Write asynchronously so logging never blocks a response. Index on (agent, timestamp) so panel queries stay cheap. Add a retention job pruning rows beyond 90 days.
3. **P3.T3.S3 — admin panel.** Table of recent hits filterable by agent, plus a count-by-agent-per-week summary. State the undercount caveat **in the UI**, not only in documentation — otherwise the numbers will eventually be misread as traffic.

## Tests
- pytest: middleware stores `ip_hash`, never the raw IP
- pytest: known agents classified correctly; unknown agents stored unclassified
- pytest: response timing unaffected — write is async, a slow DB write never delays the response
- pytest: retention job deletes rows older than 90 days, keeps newer ones
- pytest: count-by-agent-per-week aggregation returns expected buckets
- Vitest/RTL: panel filters by agent; the undercount caveat text renders
- Frontend test: beacon script present exactly once in the root layout, not duplicated per route

## Acceptance Criteria
- [ ] Pageviews and bot traffic appear in the Cloudflare dashboard
- [ ] Hits recorded with hashed IPs; known agents classified; logging never blocks a response
- [ ] Panel lists hits, filters by agent, and displays the undercount caveat

## Verify
`uv run pytest backend/tests/test_crawler_hits.py && npm run test --workspace admin` — then hit a deployed API route with a spoofed `GPTBot` user-agent and confirm the classified row appears in the admin panel.

## Commit
`feat(analytics): web analytics beacon, CrawlerHit origin logging, admin crawler panel`

## Invariants
- **Undercounts by design** (gap G9): edge-cached responses never reach the origin, and static pages are exactly what crawlers fetch most. Read it as "which crawlers have visited", never "how many times" — the ratio is not meaningful. The caveat lives in the admin UI, not just in docs.
- Raw visitor IPs are never persisted — hash only
- Logging never blocks a response path
- 90-day retention is enforced by job, not by convention
- Observe, never gate: middleware must not block or challenge AI crawlers — that is robots.txt's job, and the allow-list is fixed
