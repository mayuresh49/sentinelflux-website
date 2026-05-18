"""Standard VAPT web-layer tests — OWASP A01/A05 (Clickjacking, Open Redirect, Web Headers)."""
import re
import pytest
import requests

_REDIRECT_PARAMS = ["next", "redirect", "redirect_uri", "url", "return", "returnUrl", "goto", "continue"]
_SAFE_REFERRER_POLICIES = {
    "no-referrer", "no-referrer-when-downgrade",
    "strict-origin", "strict-origin-when-cross-origin", "same-origin",
}


@pytest.mark.security
def test_A05_clickjacking_protection(vapt_base_url):
    """Web pages must include X-Frame-Options or CSP frame-ancestors to prevent clickjacking."""
    resp = requests.get(vapt_base_url, timeout=10, allow_redirects=True)
    headers_lower = {h.lower(): v.lower() for h, v in resp.headers.items()}
    xfo = headers_lower.get("x-frame-options", "")
    csp = headers_lower.get("content-security-policy", "")
    has_xfo = xfo in ("deny", "sameorigin")
    has_csp_frame = "frame-ancestors" in csp
    assert has_xfo or has_csp_frame, (
        f"Missing clickjacking protection — X-Frame-Options: '{xfo}', "
        f"CSP frame-ancestors: {'present' if has_csp_frame else 'absent'}"
    )


@pytest.mark.security
def test_A01_open_redirect_blocked(vapt_base_url):
    """Redirect parameters must not forward requests to external hostnames."""
    external = "https://evil.example.com/phish"
    for param in _REDIRECT_PARAMS:
        resp = requests.get(
            f"{vapt_base_url}/login",
            params={param: external},
            allow_redirects=False, timeout=10,
        )
        if resp.status_code in (301, 302, 307, 308):
            location = resp.headers.get("Location", "")
            assert not location.startswith("https://evil.example.com"),                 f"Open redirect via ?{param}= redirects to external host: {location}"


@pytest.mark.security
def test_A05_referrer_policy_header(vapt_base_url):
    """Referrer-Policy header should restrict URL leakage to third parties."""
    resp = requests.get(vapt_base_url, timeout=10, allow_redirects=True)
    policy = resp.headers.get("Referrer-Policy", "")
    if policy:
        assert policy.lower() in _SAFE_REFERRER_POLICIES,             f"Referrer-Policy value '{policy}' may leak sensitive URLs"
    else:
        pytest.xfail("Referrer-Policy header absent — browser defaults may leak referrer")


@pytest.mark.security
def test_A05_no_sensitive_info_in_html_comments(vapt_base_url):
    """HTML source must not contain credentials or internal paths in HTML comments."""
    resp = requests.get(vapt_base_url, timeout=10, allow_redirects=True)
    if "text/html" not in resp.headers.get("Content-Type", ""):
        pytest.skip("Root endpoint does not return HTML")
    comments = re.findall(r"<!--(.*?)-->", resp.text, re.DOTALL)
    sensitive = ["password", "secret", "api_key", "private", "todo:", "fixme:", "hack:"]
    for comment in comments:
        found = [s for s in sensitive if s in comment.lower()]
        assert not found,             f"HTML comment may contain sensitive info ({found}): {comment[:120]!r}"
