"""Standard VAPT mobile API security tests — MASVS-PLATFORM / OWASP M1/M6."""
import pytest
import requests

_MOBILE_UA = "Mozilla/5.0 (Linux; Android 14; Pixel 7) AppleWebKit/537.36 Mobile Safari/537.36"
_MOBILE_SPECIFIC_PATHS = [
    "/api/mobile", "/api/v1/mobile", "/mobile/api",
    "/api/app", "/app/api", "/api/v1/app",
]


@pytest.mark.security
def test_M1_mobile_specific_endpoints_require_auth(vapt_base_url):
    """Mobile-specific API endpoints must require authentication — MASVS-PLATFORM."""
    exposed = []
    for path in _MOBILE_SPECIFIC_PATHS:
        try:
            resp = requests.get(f"{vapt_base_url}{path}",
                                headers={"User-Agent": _MOBILE_UA},
                                allow_redirects=False, timeout=5)
            if resp.status_code == 200:
                exposed.append(path)
        except requests.exceptions.RequestException:
            pass
    assert not exposed, f"Mobile API endpoints accessible without authentication: {exposed}"


@pytest.mark.security
def test_M6_cors_not_wildcard_on_mobile_origin(vapt_base_url, vapt_api_token):
    """CORS must not allow wildcard origins on authenticated mobile API endpoints — MASVS-PLATFORM."""
    headers = {"Origin": "app://com.example.mobileapp", "User-Agent": _MOBILE_UA}
    if vapt_api_token:
        headers["Authorization"] = f"Bearer {vapt_api_token}"
    resp = requests.get(f"{vapt_base_url}/api/v1/user", headers=headers,
                        allow_redirects=False, timeout=10)
    acao = resp.headers.get("Access-Control-Allow-Origin", "")
    if resp.status_code == 200:
        assert acao != "*",             "Access-Control-Allow-Origin: * on authenticated endpoint — CORS misconfiguration affects mobile clients"


@pytest.mark.security
def test_M6_http_method_override_blocked(vapt_base_url):
    """HTTP method override headers must not bypass method restrictions — MASVS-PLATFORM."""
    resp = requests.get(
        f"{vapt_base_url}/api/v1/user",
        headers={
            "X-HTTP-Method-Override": "DELETE",
            "X-Method-Override": "DELETE",
            "User-Agent": _MOBILE_UA,
        },
        allow_redirects=False, timeout=10,
    )
    assert resp.status_code not in (200, 204),         f"HTTP method override header accepted ({resp.status_code}) — verify method restriction enforcement"


@pytest.mark.security
def test_M1_error_responses_no_internal_paths(vapt_base_url):
    """Error responses must not expose stack traces or internal paths to mobile clients — MASVS-PLATFORM."""
    resp = requests.get(
        f"{vapt_base_url}/api/mobile_vapt_probe_nonexistent_xz99",
        headers={"User-Agent": _MOBILE_UA},
        allow_redirects=False, timeout=10,
    )
    body = resp.text.lower()
    leak_signals = [
        "traceback", "stack trace", "exception in",
        "syntaxerror", "java.lang.", "at line ",
        "/home/", "/var/www/", "/app/",
    ]
    found = [s for s in leak_signals if s in body]
    assert not found, f"Error response exposes internal details to mobile clients: {found}"
