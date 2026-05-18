"""Generate standard VAPT test suites (web, infra, mobile) for any product."""
from __future__ import annotations

from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent

# ── web app test content (existing) ──────────────────────────────────────────

_CONFTEST = '''\
"""VAPT fixture set — auto-detected from products/<product>/config/env_*.yaml."""
from pathlib import Path
import pytest
import yaml

_PRODUCT_ROOT = Path(__file__).resolve().parent.parent.parent  # products/<product>/


def _load_config() -> dict:
    cfg_dir = _PRODUCT_ROOT / "config"
    for f in sorted(cfg_dir.glob("env_*.yaml")):
        try:
            return yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        except Exception:
            pass
    return {}


def _find(cfg: dict, *keys: str) -> str:
    for section in cfg.values():
        if isinstance(section, dict):
            for k in keys:
                if k in section and section[k]:
                    return str(section[k])
    return ""


@pytest.fixture(scope="session")
def vapt_base_url() -> str:
    return _find(_load_config(), "base_url", "api_url", "url") or "http://localhost:8080"


@pytest.fixture(scope="session")
def vapt_api_token() -> str:
    return _find(_load_config(), "api_token", "token", "api_key", "auth_token")
'''

_AUTH_TESTS = '''\
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
    assert resp.status_code in (400, 401, 403, 404), \
        f"Empty Bearer token accepted with {resp.status_code}"


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
        assert resp.status_code in (400, 401, 403, 404), \
            f"Malformed header \'{header_value}\' returned {resp.status_code}"
'''

_HEADERS_TESTS = '''\
"""Standard VAPT security headers tests — OWASP A05 Security Misconfiguration."""
import pytest
import requests


@pytest.mark.security
def test_A05_response_has_content_type(vapt_base_url):
    """Every HTTP response must include a Content-Type header."""
    resp = requests.get(vapt_base_url, timeout=10, allow_redirects=True)
    assert "content-type" in {h.lower() for h in resp.headers}, \
        "Missing Content-Type header in root response"


@pytest.mark.security
def test_A05_server_header_no_version_disclosure(vapt_base_url):
    """Server header must not disclose software version strings."""
    resp = requests.get(vapt_base_url, timeout=10, allow_redirects=True)
    server = resp.headers.get("Server", "")
    version_tokens = ["Apache/", "nginx/", "Jetty/", "Tomcat/", "Python/", "Microsoft-IIS/"]
    disclosed = [t for t in version_tokens if t in server]
    assert not disclosed, f"Server header discloses version: \'{server}\'"


@pytest.mark.security
def test_A05_x_content_type_options_nosniff(vapt_base_url, vapt_api_token):
    """Authenticated API responses should carry X-Content-Type-Options: nosniff."""
    headers = {}
    if vapt_api_token:
        headers["Authorization"] = f"Bearer {vapt_api_token}"
    resp = requests.get(f"{vapt_base_url}/api/v1/user",
                        headers=headers, timeout=10, allow_redirects=False)
    if resp.status_code == 200:
        val = resp.headers.get("X-Content-Type-Options", "")
        assert "nosniff" in val.lower(), \
            f"Missing X-Content-Type-Options: nosniff on authenticated response (got \'{val}\')"


@pytest.mark.security
def test_A05_error_response_no_stack_trace(vapt_base_url):
    """Error responses must not expose stack traces or internal paths."""
    resp = requests.get(f"{vapt_base_url}/api/vapt_probe_nonexistent_endpoint_xz99",
                        timeout=10, allow_redirects=False)
    body = resp.text.lower()
    leak_signals = [
        "traceback", "stack trace", "exception in", "at line ",
        "syntaxerror", "java.lang.", "org.springframework",
        "errno", "/home/", "/var/www/",
    ]
    found = [s for s in leak_signals if s in body]
    assert not found, f"Error response leaks debug info: {found}"


@pytest.mark.security
def test_A05_cors_wildcard_not_set(vapt_base_url, vapt_api_token):
    """CORS Access-Control-Allow-Origin must not be a blanket wildcard on authenticated endpoints."""
    headers = {"Origin": "https://evil.example.com"}
    if vapt_api_token:
        headers["Authorization"] = f"Bearer {vapt_api_token}"
    resp = requests.get(f"{vapt_base_url}/api/v1/user", headers=headers,
                        allow_redirects=False, timeout=10)
    acao = resp.headers.get("Access-Control-Allow-Origin", "")
    if resp.status_code == 200:
        assert acao != "*", \
            "Access-Control-Allow-Origin: * set on an authenticated endpoint — CORS misconfiguration"
'''

_ACCESS_TESTS = '''\
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
            assert "index of" not in body and "directory listing" not in body, \
                f"Directory listing exposed at {path}"


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
'''

_CRYPTO_TESTS = '''\
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
    assert resp.status_code in (301, 302, 307, 308), \
        f"HTTP does not redirect to HTTPS (got {resp.status_code})"
    location = resp.headers.get("Location", "")
    assert location.startswith("https://"), \
        f"HTTP redirect target is not HTTPS: \'{location}\'"


@pytest.mark.security
def test_A02_hsts_header_present(vapt_base_url, vapt_api_token):
    """HTTPS responses must include a Strict-Transport-Security header."""
    if not vapt_base_url.startswith("https://"):
        pytest.skip("Product not running on HTTPS — HSTS check skipped")
    headers = {}
    if vapt_api_token:
        headers["Authorization"] = f"Bearer {vapt_api_token}"
    resp = requests.get(vapt_base_url, headers=headers, timeout=10, allow_redirects=True)
    assert "strict-transport-security" in {h.lower() for h in resp.headers}, \
        "Missing Strict-Transport-Security (HSTS) header on HTTPS response"


@pytest.mark.security
def test_A02_auth_token_not_exposed_in_redirect_url(vapt_base_url):
    """Authentication tokens must not appear as URL query parameters in redirects."""
    resp = requests.get(f"{vapt_base_url}/login",
                        allow_redirects=True, timeout=10)
    for r in resp.history:
        location = r.headers.get("Location", "").lower()
        assert "token=" not in location and "access_token=" not in location, \
            f"Auth token exposed in redirect URL: {r.headers.get(\'Location\')}"
'''

