"""Standard VAPT access control tests — OWASP A01 Broken Access Control."""
import pytest
import requests

_ADMIN_PATHS = [
    "/admin", "/admin/", "/api/admin", "/api/v1/admin",
    "/management", "/actuator", "/actuator/env", "/actuator/heapdump",
    "/.env", "/api/config", "/config",
    "/swagger-ui.html", "/swagger-ui/",
    "/api-docs", "/v2/api-docs", "/v3/api-docs",
    "/metrics", "/health/details",
]

_IDOR_TEMPLATES = [
    "/api/v1/user/{id}",
    "/api/user/{id}",
    "/api/v1/booking/{id}",
    "/api/v1/project/{id}",
]


@pytest.mark.security
def test_A01_admin_paths_require_auth(vapt_base_url):
    """Admin and management paths must not return 200 without authentication."""
    exposed = []
    for path in _ADMIN_PATHS:
        resp = requests.get(f"{vapt_base_url}{path}",
                            allow_redirects=False, timeout=10)
        if resp.status_code == 200:
            exposed.append((path, resp.status_code))
    assert not exposed, f"Admin paths accessible without auth: {exposed}"


@pytest.mark.security
def test_A01_no_directory_listing(vapt_base_url):
    """Static asset directories must not expose directory listings."""
    for path in ["/static/", "/assets/", "/uploads/", "/files/", "/public/"]:
        resp = requests.get(f"{vapt_base_url}{path}",
                            allow_redirects=False, timeout=10)
        if resp.status_code == 200:
            body = resp.text.lower()
            assert "index of" not in body and "directory listing" not in body,                 f"Directory listing exposed at {path}"


@pytest.mark.security
def test_A01_idor_probe_requires_auth(vapt_base_url):
    """Sequential resource ID probing must not return data without authentication."""
    exposed = []
    for tmpl in _IDOR_TEMPLATES:
        for rid in (0, 1, 2, 9999):
            path = tmpl.format(id=rid)
            resp = requests.get(f"{vapt_base_url}{path}",
                                allow_redirects=False, timeout=10)
            if resp.status_code == 200:
                exposed.append(path)
    assert not exposed, f"Resources accessible without auth via IDOR probe: {exposed}"
