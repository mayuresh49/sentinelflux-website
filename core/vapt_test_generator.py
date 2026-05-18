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


# ── generator ─────────────────────────────────────────────────────────────────

class VaptTestGenerator:

    _FILES: list[tuple[str, str]] = [
        ("__init__.py", ""),
        ("conftest.py", _CONFTEST),
        ("test_vapt_auth.py", _AUTH_TESTS),
        ("test_vapt_headers.py", _HEADERS_TESTS),
        ("test_vapt_access_control.py", _ACCESS_TESTS),
        ("test_vapt_crypto.py", _CRYPTO_TESTS),
        ("test_vapt_rate_limiting.py", _RATE_LIMIT_TESTS),
    ]

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