_RATE_LIMIT_TESTS = '''\
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
'''

_INJECTION_TESTS = '''\
"""Standard VAPT injection tests — OWASP A03 Injection."""
import pytest
import requests

_SQL_PAYLOADS = [
    "' OR '1'='1",
    '" OR 1=1--',
    "1; DROP TABLE users--",
    "1 UNION SELECT null,null--",
]

_XSS_PAYLOAD = "<script>alert(\'xss_vapt_probe\')</script>"

_PATH_TRAVERSAL = [
    "../../../etc/passwd",
    "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
    "....//....//....//etc/passwd",
]

_SSTI_PROBES = ["{{7*7}}", "${7*7}", "#{7*7}", "<%=7*7%>"]


@pytest.mark.security
def test_A03_sql_injection_no_500(vapt_base_url):
    """SQL injection payloads in query params must not cause 500 Internal Server Error."""
    probe_paths = ["/api/v1/user", "/api/v1/project", "/api/v1/booking", "/api/v1/search"]
    for path in probe_paths:
        for payload in _SQL_PAYLOADS:
            resp = requests.get(
                f"{vapt_base_url}{path}",
                params={"id": payload, "name": payload, "q": payload},
                allow_redirects=False, timeout=10,
            )
            assert resp.status_code != 500, \
                f"SQL injection payload caused 500 at {path}?q={payload!r}"


@pytest.mark.security
def test_A03_xss_not_reflected_unescaped(vapt_base_url):
    """XSS payload in query params must not appear unescaped in the response body."""
    resp = requests.get(
        f"{vapt_base_url}/api/v1/user",
        params={"name": _XSS_PAYLOAD, "q": _XSS_PAYLOAD},
        allow_redirects=False, timeout=10,
    )
    assert _XSS_PAYLOAD not in resp.text, \
        f"XSS payload reflected unescaped in response: {resp.text[:300]}"


@pytest.mark.security
def test_A03_path_traversal_blocked(vapt_base_url):
    """Path traversal sequences must not expose filesystem content."""
    for traversal in _PATH_TRAVERSAL:
        resp = requests.get(f"{vapt_base_url}/api/{traversal}",
                            allow_redirects=False, timeout=10)
        # 302/401 are valid blocking responses (auth redirect or auth required)
        assert resp.status_code in (301, 302, 400, 401, 403, 404, 405), \
            f"Path traversal not blocked at /api/{traversal} (got {resp.status_code})"
        assert "root:" not in resp.text, \
            f"Path traversal may have exposed /etc/passwd at /api/{traversal}"


@pytest.mark.security
def test_A03_ssti_probe_not_evaluated(vapt_base_url):
    """Server-side template injection payloads must not be evaluated."""
    for probe in _SSTI_PROBES:
        resp = requests.get(
            f"{vapt_base_url}/api/v1/user",
            params={"name": probe, "q": probe},
            allow_redirects=False, timeout=10,
        )
        # If evaluated, "49" would appear and the raw probe string would not
        if resp.status_code == 200 and "49" in resp.text and probe not in resp.text:
            pytest.fail(f"SSTI probe {probe!r} appears to have been evaluated — \'49\' found")
'''

_SESSION_TESTS = '''\
"""Standard VAPT session management tests — OWASP A07 Session Management."""
import pytest
import requests

_SESSION_KEYWORDS = ("session", "token", "auth", "jwt", "sid", "access")


@pytest.mark.security
def test_A07_session_cookie_httponly_flag(vapt_base_url):
    """Session cookies must have the HttpOnly flag to prevent XSS-based theft."""
    resp = requests.get(vapt_base_url, allow_redirects=True, timeout=10)
    set_cookie_headers = resp.raw.headers.getlist("Set-Cookie") if hasattr(resp.raw.headers, "getlist") \
        else [v for k, v in resp.raw.headers.items() if k.lower() == "set-cookie"]
    for header in set_cookie_headers:
        header_lower = header.lower()
        name = header.split("=")[0].strip().lower()
        if any(kw in name for kw in _SESSION_KEYWORDS):
            assert "httponly" in header_lower, \
                f"Session cookie \'{name}\' is missing the HttpOnly flag: {header}"


@pytest.mark.security
def test_A07_session_token_not_in_url(vapt_base_url):
    """Session tokens must not appear as URL query parameters."""
    resp = requests.get(vapt_base_url, allow_redirects=True, timeout=10)
    for r in [resp, *resp.history]:
        url_lower = r.url.lower()
        for banned in ("sessionid=", "jsessionid=", "phpsessid=", "sid="):
            assert banned not in url_lower, \
                f"Session ID exposed in URL: {r.url}"


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
            assert "secure" in header.lower(), \
                f"Session cookie \'{name}\' missing Secure flag on HTTPS: {header}"


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
'''

