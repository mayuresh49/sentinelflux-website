"""Standard VAPT security headers tests — OWASP A05 Security Misconfiguration."""
import pytest
import requests


@pytest.mark.security
def test_A05_response_has_content_type(vapt_base_url):
    """Every HTTP response must include a Content-Type header."""
    resp = requests.get(vapt_base_url, timeout=10, allow_redirects=True)
    assert "content-type" in {h.lower() for h in resp.headers},         "Missing Content-Type header in root response"


@pytest.mark.security
def test_A05_server_header_no_version_disclosure(vapt_base_url):
    """Server header must not disclose software version strings."""
    resp = requests.get(vapt_base_url, timeout=10, allow_redirects=True)
    server = resp.headers.get("Server", "")
    version_tokens = ["Apache/", "nginx/", "Jetty/", "Tomcat/", "Python/", "Microsoft-IIS/"]
    disclosed = [t for t in version_tokens if t in server]
    assert not disclosed, f"Server header discloses version: '{server}'"


@pytest.mark.security
def test_A05_x_content_type_options_nosniff(vapt_base_url, vapt_api_token):
    """Authenticated API responses should carry X-Content-Type-Options: nosniff."""
    headers = {}
    if vapt_api_token:
        headers["Authorization"] = f"Bearer {vapt_api_token}"
    resp = requests.get(f"{vapt_base_url}/api/v1/user",
                        headers=headers, timeout=10, allow_redirects=False)
    if resp.status_code == 200:
        val = resp.headers.get("X-Content-Type-Options", "")
        assert "nosniff" in val.lower(),             f"Missing X-Content-Type-Options: nosniff on authenticated response (got '{val}')"


@pytest.mark.security
def test_A05_error_response_no_stack_trace(vapt_base_url):
    """Error responses must not expose stack traces or internal paths."""
    resp = requests.get(f"{vapt_base_url}/api/vapt_probe_nonexistent_endpoint_xz99",
                        timeout=10, allow_redirects=False)
    body = resp.text.lower()
    leak_signals = [
        "traceback", "stack trace", "exception in", "at line ",
        "syntaxerror", "java.lang.", "org.springframework",
        "errno", "/home/", "/var/www/",
    ]
    found = [s for s in leak_signals if s in body]
    assert not found, f"Error response leaks debug info: {found}"


@pytest.mark.security
def test_A05_cors_wildcard_not_set(vapt_base_url, vapt_api_token):
    """CORS Access-Control-Allow-Origin must not be a blanket wildcard on authenticated endpoints."""
    headers = {"Origin": "https://evil.example.com"}
    if vapt_api_token:
        headers["Authorization"] = f"Bearer {vapt_api_token}"
    resp = requests.get(f"{vapt_base_url}/api/v1/user", headers=headers,
                        allow_redirects=False, timeout=10)
    acao = resp.headers.get("Access-Control-Allow-Origin", "")
    if resp.status_code == 200:
        assert acao != "*",             "Access-Control-Allow-Origin: * set on an authenticated endpoint — CORS misconfiguration"
