# TD-29: Track E — Resume + Forms

**Phase:** P2 · **Wave:** 7 · **Executor:** agent · **Effort:** L (4–5 days)
**Source:** development-plan-P2.md → Track E: E.T1–E.T6
**Depends on:** TD-24 · **Blocks:** GATE-P2

## Purpose
The only track with outbound side effects (Resend). Resume variants mapped to audiences with
both exposed by default; one submission model and one endpoint serve both forms with the full
anti-abuse stack and consent snapshots.

## Paths
- Create: `backend/app/features/resumes/...`, `backend/app/features/forms/...` + tests
- Create: `frontend/app/contact/page.tsx`, `frontend/app/dealflow/page.tsx`, admin submissions inbox
- Modify (per TD-24 protocol): the five shared contention files

## Steps
1. **E.T1 Resume.** `variant` (TECH/BUSINESS), `label`, `file_key`, `is_active`, `updated_at`.
   Mapping: Recruiters+Techies → tech; Investors+Founders → business; the default view exposes
   BOTH, clearly labelled (assumption A13) — an AI parser should choose which fits its search
   rather than receive your guess. Link the PDFs from `/` so they are crawlable; serve from R2
   with content-hashed keys so replacing a resume changes its URL and no cache serves the old one.
2. **E.T2 FormSubmission.** `form_type` (CONTACT/DEALFLOW), `payload` (JSONB — fields differ
   per type), `consent_given`, `consent_text` — a SNAPSHOT of the wording shown, not a
   reference to current wording (rewording later must not rewrite what each person agreed to),
   `submitter_email`, `ip_address`, `user_agent`, `is_read`, `created_at`.
3. **E.T3 Endpoint.** `POST /api/v1/forms/{form_type}`. Order matters: honeypot check →
   Turnstile `/siteverify` (P1.T2.S7 helper) → rate limit → database write. Verification must
   precede any write. Return an identical generic success response whether the submission was
   accepted or silently discarded — bots learn nothing. On success send a Resend notification
   via the P1 email client; email failure must NOT fail the request — the submission is safely
   stored, log at error level, surface unread submissions in admin. Turnstile tokens expire
   after 300s and are single-use: a stale open form fails — handle re-challenge gracefully,
   never a raw error.
4. **E.T4 Pages.** Contact: email as PLAIN TEXT in the DOM (agents read the DOM; an
   JS-assembled address is invisible to them) and in the `Person` JSON-LD; LinkedIn; Cal.com
   booking link (free tier permits multiple event types; Calendly caps at one). Dealflow:
   name, email, firm, focus area, consent checkbox — consent required before submission. Both
   forms embed the Turnstile widget.
5. **E.T5 Admin inbox.** Both types listed, filterable by type and read state, newest first.
   Detail renders the JSONB payload plus the stored consent text. CSV export — collect-only
   with manual outreach means exporting is how the list gets worked.
6. **E.T6 Tiles.** Contact: all five audiences plus default, positioned directly below the
   main tile, showing email + LinkedIn inline. Dealflow: Investors only. Resume surfaces
   within the contact tile, not as its own.
7. Register the tiles per the P1 contract → run `scripts/regen_migration.sh "resume+forms"` →
   pass `scripts/check_registries.py` → rebase on latest main before opening the PR.

## Tests
- Correct resume variant surfaces per audience; both appear in the default view; PDFs reachable and crawlable from `/`
- Both form types persist; consent text stored per submission, not referenced
- Honeypot submissions return success and persist nothing
- Missing or expired Turnstile token is rejected; rate limiting returns 429
- Resend failure logs an error and still returns success
- Email is plain text in the DOM and in JSON-LD; dealflow requires consent
- Inbox filters by type/read; consent text visible; CSV exports correctly

## Acceptance Criteria
- [ ] E.T1–E.T6 acceptance criteria above all green
- [ ] Accepted and discarded submissions return identical responses
- [ ] Migration regenerated against latest main; single head
- [ ] Registry check passes

## Verify
`curl -s localhost:3000/contact && curl -s localhost:3000/ | grep -i resume && (cd backend && uv run alembic heads) && uv run scripts/check_registries.py`

## Commit
`feat(resume,forms): variants, submissions, anti-abuse endpoint, inbox, tiles`

## Invariants
- Verification (honeypot → Turnstile → rate limit) always precedes the DB write
- Email failure never fails a submission; failures logged, never lost
- `consent_text` is an immutable snapshot per submission
- Tiles registered + regen run + registry check passed before PR
