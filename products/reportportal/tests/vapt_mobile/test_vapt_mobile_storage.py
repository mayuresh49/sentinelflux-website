"""Standard VAPT mobile data storage security tests — MASVS-STORAGE / OWASP M2."""
import pytest
import requests

_MOBILE_UA = "Mozilla/5.0 (Linux; Android 14; Pixel 7) AppleWebKit/537.36 Mobile Safari/537.36"
_SENSITIVE_ENDPOINTS = [
    "/api/v1/user", "/api/v1/me", "/api/user",
    "/api/v1/profile", "/api/profile",
]
_SESSION_KEYWORDS = ("session", "token", "auth", "jwt", "sid", "access")


@pytest.mark.security
def test_M2_sensitive_api_responses_not_cacheable(vapt_base_url, vapt_api_token):
    """Authenticated API responses with user data must include Cache-Control: no-store — MASVS-STORAGE-2."""
    if not vapt_api_token:
        pytest.skip("No API token configured — authenticated endpoint caching check skipped")
    for path in _SENSITIVE_ENDPOINTS:
        resp = requests.get(
            f"{vapt_base_url}{path}",
            headers={"Authorization": f"Bearer {vapt_api_token}", "User-Agent": _MOBILE_UA},
            allow_redirects=False, timeout=10,
        )
        if resp.status_code == 200:
            cc = resp.headers.get("Cache-Control", "").lower()
            pragma = resp.headers.get("Pragma", "").lower()
            has_no_store = "no-store" in cc
            has_no_cache = "no-cache" in cc or "no-cache" in pragma
            assert has_no_store or has_no_cache, (
                f"Sensitive API response at {path} is cacheable — "
                f"mobile clients may persist sensitive data: Cache-Control: '{cc}'"
            )
            break


@pytest.mark.security
def test_M2_login_response_no_password_echo(vapt_base_url):
    """Login responses must never echo back the submitted password — MASVS-STORAGE-1."""
    login_paths = ["/api/v1/user/login", "/api/login", "/auth/login", "/auth/token"]
    for path in login_paths:
        try:
            resp = requests.post(
                f"{vapt_base_url}{path}",
                json={"username": "vapt_probe_nonexistent", "password": "vapt_probe_pass_m2"},
                headers={"User-Agent": _MOBILE_UA},
                allow_redirects=False, timeout=10,
            )
            if resp.status_code in (200, 400, 401, 422):
                assert "vapt_probe_pass_m2" not in resp.text,                     f"Login endpoint at {path} echoes back the submitted password — must never return passwords"
        except requests.exceptions.RequestException:
            pass


@pytest.mark.security
def test_M2_session_cookies_have_secure_flags(vapt_base_url):
    """Session cookies set for mobile clients must have HttpOnly and Secure flags — MASVS-STORAGE-3."""
    resp = requests.get(vapt_base_url, allow_redirects=True, timeout=10,
                        headers={"User-Agent": _MOBILE_UA})
    set_cookie_headers = [v for k, v in resp.raw.headers.items() if k.lower() == "set-cookie"]
    for header in set_cookie_headers:
        name = header.split("=")[0].strip().lower()
        if any(kw in name for kw in _SESSION_KEYWORDS):
            header_lower = header.lower()
            assert "httponly" in header_lower,                 f"Mobile session cookie '{name}' missing HttpOnly flag: {header}"
            if vapt_base_url.startswith("https://"):
                assert "secure" in header_lower,                     f"Mobile session cookie '{name}' missing Secure flag on HTTPS: {header}"


@pytest.mark.security
def test_M2_no_sensitive_data_in_url_params(vapt_base_url):
    """Sensitive fields must not appear as URL query parameters — MASVS-STORAGE-4."""
    resp = requests.get(vapt_base_url, allow_redirects=True, timeout=10,
                        headers={"User-Agent": _MOBILE_UA})
    for r in [resp, *resp.history]:
        url_lower = r.url.lower()
        sensitive_params = ("password=", "passwd=", "secret=", "credit_card=", "ssn=", "pin=")
        for param in sensitive_params:
            assert param not in url_lower,                 f"Sensitive field '{param.rstrip('=')}' exposed in URL: {r.url}"
