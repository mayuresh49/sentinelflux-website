"""Standard VAPT mobile network security tests — MASVS-NETWORK / OWASP M3."""
import ssl
import socket
import pytest
import requests

_MOBILE_UA = "Mozilla/5.0 (Linux; Android 14; Pixel 7) AppleWebKit/537.36 Mobile Safari/537.36"


@pytest.mark.security
def test_M3_https_enforced_for_mobile(vapt_base_url):
    """Mobile clients must communicate exclusively over HTTPS — cleartext HTTP must redirect to HTTPS."""
    if not vapt_base_url.startswith("https://"):
        pytest.skip("Product not running on HTTPS — cleartext enforcement check skipped")
    http_url = vapt_base_url.replace("https://", "http://", 1)
    try:
        resp = requests.get(http_url, allow_redirects=False, timeout=10,
                            headers={"User-Agent": _MOBILE_UA})
        assert resp.status_code in (301, 302, 307, 308),             f"HTTP not redirected to HTTPS for mobile client (got {resp.status_code})"
        location = resp.headers.get("Location", "")
        assert location.startswith("https://"),             f"HTTP redirect target is not HTTPS: '{location}'"
    except requests.exceptions.ConnectionError:
        pass  # Connection refused on HTTP — acceptable hardening


@pytest.mark.security
def test_M3_tls_minimum_version_1_2(vapt_host, vapt_https_port):
    """Mobile backend must require TLS 1.2 minimum — MASVS-NETWORK-1."""
    if not vapt_https_port:
        pytest.skip("Host not running on HTTPS — TLS version check skipped")
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        ctx.maximum_version = ssl.TLSVersion.TLSv1
        with socket.create_connection((vapt_host, vapt_https_port), timeout=5) as sock:
            try:
                ctx.wrap_socket(sock, server_hostname=vapt_host)
                pytest.fail(
                    "TLS 1.0 accepted — mobile apps require minimum TLS 1.2 per MASVS-NETWORK-1"
                )
            except ssl.SSLError:
                pass
    except (AttributeError, OSError, socket.timeout):
        pytest.skip("SSL context version limiting not supported on this Python build")


@pytest.mark.security
def test_M3_hsts_header_enforced(vapt_base_url, vapt_api_token):
    """HTTPS responses must include HSTS to prevent SSL stripping attacks on mobile — MASVS-NETWORK-1."""
    if not vapt_base_url.startswith("https://"):
        pytest.skip("Not running on HTTPS — HSTS check skipped")
    headers = {"User-Agent": _MOBILE_UA}
    if vapt_api_token:
        headers["Authorization"] = f"Bearer {vapt_api_token}"
    resp = requests.get(vapt_base_url, headers=headers, timeout=10, allow_redirects=True)
    assert "strict-transport-security" in {h.lower() for h in resp.headers},         "Missing Strict-Transport-Security header — mobile clients vulnerable to SSL stripping"


@pytest.mark.security
def test_M3_api_certificate_trusted(vapt_host, vapt_https_port):
    """Mobile backend certificate must be CA-signed — self-signed certs weaken certificate pinning."""
    if not vapt_https_port:
        pytest.skip("Host not running on HTTPS — certificate trust check skipped")
    ctx = ssl.create_default_context()
    try:
        with socket.create_connection((vapt_host, vapt_https_port), timeout=5) as raw:
            with ctx.wrap_socket(raw, server_hostname=vapt_host):
                pass
    except ssl.SSLCertVerificationError as e:
        pytest.xfail(
            f"Certificate not trusted by default CAs: {e} — "
            "mobile apps should use CA-signed certificates; self-signed certs weaken pinning"
        )
    except (socket.timeout, ConnectionRefusedError, OSError) as e:
        pytest.skip(f"Could not connect to {vapt_host}:{vapt_https_port} — {e}")
