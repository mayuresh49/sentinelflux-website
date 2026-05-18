"""Standard VAPT injection tests — OWASP A03 Injection."""
import pytest
import requests

_SQL_PAYLOADS = [
    "' OR '1'='1",
    '" OR 1=1--',
    "1; DROP TABLE users--",
    "1 UNION SELECT null,null--",
]

_XSS_PAYLOAD = "<script>alert('xss_vapt_probe')</script>"

_PATH_TRAVERSAL = [
    "../../../etc/passwd",
    "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
    "....//....//....//etc/passwd",
]

_SSTI_PROBES = ["{{7*7}}", "${7*7}", "#{7*7}", "<%=7*7%>"]


@pytest.mark.security
def test_A03_sql_injection_no_500(vapt_base_url):
    """SQL injection payloads in query params must not cause 500 Internal Server Error."""
    probe_paths = ["/api/v1/user", "/api/v1/project", "/api/v1/booking", "/api/v1/search"]
    for path in probe_paths:
        for payload in _SQL_PAYLOADS:
            resp = requests.get(
                f"{vapt_base_url}{path}",
                params={"id": payload, "name": payload, "q": payload},
                allow_redirects=False, timeout=10,
            )
            assert resp.status_code != 500,                 f"SQL injection payload caused 500 at {path}?q={payload!r}"


@pytest.mark.security
def test_A03_xss_not_reflected_unescaped(vapt_base_url):
    """XSS payload in query params must not appear unescaped in the response body."""
    resp = requests.get(
        f"{vapt_base_url}/api/v1/user",
        params={"name": _XSS_PAYLOAD, "q": _XSS_PAYLOAD},
        allow_redirects=False, timeout=10,
    )
    assert _XSS_PAYLOAD not in resp.text,         f"XSS payload reflected unescaped in response: {resp.text[:300]}"


@pytest.mark.security
def test_A03_path_traversal_blocked(vapt_base_url):
    """Path traversal sequences must not expose filesystem content."""
    for traversal in _PATH_TRAVERSAL:
        resp = requests.get(f"{vapt_base_url}/api/{traversal}",
                            allow_redirects=False, timeout=10)
        # 302/401 are valid blocking responses (auth redirect or auth required)
        assert resp.status_code in (301, 302, 400, 401, 403, 404, 405),             f"Path traversal not blocked at /api/{traversal} (got {resp.status_code})"
        assert "root:" not in resp.text,             f"Path traversal may have exposed /etc/passwd at /api/{traversal}"


@pytest.mark.security
def test_A03_ssti_probe_not_evaluated(vapt_base_url):
    """Server-side template injection payloads must not be evaluated."""
    for probe in _SSTI_PROBES:
        resp = requests.get(
            f"{vapt_base_url}/api/v1/user",
            params={"name": probe, "q": probe},
            allow_redirects=False, timeout=10,
        )
        # If evaluated, "49" would appear and the raw probe string would not
        if resp.status_code == 200 and "49" in resp.text and probe not in resp.text:
            pytest.fail(f"SSTI probe {probe!r} appears to have been evaluated — '49' found")
