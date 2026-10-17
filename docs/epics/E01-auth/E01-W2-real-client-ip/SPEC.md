# E01-W2 — Real client IP behind the proxy

**Epic:** E01 Auth · **Ticket:** E01-W2 · **Status:** Ready · **Depends on:** none

## Purpose
All requests reach the backend from a proxy's private IP (logs show `10.164.196.239` for every login). Lockout, rate limits, and forms anti-abuse are therefore global: one attacker can lock the admin out, and audit rows record the proxy.

## Goal
Lockout, rate limiting, and audit rows use the real caller's IP, and a caller cannot forge it.

## Reference files
- `admin/nginx.conf` (`/api/` and `/media/` proxy headers)
- `Dockerfile` (uvicorn CMD)
- `backend/app/core/config.py` (new setting)
- `backend/app/core/net.py` (new)
- `backend/app/features/auth/utils.py`, `backend/app/features/auth/endpoints/router.py` (`client_ip`, slowapi `Limiter`)
- `backend/app/features/forms/endpoints/router.py:56` (imports `client_ip` from the auth slice)
- `backend/app/features/crawlers/middleware.py:84` (`request.client.host`)
- `frontend/next.config.ts` (rewrites to the private backend)
- `backend/.env.example`, `docs/handoff/env-vars-registry.md`

## Functionality
- **Trust model:** the Railway edge sets `X-Real-IP` to the client IP and overwrites any client-sent copy ([Railway staff answer](https://station.railway.com/questions/which-client-address-headers-does-the-ra-fb9e36d7)). Cloudflare is DNS-only, so there is no CDN hop. `X-Forwarded-For` is not used because its hop order is unreliable.
- **nginx:** `proxy_set_header X-Real-IP $http_x_real_ip;` (the edge's value, passed through). Drop `X-Forwarded-For $proxy_add_x_forwarded_for`.
- **Setting:** `TRUSTED_PROXY_CIDRS: list[str]` (default `[]`). In production, set it to the Railway private network ranges actually seen (`10.0.0.0/8`, and `fd00::/8` for IPv6 private networking).
- **`app/core/net.py: client_ip(request) -> str`:** if the direct peer (`request.client.host`) is inside a trusted CIDR and `X-Real-IP` holds a valid IP, return it (normalized; IPv6 as its `/64`). Otherwise return the peer (same normalization), or `"unknown"` if there is none.
- **Call sites:** auth router, the slowapi `key_func`, the forms router, and crawler middleware all use `app.core.net.client_ip`. Delete `features/auth/utils.py`; this also removes the forms-to-auth cross-slice import.
- **uvicorn:** unchanged. No `--forwarded-allow-ips='*'`.

## Edge cases
- Peer not trusted (local dev, direct hit) → use the peer and ignore the header, so it cannot be spoofed.
- Trusted peer, header missing, empty, a comma list, or not an IP → use the peer.
- IPv6 client, or IPv4-mapped IPv6 (`::ffff:1.2.3.4`) → normalize with `ipaddress`; mapped addresses become plain IPv4, and real IPv6 is keyed by its `/64` network string (e.g. `2001:db8:1:2::/64`) so rotating addresses inside one subscriber prefix cannot dodge lockout or limits. The result fits `String(45)`.
- Malformed CIDR in the setting → fail at startup with the variable name.
- Next.js rewrites (public forms and crawler traffic): confirm the frontend proxy passes the edge's `X-Real-IP` through. If it does not, forms and crawlers fall back to the peer IP (today's behavior), recorded as a follow-up.
- The rate limiter key changes from the proxy IP to the client IP: existing limits reset on deploy. Expected.
- Unknown peer (`request.client` is `None`, as in some test clients) → `"unknown"`.

## Testing
- Unit (`backend/app/tests/test_net.py`): trusted peer plus valid header; untrusted peer plus header; missing, malformed, and list headers; IPv6 and mapped IPv6; empty CIDR list.
- Integration (auth tests): two different `X-Real-IP` values from a trusted peer lock out independently; slowapi counts per resolved IP.
- `uv run ruff check . && uv run mypy app && uv run pytest -q`.
- Production, after deploy (user-approved): `login_attempts.ip` and the access log show your public IP; a request sending a forged `X-Real-IP` still records your real IP.

## Acceptance criteria
- [ ] Per-caller lockout and rate limits are proven by tests.
- [ ] No production code path reads `request.client.host` directly, except `core/net.py`.
- [ ] The forms slice no longer imports from the auth slice.
- [ ] `TRUSTED_PROXY_CIDRS` is documented in `.env.example` and the env registry.
- [ ] The production check confirms the real IP and that a forged header is rejected.

## Rollback
Unset `TRUSTED_PROXY_CIDRS` (behaves as today), or revert and redeploy the backend and admin services.