_WEB_TESTS = '''\
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
        f"Missing clickjacking protection — X-Frame-Options: \'{xfo}\', "
        f"CSP frame-ancestors: {\'present\' if has_csp_frame else \'absent\'}"
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
            assert not location.startswith("https://evil.example.com"), \
                f"Open redirect via ?{param}= redirects to external host: {location}"


@pytest.mark.security
def test_A05_referrer_policy_header(vapt_base_url):
    """Referrer-Policy header should restrict URL leakage to third parties."""
    resp = requests.get(vapt_base_url, timeout=10, allow_redirects=True)
    policy = resp.headers.get("Referrer-Policy", "")
    if policy:
        assert policy.lower() in _SAFE_REFERRER_POLICIES, \
            f"Referrer-Policy value \'{policy}\' may leak sensitive URLs"
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
        assert not found, \
            f"HTML comment may contain sensitive info ({found}): {comment[:120]!r}"
'''

_SSRF_TESTS = '''\
"""Standard VAPT SSRF tests — OWASP A10 Server-Side Request Forgery."""
import pytest
import requests

_INTERNAL_TARGETS = [
    "http://169.254.169.254/latest/meta-data/",   # AWS IMDS v1
    "http://metadata.google.internal/",            # GCP metadata
    "http://169.254.169.254/",
    "http://127.0.0.1/",
    "http://localhost/",
    "http://[::1]/",
    "http://0.0.0.0/",
]

_URL_PARAM_NAMES = ["url", "webhook", "callback", "redirect", "target", "src", "endpoint", "fetch"]
_FETCH_PATHS = ["/api/v1/webhook", "/api/webhook", "/api/fetch", "/api/v1/fetch", "/api/v1/preview"]


@pytest.mark.security
def test_A10_ssrf_via_url_params_blocked(vapt_base_url):
    """URL-accepting API parameters must not fetch internal or cloud-metadata endpoints."""
    suspicious = []
    for target in _INTERNAL_TARGETS[:3]:
        for param in _URL_PARAM_NAMES:
            for path in _FETCH_PATHS:
                try:
                    resp = requests.post(
                        f"{vapt_base_url}{path}",
                        json={param: target},
                        allow_redirects=False, timeout=5,
                    )
                    if resp.status_code == 200 and any(
                        kw in resp.text.lower()
                        for kw in ("ami-id", "instance-id", "metadata", "computeMetadata")
                    ):
                        suspicious.append((path, param, target))
                except requests.exceptions.RequestException:
                    pass
    assert not suspicious, f"Possible SSRF — internal metadata fetched: {suspicious}"


@pytest.mark.security
def test_A10_ssrf_dns_rebinding_probe(vapt_base_url):
    """URL params must reject or sanitize URLs pointing to RFC-1918 address ranges."""
    private_ranges = [
        "http://10.0.0.1/", "http://192.168.1.1/", "http://172.16.0.1/",
    ]
    for target in private_ranges:
        for param in _URL_PARAM_NAMES:
            for path in _FETCH_PATHS:
                try:
                    resp = requests.post(
                        f"{vapt_base_url}{path}",
                        json={param: target},
                        allow_redirects=False, timeout=5,
                    )
                    if resp.status_code == 200 and len(resp.text) > 100:
                        pytest.xfail(
                            f"Endpoint {path} with {param}={target} returned 200 with content — "
                            "manually verify this is not fetching internal network resources"
                        )
                except requests.exceptions.RequestException:
                    pass
'''

# ── infrastructure test content ───────────────────────────────────────────────

_INFRA_CONFTEST = '''\
"""VAPT infrastructure fixture set — auto-detected from products/<product>/config/env_*.yaml.
VAPT_INFRA_TARGETS env var (comma-separated) overrides the host list when set by the scan runner.
"""
import os
import re
from pathlib import Path
import pytest
import yaml

_PRODUCT_ROOT = Path(__file__).resolve().parent.parent.parent


def _load_config() -> dict:
    cfg_dir = _PRODUCT_ROOT / "config"
    for f in sorted(cfg_dir.glob("env_*.yaml")):
        try:
            return yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        except Exception:
            pass
    return {}


def _find(cfg: dict, *keys: str) -> str:
    for section in cfg.values():
        if isinstance(section, dict):
            for k in keys:
                if k in section and section[k]:
                    return str(section[k])
    return ""


@pytest.fixture(scope="session")
def vapt_base_url() -> str:
    return _find(_load_config(), "base_url", "api_url", "url") or "http://localhost:8080"


@pytest.fixture(scope="session")
def vapt_infra_targets(vapt_base_url) -> "list[str]":
    raw = os.environ.get("VAPT_INFRA_TARGETS", "").strip()
    if raw:
        return [t.strip() for t in raw.split(",") if t.strip()]
    m = re.match(r"https?://([^/:]+)", vapt_base_url)
    return [m.group(1) if m else "localhost"]


@pytest.fixture(scope="session")
def vapt_host(vapt_infra_targets) -> str:
    return vapt_infra_targets[0] if vapt_infra_targets else "localhost"


@pytest.fixture(scope="session")
def vapt_https_port(vapt_base_url) -> "int | None":
    if vapt_base_url.startswith("https://"):
        m = re.match(r"https://[^/:]+:(\d+)", vapt_base_url)
        return int(m.group(1)) if m else 443
    return None


@pytest.fixture(scope="session")
def vapt_domain(vapt_host) -> str:
    if re.match(r"^\d+\\.\\d+\\.\\d+\\.\\d+$", vapt_host) or vapt_host in ("localhost", "127.0.0.1", "::1"):
        return ""
    return vapt_host
'''

