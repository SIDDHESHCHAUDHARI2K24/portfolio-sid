# E01-W6 — Verified Resend sender domain (optional)

**Epic:** E01 Auth · **Ticket:** E01-W6 · **Status:** Optional, user-run · **Depends on:** none

## Purpose
`RESEND_FROM=onboarding@resend.dev` is Resend's test sender and only delivers to the Resend account owner. OTP works because `ADMIN_EMAIL` is that owner. Contact and dealflow notifications to any other address, or a change of admin address, will be rejected.

## Goal
Send from a verified address on `siddhesh-chaudhari.com`, so delivery does not depend on the recipient.

## Reference files
- `backend/app/core/config.py` (`resend_from` default `portfolio@siddhesh-chaudhari.com`)
- `docs/handoff/env-vars-registry.md` (Resend DNS notes)
- `backend/app/features/forms/service.py` (notification sends)

## Functionality (user steps, no code)
1. In the Resend dashboard, add the domain `siddhesh-chaudhari.com`.
2. In Cloudflare DNS, add the SPF, DKIM, and DMARC records Resend shows (DNS only, not proxied).
3. Wait for Resend to show the domain as Verified.
4. On Railway, set the backend's `RESEND_FROM` to `portfolio@siddhesh-chaudhari.com`. This triggers a redeploy.
5. Update the env registry with the domain status.

## Edge cases
- An existing SPF record on the root domain → merge `include:` into it; two SPF records invalidate both.
- Cloudflare proxying (orange cloud) on these records breaks verification.
- Changing `RESEND_FROM` before verification → every send fails with 502 (W4 logs the reason).
- DMARC `p=reject` too early can drop mail; start with `p=none`.

## Testing and acceptance criteria
- [ ] Resend shows the domain as Verified.
- [ ] A production OTP arrives from the new sender, not in spam.
- [ ] A contact form notification arrives.

## Rollback
Set `RESEND_FROM` back to `onboarding@resend.dev`. The DNS records can stay.
