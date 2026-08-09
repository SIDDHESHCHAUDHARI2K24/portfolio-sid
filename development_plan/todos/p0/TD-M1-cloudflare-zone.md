# TD-M1: Verify Cloudflare Zone Active + Renewal/WHOIS Record

**Phase:** P0 · **Wave:** 0 · **Executor:** user (agent verifies after) · **Effort:** XS (15 min)
**Source:** development-plan-P0.md → P0.T1.S1, P0.T1.S2 (collapsed to verification — domain already registered via Cloudflare Domains, nameservers already delegated, verified via dig)
**Depends on:** — · **Blocks:** TD-M2 (custom domain step), TD-M3, TD-M6

## Purpose
Registration and nameserver delegation are already done; this card reduces to
confirming the zone is Active and recording the registrar facts the plan
demands, so Access/Tunnel/Resend work proceeds on a confirmed-active zone.

## Paths
- Modify: `docs/conventions.md` (Domain section: renewal price, WHOIS privacy)

## Steps (user)
1. Cloudflare dashboard → confirm zone `siddhesh-chaudhari.com` status reads "Active" (confirm in the dashboard, not by guessing from dig)
2. Confirm the domain shows under Cloudflare Domains with auto-renew enabled
3. Note the renewal price and confirm WHOIS privacy is included (Cloudflare Domains includes it by default)
4. Record both facts in `docs/conventions.md` under a "Domain" section: renewal price + WHOIS privacy status

## Steps (agent, after user confirms)
5. Run the Verify commands below; paste evidence into the session handoff

## Tests
- `dig +short NS siddhesh-chaudhari.com` returns Cloudflare nameservers (already true)
- Zone status Active in the dashboard (user attests)

## Acceptance Criteria
- [ ] Zone status reads "Active" in the Cloudflare dashboard
- [ ] `dig NS siddhesh-chaudhari.com` returns Cloudflare nameservers
- [ ] Renewal price + WHOIS privacy recorded in docs/conventions.md

## Verify (agent runs after user completes steps)
`dig +short NS siddhesh-chaudhari.com && dig +short SOA siddhesh-chaudhari.com && grep -i "renewal" docs/conventions.md`

## Commit
`docs: record domain renewal price + WHOIS privacy; zone verified active`

## Invariants
- Zone activation is confirmed in the dashboard, never inferred from dig alone
- Until Active: Resend verification (TD-M3), Tunnel/Access (TD-M6), and the R2 custom domain (TD-M2) cannot complete