_INFRA_PORTS_TESTS = '''\
"""Standard VAPT infrastructure port exposure tests."""
import socket
import pytest

_SENSITIVE_PORTS = [
    (21, "FTP"), (23, "Telnet"), (25, "SMTP"),
    (111, "RPC"), (512, "rexec"), (513, "rlogin"), (514, "rsh"),
    (1433, "MSSQL"), (1521, "Oracle DB"),
    (3306, "MySQL"), (5432, "PostgreSQL"),
    (6379, "Redis"), (11211, "Memcached"),
    (27017, "MongoDB"), (9200, "Elasticsearch"), (9300, "Elasticsearch cluster"),
    (5601, "Kibana"), (2375, "Docker daemon (unencrypted)"),
    (2379, "etcd"), (2380, "etcd peer"),
    (8500, "Consul"), (8161, "ActiveMQ console"),
    (4848, "GlassFish admin"), (9090, "Prometheus"),
]


@pytest.mark.security
def test_INFRA_sensitive_service_ports_not_exposed(vapt_host):
    """Sensitive service ports must not be reachable from the test network — indicates firewall gaps."""
    exposed = []
    for port, name in _SENSITIVE_PORTS:
        try:
            with socket.create_connection((vapt_host, port), timeout=2):
                exposed.append(f"{port}/{name}")
        except (socket.timeout, ConnectionRefusedError, OSError):
            pass
    if exposed:
        pytest.xfail(
            f"Service ports reachable from test network — verify firewall rules: {exposed}. "
            "These should only be accessible from trusted internal networks."
        )


@pytest.mark.security
def test_INFRA_ssh_port_not_on_default(vapt_host):
    """SSH on default port 22 increases automated attack surface — consider moving to a non-standard port."""
    try:
        with socket.create_connection((vapt_host, 22), timeout=2) as sock:
            banner = sock.recv(256).decode(errors="replace")
            if "SSH" in banner.upper():
                pytest.xfail(
                    f"SSH running on default port 22 at {vapt_host}. "
                    "Moving SSH to a non-standard port reduces automated brute-force attempts."
                )
    except (socket.timeout, ConnectionRefusedError, OSError):
        pass


@pytest.mark.security
def test_INFRA_no_telnet_service(vapt_host):
    """Telnet (port 23) must not be running — transmits credentials in cleartext."""
    try:
        with socket.create_connection((vapt_host, 23), timeout=2):
            pytest.fail(f"Telnet service detected on {vapt_host}:23 — replace with SSH immediately")
    except (socket.timeout, ConnectionRefusedError, OSError):
        pass


@pytest.mark.security
def test_INFRA_no_ftp_service(vapt_host):
    """FTP (port 21) must not be running — transmits credentials in cleartext; use SFTP instead."""
    try:
        with socket.create_connection((vapt_host, 21), timeout=2) as sock:
            banner = sock.recv(256).decode(errors="replace")
            if "FTP" in banner.upper() or "220" in banner:
                pytest.fail(
                    f"FTP service detected on {vapt_host}:21 — replace with SFTP (SSH port 22) "
                    "or FTPS; FTP transmits credentials in cleartext"
                )
    except (socket.timeout, ConnectionRefusedError, OSError):
        pass
'''

_INFRA_TLS_TESTS = '''\
"""Standard VAPT TLS/SSL security tests — infrastructure layer."""
import ssl
import socket
import datetime
import pytest


@pytest.mark.security
def test_INFRA_tls_1_0_disabled(vapt_host, vapt_https_port):
    """TLS 1.0 must be disabled — deprecated protocol with POODLE and BEAST vulnerability exposure."""
    if not vapt_https_port:
        pytest.skip("Host not running on HTTPS — TLS version check skipped")
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        ctx.maximum_version = ssl.TLSVersion.TLSv1
        with socket.create_connection((vapt_host, vapt_https_port), timeout=5) as sock:
            try:
                ctx.wrap_socket(sock, server_hostname=vapt_host)
                pytest.fail(
                    f"TLS 1.0 accepted by {vapt_host}:{vapt_https_port} — "
                    "must be disabled (CVE: POODLE, BEAST)"
                )
            except ssl.SSLError:
                pass
    except (AttributeError, OSError, socket.timeout):
        pytest.skip("SSL context version limiting not supported on this Python build")


@pytest.mark.security
def test_INFRA_tls_1_1_disabled(vapt_host, vapt_https_port):
    """TLS 1.1 must be disabled — deprecated since RFC 8996 (2021)."""
    if not vapt_https_port:
        pytest.skip("Host not running on HTTPS — TLS version check skipped")
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        ctx.maximum_version = ssl.TLSVersion.TLSv1_1
        with socket.create_connection((vapt_host, vapt_https_port), timeout=5) as sock:
            try:
                ctx.wrap_socket(sock, server_hostname=vapt_host)
                pytest.fail(
                    f"TLS 1.1 accepted by {vapt_host}:{vapt_https_port} — "
                    "must be disabled per RFC 8996"
                )
            except ssl.SSLError:
                pass
    except (AttributeError, OSError, socket.timeout):
        pytest.skip("SSL context version limiting not supported on this Python build")


@pytest.mark.security
def test_INFRA_certificate_not_expired(vapt_host, vapt_https_port):
    """TLS certificate must not be expired."""
    if not vapt_https_port:
        pytest.skip("Host not running on HTTPS — certificate check skipped")
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((vapt_host, vapt_https_port), timeout=5) as raw:
            with ctx.wrap_socket(raw, server_hostname=vapt_host) as ssock:
                cert = ssock.getpeercert()
        expire_str = cert.get("notAfter", "")
        if expire_str:
            expire = datetime.datetime.strptime(expire_str, "%b %d %H:%M:%S %Y %Z")
            days_left = (expire - datetime.datetime.utcnow()).days
            assert days_left > 0, \
                f"TLS certificate expired {abs(days_left)} days ago (expired: {expire_str})"
            if days_left < 30:
                pytest.xfail(
                    f"TLS certificate expires in {days_left} days — renew before expiry"
                )
    except ssl.SSLCertVerificationError as e:
        pytest.fail(f"TLS certificate verification failed: {e}")
    except (socket.timeout, ConnectionRefusedError, OSError) as e:
        pytest.skip(f"Could not connect to {vapt_host}:{vapt_https_port} — {e}")


@pytest.mark.security
def test_INFRA_certificate_hostname_match(vapt_host, vapt_https_port):
    """TLS certificate Common Name or SAN must match the server hostname."""
    if not vapt_https_port:
        pytest.skip("Host not running on HTTPS — hostname verification skipped")
    ctx = ssl.create_default_context()
    try:
        with socket.create_connection((vapt_host, vapt_https_port), timeout=5) as raw:
            with ctx.wrap_socket(raw, server_hostname=vapt_host):
                pass
    except ssl.SSLCertVerificationError as e:
        if "hostname" in str(e).lower() or "mismatch" in str(e).lower():
            pytest.fail(f"Certificate hostname mismatch for {vapt_host}: {e}")
        pytest.xfail(
            f"Certificate verification error (may be self-signed in non-prod): {e}"
        )
    except (socket.timeout, ConnectionRefusedError, OSError) as e:
        pytest.skip(f"Could not connect to {vapt_host}:{vapt_https_port} — {e}")
'''

