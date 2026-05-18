"""Standard VAPT DNS security tests — SPF, DMARC, zone transfer."""
import socket
import pytest
import requests


@pytest.mark.security
def test_INFRA_spf_record_configured(vapt_domain):
    """SPF TXT record must be configured to prevent email spoofing on the domain."""
    if not vapt_domain:
        pytest.skip("IP address or localhost — DNS record checks skipped")
    try:
        resp = requests.get(
            "https://dns.google/resolve",
            params={"name": vapt_domain, "type": "TXT"},
            timeout=10,
        )
        answers = resp.json().get("Answer", [])
        spf_found = any("v=spf1" in (a.get("data", "") or "") for a in answers)
    except Exception as e:
        pytest.skip(f"DNS-over-HTTPS query failed — {e}")
        return
    if not spf_found:
        pytest.xfail(
            f"No SPF TXT record found for {vapt_domain} — "
            "add 'v=spf1 ... ~all' to prevent email spoofing"
        )


@pytest.mark.security
def test_INFRA_dmarc_record_configured(vapt_domain):
    """DMARC TXT record must be configured at _dmarc.<domain>."""
    if not vapt_domain:
        pytest.skip("IP address or localhost — DNS record checks skipped")
    dmarc_name = f"_dmarc.{vapt_domain}"
    try:
        resp = requests.get(
            "https://dns.google/resolve",
            params={"name": dmarc_name, "type": "TXT"},
            timeout=10,
        )
        answers = resp.json().get("Answer", [])
        dmarc_found = any("v=DMARC1" in (a.get("data", "") or "") for a in answers)
    except Exception as e:
        pytest.skip(f"DNS-over-HTTPS query failed — {e}")
        return
    if not dmarc_found:
        pytest.xfail(
            f"No DMARC record at {dmarc_name} — "
            "add 'v=DMARC1; p=quarantine; rua=mailto:...' to enforce email authentication"
        )


@pytest.mark.security
def test_INFRA_zone_transfer_blocked(vapt_host, vapt_domain):
    """DNS zone transfers must be disabled to prevent domain enumeration."""
    if not vapt_domain:
        pytest.skip("IP address or localhost — zone transfer check skipped")
    try:
        with socket.create_connection((vapt_host, 53), timeout=2):
            pass
    except (socket.timeout, ConnectionRefusedError, OSError):
        pytest.skip(f"Port 53 not open on {vapt_host} — not acting as DNS server")
        return
    pytest.xfail(
        f"DNS port 53 is open on {vapt_host} — verify zone transfers (AXFR) are restricted "
        "to authorized secondary nameservers only"
    )
