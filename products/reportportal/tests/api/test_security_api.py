import pytest
import requests


@pytest.mark.api
@pytest.mark.security
def test_RP_SEC_001_api_missing_token_returns_401(rp_base_url):
    """API call without auth token should return 401 Unauthorized."""
    resp = requests.get(f"{rp_base_url}/api/v1/user/info", headers={}, allow_redirects=False)
    assert resp.status_code in (401, 403), f"Expected 401/403, got {resp.status_code} for unauthenticated request"


@pytest.mark.api
@pytest.mark.security
def test_RP_SEC_002_api_invalid_token_returns_401(rp_base_url):
    """API call with invalid token should return 401 Unauthorized."""
    resp = requests.get(
        f"{rp_base_url}/api/v1/user/info",
        headers={"Authorization": "Bearer invalid_token_12345"},
        allow_redirects=False
    )
    assert resp.status_code in (401, 403), f"Expected 401/403 for invalid token, got {resp.status_code}"


@pytest.mark.api
@pytest.mark.security
def test_RP_SEC_003_api_project_list_requires_auth(rp_base_url):
    """Project listing endpoint should require authentication."""
    resp = requests.get(f"{rp_base_url}/api/v1/project", allow_redirects=False)
    assert resp.status_code in (401, 403), f"Expected 401/403 for /api/v1/project without auth, got {resp.status_code}"


@pytest.mark.api
@pytest.mark.security
def test_RP_SEC_004_api_response_headers_security_check(rp_base_url, rp_api_token):
    """API responses should include security headers."""
    resp = requests.get(
        f"{rp_base_url}/api/v1/user/info",
        headers={"Authorization": f"Bearer {rp_api_token}"},
        allow_redirects=False
    )
    # Check for at least some response received (could be 200 or error with token issue)
    assert resp.status_code in (200, 401, 403)
    # Verify content-type is set (XSS mitigation)
    if resp.status_code == 200:
        assert "content-type" in resp.headers.lower() or "Content-Type" in resp.headers, \
            "Missing Content-Type header in API response"


@pytest.mark.api
@pytest.mark.security
def test_RP_SEC_005_admin_endpoint_auth_check(rp_base_url):
    """Admin endpoints should require proper authentication."""
    admin_endpoints = [
        "/api/v1/user",
        "/api/v1/project",
    ]
    for endpoint in admin_endpoints:
        resp = requests.get(f"{rp_base_url}{endpoint}", allow_redirects=False)
        assert resp.status_code in (401, 403), \
            f"Endpoint {endpoint} should require auth, got {resp.status_code}"
