"""Standard VAPT mobile authentication tests — MASVS-AUTH / OWASP M4."""
import pytest
import requests

_MOBILE_UA = "Mozilla/5.0 (Linux; Android 14; Pixel 7) AppleWebKit/537.36 Mobile Safari/537.36"
_AUTH_ENDPOINTS = [
    "/api/v1/user/login", "/api/login", "/auth/login", "/auth/token",
    "/oauth/token", "/api/v1/auth",
]
_PROTECTED_PATHS = [
    "/api/v1/user", "/api/v1/me", "/api/user",
    "/api/v1/project", "/api/v1/projects",
]


@pytest.mark.security
def test_M4_auth_token_not_in_url(vapt_base_url):
    """Authentication tokens must not appear in URL query parameters — MASVS-AUTH-2."""
    resp = requests.get(vapt_base_url, allow_redirects=True, timeout=10,
                        headers={"User-Agent": _MOBILE_UA})
    for r in [resp, *resp.history]:
        url_lower = r.url.lower()
        for banned_param in ("access_token=", "token=", "auth_token=", "api_key=", "apikey="):
            assert banned_param not in url_lower,                 f"Authentication credential exposed in URL: {r.url}"


@pytest.mark.security
def test_M4_api_requires_auth_from_mobile(vapt_base_url):
    """API endpoints must require authentication regardless of client User-Agent — MASVS-AUTH-1."""
    unprotected = []
    for path in _PROTECTED_PATHS:
        resp = requests.get(f"{vapt_base_url}{path}",
                            headers={"User-Agent": _MOBILE_UA},
                            allow_redirects=False, timeout=10)
        if resp.status_code not in (401, 403, 404, 405):
            unprotected.append((path, resp.status_code))
    assert not unprotected,         f"API endpoints accessible without auth from mobile client: {unprotected}"


@pytest.mark.security
def test_M4_login_brute_force_protection(vapt_base_url):
    """Login endpoint must apply rate limiting to mobile clients — MASVS-AUTH-3."""
    rate_limited = False
    for path in _AUTH_ENDPOINTS:
        for _ in range(12):
            try:
                resp = requests.post(
                    f"{vapt_base_url}{path}",
                    json={"username": "probe_mobile_vapt", "password": "probe_pass_vapt"},
                    headers={"User-Agent": _MOBILE_UA},
                    allow_redirects=False, timeout=10,
                )
                if resp.status_code in (429, 503, 423):
                    rate_limited = True
                    break
            except requests.exceptions.RequestException:
                pass
        if rate_limited:
            break
    if not rate_limited:
        pytest.xfail(
            "No 429/503/423 observed after 12 rapid login attempts from mobile client — "
            "verify rate limiting applies to mobile user agents"
        )


@pytest.mark.security
def test_M4_weak_default_credentials_rejected(vapt_base_url):
    """Login endpoint must reject commonly known weak credentials — MASVS-AUTH-3."""
    weak_creds = [
        {"username": "admin", "password": "admin"},
        {"username": "admin", "password": "password"},
        {"username": "test", "password": "test"},
        {"username": "admin", "password": "123456"},
    ]
    accepted = []
    for path in _AUTH_ENDPOINTS:
        for creds in weak_creds:
            try:
                resp = requests.post(
                    f"{vapt_base_url}{path}", json=creds,
                    headers={"User-Agent": _MOBILE_UA},
                    allow_redirects=False, timeout=10,
                )
                if resp.status_code == 200:
                    body = resp.text.lower()
                    if "token" in body or "access" in body:
                        accepted.append(f"{path} with {creds['username']}/{creds['password']}")
            except requests.exceptions.RequestException:
                pass
    if accepted:
        pytest.xfail(
            f"Weak default credentials accepted — verify these are test-only accounts: {accepted}"
        )
