"""Generate a standard VAPT test suite for any product under products/<product>/tests/vapt/."""
from __future__ import annotations

from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent

# ── generated file contents ───────────────────────────────────────────────────

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

_XSS_PAYLOAD = "<script>alert('xss_vapt_probe')</script>"

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
            pytest.fail(f"SSTI probe {probe!r} appears to have been evaluated — '49' found")
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


# ── generator ─────────────────────────────────────────────────────────────────

class VaptTestGenerator:

    _FILES: list[tuple[str, str]] = [
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

    # Used by the template viewer endpoint to show OWASP context per file
    _FILE_META: dict[str, tuple[str, str]] = {
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

    @classmethod
    def generate(cls, product: str, force: bool = False) -> dict:
        vapt_dir = _ROOT / "products" / product / "tests" / "vapt"
        if vapt_dir.exists() and not force:
            return {
                "status": "skipped",
                "reason": "vapt/ directory already exists — use force=True to regenerate",
                "path": str(vapt_dir),
                "files": cls.test_info(product)["files"],
            }
        vapt_dir.mkdir(parents=True, exist_ok=True)
        written: list[str] = []
        for fname, content in cls._FILES:
            (vapt_dir / fname).write_text(content, encoding="utf-8")
            written.append(fname)
        return {"status": "generated", "path": str(vapt_dir), "files": written}

    @classmethod
    def test_info(cls, product: str) -> dict:
        vapt_dir = _ROOT / "products" / product / "tests" / "vapt"
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
    def template_contents(cls, product: str) -> list[dict]:
        """Return each test file's content with its OWASP metadata for the template viewer."""
        vapt_dir = _ROOT / "products" / product / "tests" / "vapt"
        result = []
        for fname, _content in cls._FILES:
            if not fname.startswith("test_"):
                continue
            owasp_ref, owasp_title = cls._FILE_META.get(fname, ("—", ""))
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
