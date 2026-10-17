# E01-W3 — Explicit wrong-password feedback

**Epic:** E01 Auth · **Ticket:** E01-W3 · **Status:** Ready · **Depends on:** E01-W2 (ship together or after; an explicit password check without per-caller lockout invites brute force)

## Purpose
Login returns the same 200 for right and wrong passwords, so the admin app always opens the OTP screen. A typo looks identical to an email failure, which is what made the outage hard to diagnose.

## Goal
Correct password → code sent → OTP screen. Wrong password → error on the login page, no OTP screen, no email.

## Reference files
- `backend/app/features/auth/service.py` (`request_otp`, `GENERIC_LOGIN_DETAIL`)
- `backend/app/features/auth/tests/test_auth.py`
- `admin/src/routes/login.tsx`, `admin/src/lib/api.ts` (401 handling)
- `backend/openapi.json`, `admin/src/api.d.ts`, `frontend/src/api.d.ts` (regenerate only if a schema changes)
- `docs/features/auth.md` (the "indistinguishable" invariant)

## Functionality
| Case | Status | `detail` | Side effects |
|---|---|---|---|
| Locked out | 429 | `Too many attempts. Try again later.` | none (unchanged) |
| Wrong password | **400** | `Incorrect password.` | failure row recorded |
| Right password, email sent | 200 | `Code sent.` | success row, old challenges deleted, new challenge |
| Right password, email failed | 502 | `Code delivery failed; try again later.` | challenge deleted (unchanged) |
| Development mode | 200 | `Code sent.` | code readable via the dev endpoint (unchanged) |

- Use 400, not 401: `apiFetch` turns any 401 into a redirect to `/login` and drops the message.
- Keep the Argon2 timing decoy when no hash is configured.
- Admin: `onSuccess` navigates to `/login/verify` (now only on a real send). On error, show `ApiError.message`, stay on `/login`, and keep the typed password.
- `docs/features/auth.md`: replace the invariant with "explicit result; brute force bounded by per-IP lockout (W2) and the OTP second factor". Update the flow diagram and API table.

## Edge cases
- Empty or whitespace password: the UI blocks submit. The backend treats `""` as a wrong password (400, failure row) and a missing field as 422. The schema is unchanged, so the OpenAPI is unchanged (decision 2026-10-17).
- Wrong password while locked out → 429 (lockout check runs first).
- The 10th failure triggers lockout on the 11th attempt, not the 10th response.
- Slowapi limit (5/min) → 429 with the rate-limit detail; the UI shows it.
- A DB override row in `admin_credentials` is checked before the env hash (unchanged).
- Double-submit: the second request deletes the first challenge; only the latest code works (unchanged, documented).
- The verify page opened directly without a login → existing "Invalid or expired code" path.

## Testing
- Backend: one test per table row; `send_otp` called exactly once on success and never on a wrong password; replace the test that asserts identical responses.
- Admin: `npm run lint && npm run build`. Locally (`LOCAL.md`): a wrong password shows the error and stays on `/login`; the right password reaches `/login/verify`.
- Run the react-doctor skill on the admin change.
- Production, after deploy (user-approved): a wrong password shows the error and Resend usage does not change; the right password sends an email.

## Acceptance criteria
- [ ] The behavior matches the table, with tests green.
- [ ] The admin UI shows the error and does not navigate.
- [ ] `docs/features/auth.md` is updated.

## Rollback
Revert and redeploy the backend and admin services. No data changes.
