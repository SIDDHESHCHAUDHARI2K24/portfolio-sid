"""client_ip: X-Real-IP honoured only from a trusted proxy peer."""

from collections.abc import Iterator

import pytest
from pydantic import ValidationError
from starlette.requests import Request

from app.core.config import Settings, get_settings
from app.core.net import client_ip

TRUSTED_PEER = "10.164.196.239"


def _request(peer: str | None, real_ip: str | None = None) -> Request:
    headers = [] if real_ip is None else [(b"x-real-ip", real_ip.encode())]
    scope = {
        "type": "http",
        "headers": headers,
        "client": (peer, 4321) if peer is not None else None,
    }
    return Request(scope)


@pytest.fixture
def trusted_cidrs() -> Iterator[None]:
    settings = get_settings()
    old = settings.trusted_proxy_cidrs
    settings.trusted_proxy_cidrs = ["10.0.0.0/8", "fd00::/8"]
    yield
    settings.trusted_proxy_cidrs = old


@pytest.mark.usefixtures("trusted_cidrs")
def test_trusted_peer_valid_header_returns_header() -> None:
    assert client_ip(_request(TRUSTED_PEER, "203.0.113.7")) == "203.0.113.7"


@pytest.mark.usefixtures("trusted_cidrs")
def test_header_value_is_stripped() -> None:
    assert client_ip(_request(TRUSTED_PEER, "  203.0.113.7 ")) == "203.0.113.7"


@pytest.mark.usefixtures("trusted_cidrs")
def test_untrusted_peer_ignores_header() -> None:
    assert client_ip(_request("198.51.100.9", "203.0.113.7")) == "198.51.100.9"


@pytest.mark.usefixtures("trusted_cidrs")
@pytest.mark.parametrize(
    "header",
    [None, "", "   ", "203.0.113.7, 10.0.0.1", "not-an-ip", "203.0.113.999", "fe80::1%eth0"],
)
def test_trusted_peer_bad_header_falls_back_to_peer(header: str | None) -> None:
    assert client_ip(_request(TRUSTED_PEER, header)) == TRUSTED_PEER


@pytest.mark.usefixtures("trusted_cidrs")
def test_ipv6_client_via_trusted_peer() -> None:
    assert client_ip(_request(TRUSTED_PEER, "2001:DB8::1")) == "2001:db8::1"


@pytest.mark.usefixtures("trusted_cidrs")
def test_ipv6_trusted_peer() -> None:
    assert client_ip(_request("fd12:3456::7", "203.0.113.7")) == "203.0.113.7"


@pytest.mark.usefixtures("trusted_cidrs")
def test_ipv4_mapped_header_normalized() -> None:
    assert client_ip(_request(TRUSTED_PEER, "::ffff:1.2.3.4")) == "1.2.3.4"


@pytest.mark.usefixtures("trusted_cidrs")
def test_ipv4_mapped_peer_normalized_and_matched() -> None:
    assert client_ip(_request("::ffff:10.1.2.3", "203.0.113.7")) == "203.0.113.7"
    assert client_ip(_request("::ffff:198.51.100.9", "203.0.113.7")) == "198.51.100.9"


def test_empty_cidr_list_never_trusts_header() -> None:
    assert get_settings().trusted_proxy_cidrs == []
    assert client_ip(_request(TRUSTED_PEER, "203.0.113.7")) == TRUSTED_PEER


def test_no_client_is_unknown() -> None:
    assert client_ip(_request(None, "203.0.113.7")) == "unknown"


def test_non_ip_peer_returned_as_is() -> None:
    assert client_ip(_request("testclient", "203.0.113.7")) == "testclient"


def test_invalid_cidr_fails_with_variable_name_not_value() -> None:
    with pytest.raises(ValidationError) as excinfo:
        Settings(trusted_proxy_cidrs=["10.0.0.0/8", "bogus-cidr-value"])
    message = str(excinfo.value)
    assert "TRUSTED_PROXY_CIDRS" in message
    assert "bogus-cidr-value" not in message


def test_invalid_cidr_from_env_fails_at_load(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TRUSTED_PROXY_CIDRS", '["10.0.0.0/33"]')
    with pytest.raises(ValidationError, match="TRUSTED_PROXY_CIDRS"):
        Settings()


def test_valid_cidrs_load_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TRUSTED_PROXY_CIDRS", '["10.0.0.0/8","fd00::/8"]')
    assert Settings().trusted_proxy_cidrs == ["10.0.0.0/8", "fd00::/8"]
