"""Standard VAPT session management tests — OWASP A07 Session Management."""
import pytest
import requests

_SESSION_KEYWORDS = ("session", "token", "auth", "jwt", "sid", "access")


@pytest.mark.security
def test_A07_session_cookie_httponly_flag(vapt_base_url):
    """Session cookies must have the HttpOnly flag to prevent XSS-based theft."""
    resp = requests.get(vapt_base_url, allow_redirects=True, timeout=10)
    set_cookie_headers = resp.raw.headers.getlist("Set-Cookie") if hasattr(resp.raw.headers, "getlist")         else [v for k, v in resp.raw.headers.items() if k.lower() == "set-cookie"]
    for header in set_cookie_headers:
        header_lower = header.lower()
        name = header.split("=")[0].strip().lower()
        if any(kw in name for kw in _SESSION_KEYWORDS):
            assert "httponly" in header_lower,                 f"Session cookie '{name}' is missing the HttpOnly flag: {header}"


@pytest.mark.security
def test_A07_session_token_not_in_url(vapt_base_url):
    """Session tokens must not appear as URL query parameters."""
    resp = requests.get(vapt_base_url, allow_redirects=True, timeout=10)
    for r in [resp, *resp.history]:
        url_lower = r.url.lower()
        for banned in ("sessionid=", "jsessionid=", "phpsessid=", "sid="):
            assert banned not in url_lower,                 f"Session ID exposed in URL: {r.url}"


@pytest.mark.security
def test_A07_secure_cookie_flag_on_https(vapt_base_url):
    """Session cookies must have the Secure flag when running on HTTPS."""
    if not vapt_base_url.startswith("https://"):
        pytest.skip("Not running on HTTPS — Secure cookie flag check skipped")
    resp = requests.get(vapt_base_url, allow_redirects=True, timeout=10)
    set_cookie_headers = [v for k, v in resp.raw.headers.items() if k.lower() == "set-cookie"]
    for header in set_cookie_headers:
        name = header.split("=")[0].strip().lower()
        if any(kw in name for kw in _SESSION_KEYWORDS):
            assert "secure" in header.lower(),                 f"Session cookie '{name}' missing Secure flag on HTTPS: {header}"


@pytest.mark.security
def test_A07_session_cookie_samesite_flag(vapt_base_url):
    """Session cookies should declare a SameSite attribute to mitigate CSRF."""
    resp = requests.get(vapt_base_url, allow_redirects=True, timeout=10)
    set_cookie_headers = [v for k, v in resp.raw.headers.items() if k.lower() == "set-cookie"]
    missing = []
    for header in set_cookie_headers:
        name = header.split("=")[0].strip().lower()
        if any(kw in name for kw in _SESSION_KEYWORDS):
            if "samesite" not in header.lower():
                missing.append(name)
    if missing:
        pytest.xfail(
            f"Cookies {missing} have no SameSite attribute — "
            "verify CSRF protection is enforced at the application layer"
        )
