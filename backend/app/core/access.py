"""Cloudflare Access JWT verification, gated on ``CF_ACCESS_ENABLED``.

Defense in depth: when the edge gate is on, the origin refuses traffic that
did not pass through it. The JWKS is fetched once and cached module-level
with a TTL — never per request.
"""

import asyncio
import json
import time
import urllib.request
from typing import Any

import jwt
from fastapi import HTTPException, Request

from app.core.config import get_settings

JWKS_TTL_SECONDS = 300.0

_jwks_cache: dict[str, Any] = {"jwks": None, "fetched_at": 0.0}


def _jwks_url(team_domain: str) -> str:
    return f"https://{team_domain}/cdn-cgi/access/certs"


def _fetch_jwks(team_domain: str) -> jwt.PyJWKSet:
    with urllib.request.urlopen(_jwks_url(team_domain), timeout=10) as response:
        data = json.loads(response.read())
    keys: list[dict[str, Any]] = data["keys"]
    return jwt.PyJWKSet(keys)


async def _get_jwks(team_domain: str) -> jwt.PyJWKSet:
    now = time.monotonic()
    cached = _jwks_cache["jwks"]
    if (
        isinstance(cached, jwt.PyJWKSet)
        and now - float(_jwks_cache["fetched_at"]) < JWKS_TTL_SECONDS
    ):
        return cached
    jwks = await asyncio.to_thread(_fetch_jwks, team_domain)
    _jwks_cache["jwks"] = jwks
    _jwks_cache["fetched_at"] = now
    return jwks


async def verify_cf_access(request: Request) -> None:
    settings = get_settings()
    if not settings.cf_access_enabled:
        return

    team_domain = settings.cf_access_team_domain
    aud = settings.cf_access_aud
    if not team_domain or not aud:
        raise HTTPException(status_code=403, detail="Forbidden")

    assertion = request.headers.get("Cf-Access-Jwt-Assertion")
    if not assertion:
        raise HTTPException(status_code=403, detail="Forbidden")

    try:
        jwks = await _get_jwks(team_domain)
        kid = jwt.get_unverified_header(assertion).get("kid")
        signing_key = next((k.key for k in jwks.keys if k.key_id == kid), None)
        if signing_key is None:
            raise HTTPException(status_code=403, detail="Forbidden")
        jwt.decode(
            assertion,
            key=signing_key,
            algorithms=["RS256"],
            audience=aud,
            issuer=f"https://{team_domain}",
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=403, detail="Forbidden") from exc
