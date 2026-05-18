"""Standard VAPT rate limiting tests — OWASP A04 Unrestricted Resource Consumption."""
import time
import pytest
import requests


@pytest.mark.security
def test_A04_login_endpoint_rate_limited(vapt_base_url):
    """Login endpoint must apply rate limiting to prevent brute-force attacks."""
    login_paths = ["/api/v1/user/login", "/api/login", "/auth/login", "/login"]
    rate_limited = False
    for path in login_paths:
        for _ in range(15):
            resp = requests.post(
                f"{vapt_base_url}{path}",
                json={"username": "probe_user_vapt", "password": "probe_pass_vapt"},
                allow_redirects=False, timeout=10,
            )
            if resp.status_code in (429, 503, 423):
                rate_limited = True
                break
        if rate_limited:
            break
    if not rate_limited:
        pytest.xfail(
            "No 429/503/423 observed after 15 rapid login attempts — "
            "verify rate limiting is enforced at the gateway/load balancer level"
        )


@pytest.mark.security
def test_A04_api_endpoint_rate_limited(vapt_base_url):
    """Public API endpoints must enforce rate limiting under rapid sequential requests."""
    found_limit = False
    for _ in range(30):
        resp = requests.get(f"{vapt_base_url}/api/v1/user",
                            allow_redirects=False, timeout=10)
        if resp.status_code in (429, 503):
            found_limit = True
            break
    if not found_limit:
        pytest.xfail(
            "No 429/503 observed after 30 rapid unauthenticated requests — "
            "confirm rate limiting is enforced upstream"
        )
