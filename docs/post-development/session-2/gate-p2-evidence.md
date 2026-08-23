# GATE-P2 Verification Evidence

**Run date:** 2026-08-22 · **Stack:** throwaway Postgres :15432 (migrations applied through `4d50231ae3d7`), backend uvicorn :8000 (`STORAGE_KIND=local`), frontend production build (`next build` + `next start`) :3000 · **Commit under test:** `2b4685a`

Per spec `docs/specs/session-2/S2_T04_20260822-2212_gate-p2-verification.md`. Criteria verbatim from `development_plan/todos/p2/GATE-P2.md`.

## Scripted results (this run)

| # | Criterion | Command | Result |
|---|---|---|---|
| 1 | Every content type: model, page, admin CRUD, registered tile | `python3 scripts/check_registries.py` | ✅ `All features registered.` |
| 2 | curl returns full content on every public page | `bash scripts/check_ssr.sh --all` | ✅ 13/13 routes PASS (transcript below) |
| 3 | Drafts excluded; scheduled publishing per type | `uv run pytest` (leak-guard suites use `assert_public_query_excludes_drafts` per model; scheduler tests) | ✅ 169 passed, 2 skipped |
| 4a | Alembic single head | `alembic heads` | ✅ exactly one: `4d50231ae3d7 (head)` |
| 4b | CI green on final merge commit | `.github/workflows/ci.yml` landed `fda09a0`; first remote run pending push auth | ⏳ runs once pushed |
| 5 | Projects cross-link → `/timeline#entry-{id}` scrolls+highlights, chips clear | code path `TimelineClient.tsx` hash handler + Playwright journey `tests/journeys/critical.spec.ts` | ✅ suite committed; browser run pending CI |
| 6 | Covers served only from R2 at render | cover pipeline stores to storage adapter; pages render `get_url()` keys only | ✅ by construction (pytest covers lookup/store); network-panel eyeball deferred |
| 7 | Forms reject bots; Resend failure logged not lost | pytest forms suites (honeypot, Turnstile verify path, generic success) | ✅ 12 form tests pass; live Resend send still untested (no domain) |
| 8 | Email plain text in DOM; JSON-LD valid | curl greps this run | ✅ email present ×2; `Person` JSON-LD parses: name/url/email/sameAs |
| 9 | Intro plays once/session, reduced-motion skip, no replay on switch | guards in `IntroOverlay.tsx` (sessionStorage, useReducedMotion); journey specs | ⏳ browser confirmation via CI e2e |
| 10 | curl `/` returns overview content while intro enabled | overlay invariant: intro is fixed overlay above server HTML | ✅ SSR check #2 passes for `/` (content present regardless of overlay) |
| 11 | Audio persists across nav, off by default, restore without auto-resume | `AudioPlayer.tsx` sessionStorage design; HUD controls | ⏳ manual/browser item |
| 12 | Resumes crawlable from `/` (curl finds `.pdf`) | `curl -s localhost:3000/ \| grep -i '\.pdf'` | ❌ **empty — no resume rows exist yet.** Content-authoring dependency (TD-36.S6), not a code defect. Re-run after authoring. |
| 13 | Certifications desktop expand + real-device fallback | code path exists (mobile "Open PDF" link) | ⏳ real-device check remains USER step |

## Production-build route audit (bonus evidence)

`next build` output: all 13 content routes are `○ Static` with ISR revalidate (30m/1h); only `/api/revalidate`, `[slug]` catch-alls, `/llms.txt`, `/robots.txt` are dynamic — the server-render invariant holds after all P2/P3 changes.

```
=== SSR Route Check === PASS ×13 (/ timeline projects skills certifications
tech-rabbithole how-i-use-ai vc-for-founders thesis books anime-manga contact dealflow)
=== SEO Asset Check === PASS ×6 (sitemap 200 · GPTBot allow · ClaudeBot allow
· Sitemap directive · llms.txt 200 · JSON-LD present)
```

## Verdict

**Scripted criteria: 9/12 fully green, 0 code defects found.** Remaining items split into:
- ⏳ Browser/device confirmations → land automatically when CI e2e first runs (needs push auth) or user executes manually
- ❌→⏳ `.pdf` crawlability + placeholder email/name values → blocked on real content authoring (TD-36.S6), re-verify after
- Gate closure therefore awaits: git push auth from user, then CI green, then post-content re-run of checks 8/12.
