"""Client address resolution behind the Railway proxy chain."""

from functools import lru_cache
from ipaddress import (
    IPv4Address,
    IPv4Network,
    IPv6Address,
    IPv6Network,
    ip_address,
    ip_network,
)

from fastapi import Request

from app.core.config import get_settings

_REAL_IP_HEADER = "x-real-ip"


@lru_cache
def _networks(cidrs: tuple[str, ...]) -> tuple[IPv4Network | IPv6Network, ...]:
    return tuple(ip_network(c, strict=False) for c in cidrs)


def _normalize(addr: IPv4Address | IPv6Address) -> IPv4Address | IPv6Address:
    """Collapse IPv4-mapped IPv6 (``::ffff:1.2.3.4``) to plain IPv4."""
    if isinstance(addr, IPv6Address) and addr.ipv4_mapped is not None:
        return addr.ipv4_mapped
    return addr


def client_ip(request: Request) -> str:
    """Real caller address for rate limiting, lockout and audit rows.

    ``X-Real-IP`` is honoured only when the direct peer sits inside
    ``TRUSTED_PROXY_CIDRS`` (the Railway edge overwrites any client-sent copy);
    otherwise the header is ignored so a caller cannot forge it. Falls back to
    the peer, or ``"unknown"`` when there is none.
    """
    if request.client is None:
        return "unknown"
    peer = request.client.host
    try:
        peer_addr = _normalize(ip_address(peer))
    except ValueError:
        return peer

    networks = _networks(tuple(get_settings().trusted_proxy_cidrs))
    if any(peer_addr in net for net in networks):
        raw = request.headers.get(_REAL_IP_HEADER, "").strip()
        if raw and "%" not in raw:
            try:
                return str(_normalize(ip_address(raw)))
            except ValueError:
                pass
    return str(peer_addr)
