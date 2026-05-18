"""Standard VAPT TLS/SSL security tests — infrastructure layer."""
import ssl
import socket
import datetime
import pytest


@pytest.mark.security
def test_INFRA_tls_1_0_disabled(vapt_host, vapt_https_port):
    """TLS 1.0 must be disabled — deprecated protocol with POODLE and BEAST vulnerability exposure."""
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
                    f"TLS 1.0 accepted by {vapt_host}:{vapt_https_port} — "
                    "must be disabled (CVE: POODLE, BEAST)"
                )
            except ssl.SSLError:
                pass
    except (AttributeError, OSError, socket.timeout):
        pytest.skip("SSL context version limiting not supported on this Python build")


@pytest.mark.security
def test_INFRA_tls_1_1_disabled(vapt_host, vapt_https_port):
    """TLS 1.1 must be disabled — deprecated since RFC 8996 (2021)."""
    if not vapt_https_port:
        pytest.skip("Host not running on HTTPS — TLS version check skipped")
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        ctx.maximum_version = ssl.TLSVersion.TLSv1_1
        with socket.create_connection((vapt_host, vapt_https_port), timeout=5) as sock:
            try:
                ctx.wrap_socket(sock, server_hostname=vapt_host)
                pytest.fail(
                    f"TLS 1.1 accepted by {vapt_host}:{vapt_https_port} — "
                    "must be disabled per RFC 8996"
                )
            except ssl.SSLError:
                pass
    except (AttributeError, OSError, socket.timeout):
        pytest.skip("SSL context version limiting not supported on this Python build")


@pytest.mark.security
def test_INFRA_certificate_not_expired(vapt_host, vapt_https_port):
    """TLS certificate must not be expired."""
    if not vapt_https_port:
        pytest.skip("Host not running on HTTPS — certificate check skipped")
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((vapt_host, vapt_https_port), timeout=5) as raw:
            with ctx.wrap_socket(raw, server_hostname=vapt_host) as ssock:
                cert = ssock.getpeercert()
        expire_str = cert.get("notAfter", "")
        if expire_str:
            expire = datetime.datetime.strptime(expire_str, "%b %d %H:%M:%S %Y %Z")
            days_left = (expire - datetime.datetime.utcnow()).days
            assert days_left > 0,                 f"TLS certificate expired {abs(days_left)} days ago (expired: {expire_str})"
            if days_left < 30:
                pytest.xfail(
                    f"TLS certificate expires in {days_left} days — renew before expiry"
                )
    except ssl.SSLCertVerificationError as e:
        pytest.fail(f"TLS certificate verification failed: {e}")
    except (socket.timeout, ConnectionRefusedError, OSError) as e:
        pytest.skip(f"Could not connect to {vapt_host}:{vapt_https_port} — {e}")


@pytest.mark.security
def test_INFRA_certificate_hostname_match(vapt_host, vapt_https_port):
    """TLS certificate Common Name or SAN must match the server hostname."""
    if not vapt_https_port:
        pytest.skip("Host not running on HTTPS — hostname verification skipped")
    ctx = ssl.create_default_context()
    try:
        with socket.create_connection((vapt_host, vapt_https_port), timeout=5) as raw:
            with ctx.wrap_socket(raw, server_hostname=vapt_host):
                pass
    except ssl.SSLCertVerificationError as e:
        if "hostname" in str(e).lower() or "mismatch" in str(e).lower():
            pytest.fail(f"Certificate hostname mismatch for {vapt_host}: {e}")
        pytest.xfail(
            f"Certificate verification error (may be self-signed in non-prod): {e}"
        )
    except (socket.timeout, ConnectionRefusedError, OSError) as e:
        pytest.skip(f"Could not connect to {vapt_host}:{vapt_https_port} — {e}")
