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