_INFRA_SERVICES_TESTS = '''\
"""Standard VAPT service exposure tests — default pages, version disclosure, debug endpoints."""
import re
import pytest
import requests

_DEBUG_PATHS = [
    "/actuator", "/actuator/env", "/actuator/beans", "/actuator/heapdump",
    "/actuator/metrics", "/actuator/mappings",
    "/debug", "/_debug", "/console",
    "/.git/config", "/.git/HEAD", "/.env", "/.env.local", "/.env.production",
    "/config.json", "/config.yaml", "/application.properties", "/application.yml",
    "/phpinfo.php", "/server-status", "/server-info",
    "/wp-admin", "/phpmyadmin", "/adminer.php",
]

_BACKUP_EXTENSIONS = [
    "/index.php.bak", "/index.bak", "/web.config.bak",
    "/database.sql", "/backup.sql", "/dump.sql",
    "/backup.zip", "/site.tar.gz",
]

_DEFAULT_PAGES = [
    "it works!", "apache2 ubuntu default page", "apache http server test page",
    "welcome to nginx", "nginx is successfully installed",
    "internet information services", "welcome to iis",
    "test page for the apache http server",
    "congratulations: your new web server is installed",
]


@pytest.mark.security
def test_INFRA_no_default_server_page(vapt_base_url):
    """Server must not return default installation pages indicating unconfigured deployment."""
    resp = requests.get(vapt_base_url, timeout=10, allow_redirects=True)
    if "text/html" not in resp.headers.get("Content-Type", ""):
        pytest.skip("Root endpoint does not return HTML")
    body = resp.text.lower()
    found = [p for p in _DEFAULT_PAGES if p in body]
    assert not found, f"Default server installation page detected: {found}"


@pytest.mark.security
def test_INFRA_version_disclosure_in_headers(vapt_base_url):
    """Server, X-Powered-By, and framework headers must not disclose version strings."""
    resp = requests.get(vapt_base_url, timeout=10, allow_redirects=True)
    version_re = re.compile(r"/\d+[\.\d]+")
    candidates = {
        "Server": resp.headers.get("Server", ""),
        "X-Powered-By": resp.headers.get("X-Powered-By", ""),
        "X-AspNet-Version": resp.headers.get("X-AspNet-Version", ""),
        "X-Runtime": resp.headers.get("X-Runtime", ""),
        "X-Generator": resp.headers.get("X-Generator", ""),
    }
    disclosed = {k: v for k, v in candidates.items() if v and version_re.search(v)}
    assert not disclosed, f"Version strings disclosed in HTTP headers: {disclosed}"


@pytest.mark.security
def test_INFRA_debug_endpoints_blocked(vapt_base_url):
    """Debug, admin console, and internal endpoints must not return 200 without authentication."""
    exposed = []
    for path in _DEBUG_PATHS:
        try:
            resp = requests.get(f"{vapt_base_url}{path}", allow_redirects=False, timeout=5)
            if resp.status_code == 200:
                exposed.append(f"{path} ({resp.status_code})")
        except requests.exceptions.RequestException:
            pass
    assert not exposed, f"Debug/admin endpoints accessible without authentication: {exposed}"


@pytest.mark.security
def test_INFRA_backup_files_not_exposed(vapt_base_url):
    """Backup and configuration archive files must not be directly downloadable."""
    exposed = []
    for path in _BACKUP_EXTENSIONS:
        try:
            resp = requests.get(f"{vapt_base_url}{path}", allow_redirects=False, timeout=5)
            if resp.status_code == 200 and len(resp.content) > 0:
                exposed.append(path)
        except requests.exceptions.RequestException:
            pass
    assert not exposed, f"Backup/config files are publicly accessible: {exposed}"
'''

