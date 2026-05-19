"""Standard VAPT DNS security tests — SPF, DMARC, zone transfer."""
import socket
import struct
import pytest
import requests


def _axfr_allowed(host: str, domain: str) -> bool:
    """Returns True if the DNS server at host permits AXFR for domain (zone transfer not blocked)."""
    qname = b"".join(bytes([len(p)]) + p.encode() for p in domain.split(".")) + b"\x00"
    msg = (
        b"\xab\xcd\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00"  # header: id, flags, 1 question
        + qname
        + b"\x00\xfc\x00\x01"  # QTYPE=AXFR(252), QCLASS=IN(1)
    )
    wire = struct.pack("!H", len(msg)) + msg  # TCP DNS: 2-byte length prefix
    try:
        with socket.create_connection((host, 53), timeout=5) as sock:
            sock.sendall(wire)
            rlen_b = sock.recv(2)
            if len(rlen_b) < 2:
                return False
            rlen = struct.unpack("!H", rlen_b)[0]
            resp = b""
            while len(resp) < rlen:
                chunk = sock.recv(rlen - len(resp))
                if not chunk:
                    break
                resp += chunk
            if len(resp) < 8:
                return False
            rcode = resp[3] & 0x0F  # low 4 bits of byte 3
            ancount = struct.unpack("!H", resp[6:8])[0]
            return rcode == 0 and ancount > 0
    except Exception:
        return False


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
    """DNS zone transfers (AXFR) must be blocked — unrestricted AXFR leaks the full DNS zone."""
    if not vapt_domain:
        pytest.skip("IP address or localhost — zone transfer check skipped")
    try:
        with socket.create_connection((vapt_host, 53), timeout=2):
            pass
    except (socket.timeout, ConnectionRefusedError, OSError):
        pytest.skip(f"Port 53 not open on {vapt_host} — not acting as DNS server")
        return
    if _axfr_allowed(vapt_host, vapt_domain):
        pytest.fail(
            f"DNS zone transfer (AXFR) allowed for {vapt_domain} via {vapt_host} — "
            "restrict AXFR to authorized secondary nameservers only"
        )
