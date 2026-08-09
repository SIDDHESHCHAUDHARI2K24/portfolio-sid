# TD-M6: Cloudflare Tunnel + Access (Env-Gated, Single Hostname)

**Phase:** P0 · **Wave:** 4 · **Executor:** paired (user: Zero Trust dashboard; agent: cloudflared service + JWT verification) · **Effort:** M (half day)
**Source:** development-plan-P0.md → P0.T2.S5, P0.T2.S6
**Depends on:** TD-M1, TD-M4 · **Blocks:** TD-36 (launch turns Access on permanently)

## Purpose
The admin hostname is reachable without exposing a public inbound port, and
Access gates it behind email OTP. ONE hostname carries both the SPA and
/api/* — splitting them across subdomains redirects CORS preflights into the
login page and fails looking like a CORS misconfiguration.

## Paths
- Create/modify: cloudflared Railway service; backend `app/core/security.py` (Access JWT verification)
- Reference: Railway env vars CF_TUNNEL_TOKEN, CF_ACCESS_ENABLED, CF_ACCESS_TEAM_DOMAIN (registry entries)

## Steps
1. User: Cloudflare Zero Trust → create a NAMED tunnel (quick tunnels are ephemeral and unsuitable); copy the tunnel token; store it as Railway env var CF_TUNNEL_TOKEN
2. User: add public hostname `admin.siddhesh-chaudhari.com` on the tunnel, routed to the backend service's INTERNAL Railway address — single hostname for SPA + API
3. Agent: create the `cloudflared` Railway service running `cloudflared tunnel run` with the token
4. User: create an Access application covering `admin.siddhesh-chaudhari.com` (both the SPA and /api/* paths on the same hostname); identity method email OTP; policy allows ONLY the owner's email (free tier covers 50 users)
5. Agent: backend verifies the `Cf-Access-Jwt-Assertion` header via PyJWT against the team JWKS at `https://<team>.cloudflareaccess.com/cdn-cgi/access/certs`, behind the env flag CF_ACCESS_ENABLED
6. Agent: deploy with CF_ACCESS_ENABLED=false first (app-layer auth carries the interim); flip to true after verification
7. Record CF_ACCESS_TEAM_DOMAIN in the env registry

## Tests
- Visiting `admin.siddhesh-chaudhari.com` prompts for Access email-OTP authentication
- With CF_ACCESS_ENABLED=true: a request with a forged or missing Cf-Access-Jwt-Assertion is rejected
- With CF_ACCESS_ENABLED=false: app-layer-only auth is restored
- Stopping the tunnel service makes the hostname stop reaching the backend

## Acceptance Criteria
- [ ] admin.siddhesh-chaudhari.com resolves through the named tunnel to the backend
- [ ] Access prompts for email OTP; only the owner is allowed
- [ ] Invalid/missing assertion rejected when CF_ACCESS_ENABLED=true
- [ ] CF_ACCESS_ENABLED=false restores app-layer-only auth
- [ ] SPA + API share the single hostname under one Access app

## Verify (agent)
`curl -sI https://admin.siddhesh-chaudhari.com | head -5 && curl -s -o /dev/null -w '%{http_code}' -H 'Cf-Access-Jwt-Assertion: invalid' https://admin.siddhesh-chaudhari.com/api/v1/health`

## Commit
`feat(infra): cloudflared tunnel + Access JWT gate behind CF_ACCESS_ENABLED`

## Invariants
- One hostname, one Access app — never split SPA and API across subdomains
- Named tunnels only; trycloudflare.com prohibited for production
- CF_ACCESS_ENABLED stays an env gate; launch (TD-36) turns it on permanently