_INFRA_DNS_TESTS = '''\
"""Standard VAPT DNS security tests — SPF, DMARC, zone transfer."""
import socket
import pytest
import requests


@pytest.mark.security
def test_INFRA_spf_record_configured(vapt_domain):
    """SPF TXT record must be configured to prevent email spoofing on the domain."""
    if not vapt_domain:
        pytest.skip("IP address or localhost — DNS record checks skipped")
    try:
        resp = requests.get(
            "https://dns.google/resolve",
            params={"name": vapt_domain, "type": "TXT"},
            timeout=10,
        )
        answers = resp.json().get("Answer", [])
        spf_found = any("v=spf1" in (a.get("data", "") or "") for a in answers)
    except Exception as e:
        pytest.skip(f"DNS-over-HTTPS query failed — {e}")
        return
    if not spf_found:
        pytest.xfail(
            f"No SPF TXT record found for {vapt_domain} — "
            "add \'v=spf1 ... ~all\' to prevent email spoofing"
        )


@pytest.mark.security
def test_INFRA_dmarc_record_configured(vapt_domain):
    """DMARC TXT record must be configured at _dmarc.<domain>."""
    if not vapt_domain:
        pytest.skip("IP address or localhost — DNS record checks skipped")
    dmarc_name = f"_dmarc.{vapt_domain}"
    try:
        resp = requests.get(
            "https://dns.google/resolve",
            params={"name": dmarc_name, "type": "TXT"},
            timeout=10,
        )
        answers = resp.json().get("Answer", [])
        dmarc_found = any("v=DMARC1" in (a.get("data", "") or "") for a in answers)
    except Exception as e:
        pytest.skip(f"DNS-over-HTTPS query failed — {e}")
        return
    if not dmarc_found:
        pytest.xfail(
            f"No DMARC record at {dmarc_name} — "
            "add \'v=DMARC1; p=quarantine; rua=mailto:...\' to enforce email authentication"
        )


@pytest.mark.security
def test_INFRA_zone_transfer_blocked(vapt_host, vapt_domain):
    """DNS zone transfers must be disabled to prevent domain enumeration."""
    if not vapt_domain:
        pytest.skip("IP address or localhost — zone transfer check skipped")
    try:
        with socket.create_connection((vapt_host, 53), timeout=2):
            pass
    except (socket.timeout, ConnectionRefusedError, OSError):
        pytest.skip(f"Port 53 not open on {vapt_host} — not acting as DNS server")
        return
    pytest.xfail(
        f"DNS port 53 is open on {vapt_host} — verify zone transfers (AXFR) are restricted "
        "to authorized secondary nameservers only"
    )
'''

# ── mobile test content ───────────────────────────────────────────────────────

_MOBILE_CONFTEST = '''\
"""VAPT mobile security fixture set — auto-detected from products/<product>/config/env_*.yaml."""
import re
from pathlib import Path
import pytest
import yaml

_PRODUCT_ROOT = Path(__file__).resolve().parent.parent.parent


def _load_config() -> dict:
    cfg_dir = _PRODUCT_ROOT / "config"
    for f in sorted(cfg_dir.glob("env_*.yaml")):
        try:
            return yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        except Exception:
            pass
    return {}


def _find(cfg: dict, *keys: str) -> str:
    for section in cfg.values():
        if isinstance(section, dict):
            for k in keys:
                if k in section and section[k]:
                    return str(section[k])
    return ""


@pytest.fixture(scope="session")
def vapt_base_url() -> str:
    return _find(_load_config(), "base_url", "api_url", "url") or "http://localhost:8080"


@pytest.fixture(scope="session")
def vapt_api_token() -> str:
    return _find(_load_config(), "api_token", "token", "api_key", "auth_token")


@pytest.fixture(scope="session")
def vapt_host(vapt_base_url) -> str:
    m = re.match(r"https?://([^/:]+)", vapt_base_url)
    return m.group(1) if m else "localhost"


@pytest.fixture(scope="session")
def vapt_https_port(vapt_base_url) -> "int | None":
    if vapt_base_url.startswith("https://"):
        m = re.match(r"https://[^/:]+:(\d+)", vapt_base_url)
        return int(m.group(1)) if m else 443
    return None
'''

_MOBILE_NETWORK_TESTS = '''\
"""Standard VAPT mobile network security tests — MASVS-NETWORK / OWASP M3."""
import ssl
import socket
import pytest
import requests

_MOBILE_UA = "Mozilla/5.0 (Linux; Android 14; Pixel 7) AppleWebKit/537.36 Mobile Safari/537.36"


@pytest.mark.security
def test_M3_https_enforced_for_mobile(vapt_base_url):
    """Mobile clients must communicate exclusively over HTTPS — cleartext HTTP must redirect to HTTPS."""
    if not vapt_base_url.startswith("https://"):
        pytest.skip("Product not running on HTTPS — cleartext enforcement check skipped")
    http_url = vapt_base_url.replace("https://", "http://", 1)
    try:
        resp = requests.get(http_url, allow_redirects=False, timeout=10,
                            headers={"User-Agent": _MOBILE_UA})
        assert resp.status_code in (301, 302, 307, 308), \
            f"HTTP not redirected to HTTPS for mobile client (got {resp.status_code})"
        location = resp.headers.get("Location", "")
        assert location.startswith("https://"), \
            f"HTTP redirect target is not HTTPS: \'{location}\'"
    except requests.exceptions.ConnectionError:
        pass  # Connection refused on HTTP — acceptable hardening


@pytest.mark.security
def test_M3_tls_minimum_version_1_2(vapt_host, vapt_https_port):
    """Mobile backend must require TLS 1.2 minimum — MASVS-NETWORK-1."""
    if not vapt_https_port:
        pytest.skip("Host not running on HTTPS — TLS version check skipped")
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        ctx.maximum_version = ssl.TLSVersion.TLSv1
        with socket.create_connection((vapt_host, vapt_https_port), timeout=5) as sock:
            try:
                ctx.wrap_socket(sock, server_hostname=vapt_host)
                pytest.fail(
                    "TLS 1.0 accepted — mobile apps require minimum TLS 1.2 per MASVS-NETWORK-1"
                )
            except ssl.SSLError:
                pass
    except (AttributeError, OSError, socket.timeout):
        pytest.skip("SSL context version limiting not supported on this Python build")


@pytest.mark.security
def test_M3_hsts_header_enforced(vapt_base_url, vapt_api_token):
    """HTTPS responses must include HSTS to prevent SSL stripping attacks on mobile — MASVS-NETWORK-1."""
    if not vapt_base_url.startswith("https://"):
        pytest.skip("Not running on HTTPS — HSTS check skipped")
    headers = {"User-Agent": _MOBILE_UA}
    if vapt_api_token:
        headers["Authorization"] = f"Bearer {vapt_api_token}"
    resp = requests.get(vapt_base_url, headers=headers, timeout=10, allow_redirects=True)
    assert "strict-transport-security" in {h.lower() for h in resp.headers}, \
        "Missing Strict-Transport-Security header — mobile clients vulnerable to SSL stripping"


@pytest.mark.security
def test_M3_api_certificate_trusted(vapt_host, vapt_https_port):
    """Mobile backend certificate must be CA-signed — self-signed certs weaken certificate pinning."""
    if not vapt_https_port:
        pytest.skip("Host not running on HTTPS — certificate trust check skipped")
    ctx = ssl.create_default_context()
    try:
        with socket.create_connection((vapt_host, vapt_https_port), timeout=5) as raw:
            with ctx.wrap_socket(raw, server_hostname=vapt_host):
                pass
    except ssl.SSLCertVerificationError as e:
        pytest.xfail(
            f"Certificate not trusted by default CAs: {e} — "
            "mobile apps should use CA-signed certificates; self-signed certs weaken pinning"
        )
    except (socket.timeout, ConnectionRefusedError, OSError) as e:
        pytest.skip(f"Could not connect to {vapt_host}:{vapt_https_port} — {e}")
'''

