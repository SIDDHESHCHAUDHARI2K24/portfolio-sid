# TD-M3: Resend Domain Verification — SPF/DKIM/DMARC

**Phase:** P0 · **Wave:** 2 · **Executor:** user (agent verifies after) · **Effort:** S (1 hr)
**Source:** development-plan-P0.md → P0.T1.S6
**Depends on:** TD-M1 · **Blocks:** TD-17 (admin OTP email)

## Purpose
Both email use cases (admin OTP, form notifications) target the owner's own
inbox; an OTP email landing in spam is a self-inflicted lockout from the
admin portal. Verification is DNS work in the active Cloudflare zone.

## Paths
- Modify: Cloudflare zone DNS records; `development_plan/handoff/env-vars-registry.md` (RESEND_API_KEY reference)

## Steps (user)
1. Create the Resend account; add domain `siddhesh-chaudhari.com` for verification
2. Publish the exact SPF and DKIM records Resend issues as **DNS-only (grey cloud)** records in the Cloudflare zone
3. Add a DMARC record at `_dmarc` with `p=none` — it costs nothing and gives visibility
4. Wait for the Resend dashboard to show the domain verified
5. Generate a sending API key; record `RESEND_API_KEY → Railway backend env` in env-vars-registry.md; the actual value goes only into Railway (TD-M4)
6. Send a test email; confirm it arrives in the inbox, NOT spam

## Steps (agent, after user confirms)
7. Run the Verify commands

## Tests
- dig shows SPF includes resend, the DKIM selector record is present, DMARC is present
- Test email lands in the inbox (user attests)

## Acceptance Criteria
- [ ] Resend dashboard shows the domain verified
- [ ] SPF, DKIM, and DMARC records present in the zone (DNS-only, grey cloud)
- [ ] Test email arrives in inbox, not spam
- [ ] RESEND_API_KEY referenced in the registry, value in Railway only

## Verify (agent runs after user completes steps)
`dig +short TXT siddhesh-chaudhari.com && dig +short TXT resend._domainkey.siddhesh-chaudhari.com && dig +short TXT _dmarc.siddhesh-chaudhari.com && grep -c RESEND_API_KEY development_plan/handoff/env-vars-registry.md`

## Commit
`docs: record Resend verification — SPF/DKIM/DMARC present, key in registry`

## Invariants
- Mail records are DNS-only (grey cloud) — never proxied through the orange cloud
- Free tier (3,000/month, 100/day) far exceeds this project's needs; no paid upgrade
- RESEND_API_KEY never enters git; the registry holds references only
