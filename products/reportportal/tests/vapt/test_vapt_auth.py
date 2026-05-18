"""Standard VAPT auth enforcement tests — OWASP A07 Identification and Authentication Failures."""
import pytest
import requests

_PROBE_PATHS = [
    "/api/v1/user", "/api/user", "/api/users",
    "/api/v1/admin", "/api/admin",
    "/api/v1/project", "/api/v1/projects",
    "/api/me", "/api/v1/me",
    "/api/v1/user/info",
]


@pytest.mark.security
def test_A07_api_without_auth_returns_401(vapt_base_url):
    """Unauthenticated requests to API endpoints must return 401 or 403."""
    unprotected = []
    for path in _PROBE_PATHS:
        resp = requests.get(f"{vapt_base_url}{path}", allow_redirects=False, timeout=10)
        if resp.status_code not in (401, 403, 404, 405):
            unprotected.append((path, resp.status_code))
    assert not unprotected, f"Endpoints accessible without auth: {unprotected}"


@pytest.mark.security
def test_A07_invalid_bearer_token_returns_401(vapt_base_url):
    """A syntactically valid but unknown Bearer token must be rejected with 401 or 403."""
    headers = {"Authorization": "Bearer invalid_vapt_probe_token_abc123xyz"}
    unprotected = []
    for path in _PROBE_PATHS:
        resp = requests.get(f"{vapt_base_url}{path}", headers=headers,
                            allow_redirects=False, timeout=10)
        if resp.status_code not in (401, 403, 404, 405):
            unprotected.append((path, resp.status_code))
    assert not unprotected, f"Endpoints accepted invalid token: {unprotected}"


@pytest.mark.security
def test_A07_empty_bearer_token_returns_401(vapt_base_url):
    """An empty Bearer value must be rejected."""
    resp = requests.get(f"{vapt_base_url}/api/v1/user",
                        headers={"Authorization": "Bearer "},
                        allow_redirects=False, timeout=10)
    assert resp.status_code in (400, 401, 403, 404),         f"Empty Bearer token accepted with {resp.status_code}"


@pytest.mark.security
def test_A07_malformed_auth_header_returns_401(vapt_base_url):
    """Malformed Authorization header variants must all be rejected."""
    bad_headers = [
        "Token badtoken",
        "Basic " + "x" * 100,
        "Bearer",
        "null",
        "undefined",
    ]
    for header_value in bad_headers:
        resp = requests.get(f"{vapt_base_url}/api/v1/user",
                            headers={"Authorization": header_value},
                            allow_redirects=False, timeout=10)
        assert resp.status_code in (400, 401, 403, 404),             f"Malformed header '{header_value}' returned {resp.status_code}"
