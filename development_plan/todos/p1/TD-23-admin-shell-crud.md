# TD-23: Admin Shell & Timeline CRUD — Login, Guard, CRUD Screens, Tag-Map Matrix

**Phase:** P1 · **Wave:** 6 · **Executor:** agent · **Effort:** L (2–3 days)
**Source:** development-plan-P1.md → P1.T8 (S1–S4)
**Depends on:** TD-17, TD-20 · **Blocks:** GATE-P1

## Purpose
The admin half of the spine: two-step login, session guard, the Timeline
CRUD screens Phase 2 copies nine times, and the audience-tag matrix. The
shared field components are extracted now — skipping the extraction means
nine copies of a status selector that then need nine edits.

## Paths
- Create: `admin/src/routes/login.tsx`, `admin/src/routes/login-verify.tsx`, `admin/src/components/fields/` (`TagSelect.tsx`, `AudienceOverrideSelect.tsx`, `PublishStatusField.tsx`, `MarkdownField.tsx`), timeline list/create/edit routes, tag-map matrix route, auth guard + query client setup
- Modify: `admin/src/main.tsx` (router + providers)

## Steps
1. Login flow (React Router): `/login` password step posts and, on success, advances to `/login/verify` OTP entry; show remaining attempts and expiry countdown — an OTP screen with no feedback is where people get locked out of their own portal; expired OTP → specific message with a resend option; 429 → clear "too many attempts, wait N minutes", not a generic error
2. Auth guard: route wrapper checks the session via `GET /api/v1/admin/me`, redirecting to `/login` on 401; TanStack Query with a global 401 handler so any expired-session response redirects cleanly rather than surfacing an error toast per request; sidebar navigation, content area, toast notifications. Client-side guards are UX, not security — the API remains the real boundary
3. Timeline CRUD: list with status badges and kind filter; form with all fields, tag multi-select, audience override checkboxes, status selector revealing a `publish_at` picker when Scheduled is chosen, markdown editor with preview; optimistic updates via TanStack Query mutations; validation errors surfaced inline
4. Extract the reusable pieces into `admin/src/components/fields/` — `TagSelect`, `AudienceOverrideSelect`, `PublishStatusField`, `MarkdownField` — before the second feature copies them, not after the third copy
5. Audience-tag matrix: checkbox grid — audiences as columns, topic tags as rows; batch save in one request rather than per-cell; tag management (create, rename, delete) on the same screen, with delete blocked when a tag is in use rather than cascading silently — a cascading delete would unhighlight content across the whole site with no record of what changed; saving invalidates the cached `/api/v1/relevance/map` response

## Tests
- Correct password then correct OTP grants access; expired OTP shows a specific message with resend; rate limiting surfaces a clear wait time
- Direct navigation to any admin route without a session redirects to login; session expiry mid-session redirects cleanly
- Full CRUD with validation errors inline; scheduled entries accept a future `publish_at`
- Matrix loads the current mapping and saves changes in one request; deleting an in-use tag is blocked with a clear message
- Component tests (Vitest + RTL) for the four shared field components in isolation

## Acceptance Criteria
- [ ] Login flow shows attempts remaining, expiry countdown, and a clear 429 wait
- [ ] No admin route renders without a valid session
- [ ] Full CRUD works; saving triggers revalidation and the public page updates within seconds
- [ ] Shared field components live in `admin/src/components/fields/` and are used by the timeline form
- [ ] Matrix batch save invalidates the cached map endpoint; in-use tag delete blocked

## Verify
`npm run build && npm run test` in `admin/` · manual: edit a timeline entry → public `/timeline` reflects it within seconds

## Commit
`feat(admin): login flow, auth guard, timeline crud, shared fields, tag-map matrix`

## Notes
- The timeline form is the reference implementation: Phase 2 CRUD screens copy its structure and consume the shared fields unchanged
- Optimistic updates must roll back cleanly on mutation error — a failed save that leaves stale UI is worse than a spinner

## Invariants
- Shared field components are the template — Phase 2 features extend them, never fork them
- Deleting an in-use tag is blocked, never cascading
- Client guards are UX; every admin endpoint is independently protected by `require_admin`