_MOBILE_AUTH_TESTS = '''\
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
            assert banned_param not in url_lower, \
                f"Authentication credential exposed in URL: {r.url}"


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
    assert not unprotected, \
        f"API endpoints accessible without auth from mobile client: {unprotected}"


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
                        accepted.append(f"{path} with {creds[\'username\']}/{creds[\'password\']}")
            except requests.exceptions.RequestException:
                pass
    if accepted:
        pytest.xfail(
            f"Weak default credentials accepted — verify these are test-only accounts: {accepted}"
        )
'''

_MOBILE_API_TESTS = '''\
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
        assert acao != "*", \
            "Access-Control-Allow-Origin: * on authenticated endpoint — CORS misconfiguration affects mobile clients"


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
    assert resp.status_code not in (200, 204), \
        f"HTTP method override header accepted ({resp.status_code}) — verify method restriction enforcement"


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
'''

_MOBILE_STORAGE_TESTS = '''\
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
                f"mobile clients may persist sensitive data: Cache-Control: \'{cc}\'"
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
                assert "vapt_probe_pass_m2" not in resp.text, \
                    f"Login endpoint at {path} echoes back the submitted password — must never return passwords"
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
            assert "httponly" in header_lower, \
                f"Mobile session cookie \'{name}\' missing HttpOnly flag: {header}"
            if vapt_base_url.startswith("https://"):
                assert "secure" in header_lower, \
                    f"Mobile session cookie \'{name}\' missing Secure flag on HTTPS: {header}"


@pytest.mark.security
def test_M2_no_sensitive_data_in_url_params(vapt_base_url):
    """Sensitive fields must not appear as URL query parameters — MASVS-STORAGE-4."""
    resp = requests.get(vapt_base_url, allow_redirects=True, timeout=10,
                        headers={"User-Agent": _MOBILE_UA})
    for r in [resp, *resp.history]:
        url_lower = r.url.lower()
        sensitive_params = ("password=", "passwd=", "secret=", "credit_card=", "ssn=", "pin=")
        for param in sensitive_params:
            assert param not in url_lower, \
                f"Sensitive field \'{param.rstrip(\'=\')}\' exposed in URL: {r.url}"
'''

# ── generator class ───────────────────────────────────────────────────────────

