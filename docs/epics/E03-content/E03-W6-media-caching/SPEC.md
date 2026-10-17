# E03-W6 — Media caching: browser cache and Cloudflare edge cache

**Epic:** E03 Content · **Ticket:** E03-W6 · **Status:** Part A done (local); Part B pending (user, after deploy) · **Depends on:** E03-W1

## Purpose
Covers are fetched once and stored (W1, W5), but `/media/*` is served from the backend volume with no `Cache-Control` (only ETag and Last-Modified, checked 2026-10-17). Repeat visitors revalidate every file, and every visitor's request reaches the backend. The S3 path already sets a cache header (`backend/app/core/storage.py:71`); the local-disk path that production uses does not.

## Goal
A first visitor loads a cover from our storage; a repeat visitor loads it from the browser cache with no request; any visitor near a Cloudflare edge gets it from the edge cache. Cost: free (Cloudflare Free plan includes CDN caching and bandwidth).

## Reference files
- `backend/app/app.py` (`/media` StaticFiles mount), `backend/app/core/storage.py` (`CACHE_CONTROL`, key naming)
- Every storage writer: `features/collections/covers.py`, `features/certifications/`, `features/resumes/`, `features/projects/` (attachments), `features/posts/` (if any) — audit key naming
- `frontend/next.config.ts` (`/media` rewrite), `admin/nginx.conf` (`/media/` proxy)
- `backend/app/core/net.py` (client IP; affected by part B)
- `docs/DEPLOYMENT.md`, `docs/handoff/env-vars-registry.md`

## Functionality

**Part A (code):**
- Wrap the `/media` mount so responses carry `Cache-Control: public, max-age=31536000, immutable` for content-hashed keys, reusing the `CACHE_CONTROL` constant from `storage.py`.
- Audit every storage writer first. Any key that can be overwritten under the same name gets `Cache-Control: public, max-age=300` instead, or moves to content-hashed naming if that is trivial. Record the audit in this spec.
- 404s and errors carry no long cache header.

**Part B (infra, user-run, after Part A is deployed):**
1. Cloudflare SSL/TLS mode: **Full** (not Full Strict; Railway has no Cloudflare origin cert). This is required before proxying.
2. Turn on the proxy (orange cloud) for the **apex `siddhesh-chaudhari.com` only**.
3. Keep `admin.siddhesh-chaudhari.com` DNS-only (grey cloud), so admin login, lockout and the forged-IP protection (E01-W2) are unchanged.
4. Cloudflare caches `.jpg`/`.png`/`.webp` by extension by default and respects `Cache-Control`; no page rules are needed. HTML stays uncached (default).

## Edge cases
- **Client IP behind Cloudflare (main risk):** with the proxy on, Railway's edge sees Cloudflare's address. Railway staff say the edge then sets `X-Real-IP` from `CF-Connecting-IP`, but this is not documented. **Gate:** after enabling, submit one public form and check that the backend log/IP shows your public IP, not a Cloudflare range. If it shows a Cloudflare IP, turn the proxy off (grey cloud): public forms' per-IP anti-abuse would otherwise become global.
- **Certificate:** if Railway reports "Cloudflare proxy detected" and cannot renew the certificate, turn the proxy off. The site keeps working DNS-only.
- A replaced resume or attachment under the same key must not be cached for a year (Part A audit).
- ISR pages: Cloudflare does not cache HTML by default, so Next revalidation is unaffected.
- `immutable` must never be sent for `/api/*`.

## Testing
- **Part A:** a backend test asserts the header on a stored `/media` file, short or no cache for non-hashed keys, and no cache header on a 404. Check with `curl -I` through the frontend (`/media/...` via rewrite) and the admin (`nginx`), confirming the header survives both proxies.
- **Part B (production, user):** `curl -I https://siddhesh-chaudhari.com/media/<cover>` twice. The second response shows `cf-cache-status: HIT`. Run the client-IP gate above.

## Acceptance criteria
- [x] Part A: header served; audit recorded; tests pass.
- [ ] Part B: `cf-cache-status: HIT` on covers; the client-IP gate passes, or the proxy is reverted with a note.
- [ ] `docs/DEPLOYMENT.md` documents the Cloudflare settings and the rollback.

## Storage key audit

Writers to storage (grep of `put(` / `get_storage` / `StorageAdapter` across `backend/`), 2026-10-17:

| Feature | Writer | Key pattern | Content-hashed? |
|---|---|---|---|
| collections (covers, W1/W5) | `features/collections/covers.py::_store_cover` via `content_hashed_key` | `<book\|anime\|manhwa\|...>-<sha256[:12]>.<png\|webp\|jpg>` | Yes: same name implies same bytes |
| resumes | `scripts/seed_resumes.py` (`resume_file_key`, `storage.put`) | `resumes/<variant>-<sha256[:12]>.pdf` | Yes |
| certifications | no code writer; `file_key` is only read (`get_url`) | n/a (manual upload) | Unknown; treated as overwritable |
| projects attachments | no code writer; `storage_key` only read | n/a (manual upload) | Unknown; treated as overwritable |
| skills icons | no code writer; `icon_key` only read | n/a | Unknown; treated as overwritable |
| posts | no storage use | n/a | n/a |

Rule implemented in `backend/app/core/media.py`: a key matching `-<12 lowercase hex>.<ext>` is treated as content-hashed and gets `CACHE_CONTROL` (`public, max-age=31536000, immutable`, value verified unchanged). Every other key under `/media` gets `public, max-age=300`. Responses other than 200/206/304 (404 etc.) get no `Cache-Control`. Only the `/media` mount is affected; `/api/*` is untouched.

Verified locally (preview backend 24785, frontend 24735 rewrite, admin 24755 proxy): the long header survives both proxies; 404 has none.

## Rollback
- **Part A:** revert.
- **Part B:** grey-cloud the apex in Cloudflare (takes effect in minutes).

Sources: [Railway public networking](https://docs.railway.com/deploy/exposing-your-app); Railway forum on [Cloudflare and client IP](https://station.railway.com/questions/reveal-real-ip-address-when-using-cloudf-dec5795d) and [Full (Strict)](https://station.railway.com/questions/cloudflare-ssl-full-strict-does-not-ab35244a).
