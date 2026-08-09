# GATE-P2 — Phase 2 Exit Gate

**Phase:** P2 · **Wave:** 7 · **Executor:** agent + user · **After:** TD-24..TD-30 all merged
**Source:** development-plan-P2.md → Exit Checklist (verbatim)

## Exit Checklist

- [ ] Every content type has model, page, admin CRUD and registered tile
  - Verify: `uv run scripts/check_registries.py`; tile registry holds entries for projects, skills, certifications, three post collections, thesis, books, anime & manhwa, hobbies, investor intro, contact, dealflow
- [ ] `curl` returns full content on every public page
  - Verify: `bash scripts/check_ssr.sh` over /projects, /projects/[slug], /skills, /certifications, all three collection pages, /thesis, /books, anime & manhwa page, prose pages, /contact, /dealflow
- [ ] Drafts excluded and scheduled publishing verified on every type
  - Verify: seed one draft + one scheduled entry per type; `curl` excludes the draft; scheduler cron flips the scheduled entry to published
- [ ] Projects cross-link navigates to the correct timeline entry
  - Verify: click cross-link → `/timeline#entry-{id}` scrolls to and highlights the entry; filter chips cleared on anchor nav
- [ ] Certifications expand works on desktop and falls back on real mobile
  - Verify: desktop expand shows PDF/image inline; real device (user's phone, paired step) shows a working open/download fallback
- [ ] Covers served only from R2; no third-party image requests at render
  - Verify: network panel on /books and the anime & manhwa page shows zero requests to covers.openlibrary.org, Jikan, or MAL hosts
- [ ] Both forms reject bots and notify via Resend; failures logged not lost
  - Verify: honeypot and expired-Turnstile submissions discarded with the identical generic success response; inject a Resend failure → submission persists, error logged, unread visible in admin
- [ ] Email plain text in DOM and JSON-LD; resumes crawlable from `/`
  - Verify: `curl -s localhost:3000/contact | grep '<email address>'`; `curl -s localhost:3000/ | grep -i '\.pdf'`
- [ ] Intro plays once per session, respects reduced motion, never replays on switch
  - Verify: sessionStorage flag set after first play; OS reduced-motion setting skips entirely; category switch never replays
- [ ] `curl` on `/` returns overview content with the intro enabled
  - Verify: `curl -s localhost:3000/` contains the full overview markup while the intro is enabled in the browser
- [ ] Audio persists across navigation, off by default, no auto-resume
  - Verify: start audio → client-side navigation → uninterrupted; hard reload → track and volume restored, paused; first visit silent
- [ ] `alembic heads` returns one head; CI green
  - Verify: `(cd backend && uv run alembic heads)` → exactly one head after all tracks merged; GitHub Actions green on the final merge commit

## Sign-off
- All tracks (TD-25..TD-30) merged via the TD-24 queue: Track A first, one merge at a time, remaining branches rebased + regenerated after each merge
- Real-device PDF fallback (TD-26) verified on the user's phone before the gate closes
- `alembic heads` == 1 on the post-merge main; any `alembic merge heads` escape hatch used is recorded in the handoff doc
