"""Standard VAPT transport security tests — OWASP A02 Cryptographic Failures."""
import pytest
import requests


@pytest.mark.security
def test_A02_http_redirects_to_https(vapt_base_url):
    """Plain HTTP requests must be redirected to HTTPS in production environments."""
    if not vapt_base_url.startswith("https://"):
        pytest.skip("Product not running on HTTPS — redirect check skipped for local envs")
    http_url = vapt_base_url.replace("https://", "http://", 1)
    resp = requests.get(http_url, allow_redirects=False, timeout=10)
    assert resp.status_code in (301, 302, 307, 308),         f"HTTP does not redirect to HTTPS (got {resp.status_code})"
    location = resp.headers.get("Location", "")
    assert location.startswith("https://"),         f"HTTP redirect target is not HTTPS: '{location}'"


@pytest.mark.security
def test_A02_hsts_header_present(vapt_base_url, vapt_api_token):
    """HTTPS responses must include a Strict-Transport-Security header."""
    if not vapt_base_url.startswith("https://"):
        pytest.skip("Product not running on HTTPS — HSTS check skipped")
    headers = {}
    if vapt_api_token:
        headers["Authorization"] = f"Bearer {vapt_api_token}"
    resp = requests.get(vapt_base_url, headers=headers, timeout=10, allow_redirects=True)
    assert "strict-transport-security" in {h.lower() for h in resp.headers},         "Missing Strict-Transport-Security (HSTS) header on HTTPS response"


@pytest.mark.security
def test_A02_auth_token_not_exposed_in_redirect_url(vapt_base_url):
    """Authentication tokens must not appear as URL query parameters in redirects."""
    resp = requests.get(f"{vapt_base_url}/login",
                        allow_redirects=True, timeout=10)
    for r in resp.history:
        location = r.headers.get("Location", "").lower()
        assert "token=" not in location and "access_token=" not in location,             f"Auth token exposed in redirect URL: {r.headers.get('Location')}"