class VaptTestGenerator:

    _FILES_WEB: list[tuple[str, str]] = [
        ("__init__.py", ""),
        ("conftest.py", _CONFTEST),
        ("test_vapt_auth.py", _AUTH_TESTS),
        ("test_vapt_session.py", _SESSION_TESTS),
        ("test_vapt_headers.py", _HEADERS_TESTS),
        ("test_vapt_web.py", _WEB_TESTS),
        ("test_vapt_access_control.py", _ACCESS_TESTS),
        ("test_vapt_injection.py", _INJECTION_TESTS),
        ("test_vapt_crypto.py", _CRYPTO_TESTS),
        ("test_vapt_rate_limiting.py", _RATE_LIMIT_TESTS),
        ("test_vapt_ssrf.py", _SSRF_TESTS),
    ]

    _FILES_INFRA: list[tuple[str, str]] = [
        ("__init__.py", ""),
        ("conftest.py", _INFRA_CONFTEST),
        ("test_vapt_infra_ports.py", _INFRA_PORTS_TESTS),
        ("test_vapt_infra_tls.py", _INFRA_TLS_TESTS),
        ("test_vapt_infra_services.py", _INFRA_SERVICES_TESTS),
        ("test_vapt_infra_dns.py", _INFRA_DNS_TESTS),
    ]

    _FILES_MOBILE: list[tuple[str, str]] = [
        ("__init__.py", ""),
        ("conftest.py", _MOBILE_CONFTEST),
        ("test_vapt_mobile_network.py", _MOBILE_NETWORK_TESTS),
        ("test_vapt_mobile_auth.py", _MOBILE_AUTH_TESTS),
        ("test_vapt_mobile_api.py", _MOBILE_API_TESTS),
        ("test_vapt_mobile_storage.py", _MOBILE_STORAGE_TESTS),
    ]

    # Backward-compat alias used by older call sites
    _FILES = _FILES_WEB

    _SUBDIRS: dict[str, str] = {
        "web": "vapt",
        "infra": "vapt_infra",
        "mobile": "vapt_mobile",
    }

    _FILE_META_WEB: dict[str, tuple[str, str]] = {
        "test_vapt_auth.py":           ("A07", "Identification and Authentication Failures"),
        "test_vapt_session.py":        ("A07", "Session Management"),
        "test_vapt_headers.py":        ("A05", "Security Misconfiguration — HTTP Headers"),
        "test_vapt_web.py":            ("A01/A05", "Web Layer — Clickjacking, Open Redirect"),
        "test_vapt_access_control.py": ("A01", "Broken Access Control"),
        "test_vapt_injection.py":      ("A03", "Injection — SQL, XSS, Path Traversal, SSTI"),
        "test_vapt_crypto.py":         ("A02", "Cryptographic Failures — TLS, HTTPS, HSTS"),
        "test_vapt_rate_limiting.py":  ("A04", "Unrestricted Resource Consumption"),
        "test_vapt_ssrf.py":           ("A10", "Server-Side Request Forgery"),
    }

    _FILE_META_INFRA: dict[str, tuple[str, str]] = {
        "test_vapt_infra_ports.py":    ("INFRA", "Exposed Service Ports — Firewall Gaps"),
        "test_vapt_infra_tls.py":      ("A02", "TLS/SSL Version and Certificate Security"),
        "test_vapt_infra_services.py": ("A05", "Service Misconfiguration — Default Pages, Version Disclosure"),
        "test_vapt_infra_dns.py":      ("A05", "DNS Security — SPF, DMARC, Zone Transfer"),
    }

    _FILE_META_MOBILE: dict[str, tuple[str, str]] = {
        "test_vapt_mobile_network.py": ("M3", "MASVS-NETWORK — TLS, HTTPS Enforcement, HSTS"),
        "test_vapt_mobile_auth.py":    ("M4", "MASVS-AUTH — Authentication, Rate Limiting"),
        "test_vapt_mobile_api.py":     ("M1/M6", "MASVS-PLATFORM — API Security, Method Override"),
        "test_vapt_mobile_storage.py": ("M2", "MASVS-STORAGE — Cache, Cookie Flags, Sensitive Data"),
    }

    # Backward-compat alias
    _FILE_META = _FILE_META_WEB

    @classmethod
    def _files_for(cls, scan_type: str) -> list[tuple[str, str]]:
        return {
            "web": cls._FILES_WEB,
            "infra": cls._FILES_INFRA,
            "mobile": cls._FILES_MOBILE,
        }.get(scan_type, cls._FILES_WEB)

    @classmethod
    def _meta_for(cls, scan_type: str) -> dict[str, tuple[str, str]]:
        return {
            "web": cls._FILE_META_WEB,
            "infra": cls._FILE_META_INFRA,
            "mobile": cls._FILE_META_MOBILE,
        }.get(scan_type, cls._FILE_META_WEB)

    @classmethod
    def generate(cls, product: str, scan_type: str = "web", force: bool = False) -> dict:
        subdir = cls._SUBDIRS.get(scan_type, "vapt")
        vapt_dir = _ROOT / "products" / product / "tests" / subdir
        files = cls._files_for(scan_type)
        if vapt_dir.exists() and not force:
            return {
                "status": "skipped",
                "reason": f"{subdir}/ directory already exists — use force=True to regenerate",
                "path": str(vapt_dir),
                "files": cls.test_info(product, scan_type)["files"],
            }
        vapt_dir.mkdir(parents=True, exist_ok=True)
        written: list[str] = []
        for fname, content in files:
            (vapt_dir / fname).write_text(content, encoding="utf-8")
            written.append(fname)
        return {"status": "generated", "path": str(vapt_dir), "files": written}

    @classmethod
    def test_info(cls, product: str, scan_type: str = "web") -> dict:
        subdir = cls._SUBDIRS.get(scan_type, "vapt")
        vapt_dir = _ROOT / "products" / product / "tests" / subdir
        if not vapt_dir.exists():
            return {"exists": False, "files": [], "test_count": 0}
        test_files = sorted(f.name for f in vapt_dir.glob("test_*.py"))
        test_count = sum(
            1 for f in vapt_dir.glob("test_*.py")
            for line in f.read_text(encoding="utf-8").splitlines()
            if line.strip().startswith("def test_")
        )
        return {"exists": True, "files": test_files, "test_count": test_count}

    @classmethod
    def all_test_info(cls, product: str) -> dict[str, dict]:
        """Return test_info for all three scan types in a single call."""
        return {st: cls.test_info(product, st) for st in ("web", "infra", "mobile")}

    @classmethod
    def template_contents(cls, product: str, scan_type: str = "web") -> list[dict]:
        """Return each test file's content with OWASP/MASVS metadata for the template viewer."""
        subdir = cls._SUBDIRS.get(scan_type, "vapt")
        vapt_dir = _ROOT / "products" / product / "tests" / subdir
        files = cls._files_for(scan_type)
        meta = cls._meta_for(scan_type)
        result = []
        for fname, _content in files:
            if not fname.startswith("test_"):
                continue
            owasp_ref, owasp_title = meta.get(fname, ("—", ""))
            path = vapt_dir / fname
            content = path.read_text(encoding="utf-8") if path.exists() else _content
            test_count = sum(1 for l in content.splitlines() if l.strip().startswith("def test_"))
            result.append({
                "filename": fname,
                "owasp_ref": owasp_ref,
                "owasp_title": owasp_title,
                "test_count": test_count,
                "content": content,
            })
        return result
