import sys
from pathlib import Path

# Inject paths so OrangeHRM page objects and tests can use unmodified imports:
#   "from pages.web.login_page import LoginPage"  → examples/orangehrm/pages/web/
#   "from pages.base_page import BasePage"         → <framework root>/pages/
_EXAMPLE_ROOT = Path(__file__).resolve().parent
_FRAMEWORK_ROOT = _EXAMPLE_ROOT.parent.parent

for _p in (str(_EXAMPLE_ROOT), str(_FRAMEWORK_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import yaml
import pytest


def _load_config(request) -> dict:
    env = request.config.getoption("--env", default="qa")
    config_file = _EXAMPLE_ROOT / "config" / f"env_{env}.yaml"
    if not config_file.exists():
        raise FileNotFoundError(f"OrangeHRM config not found: {config_file}")
    with config_file.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="session")
def orangehrm_config(request):
    return _load_config(request)


@pytest.fixture(scope="session")
def orangehrm_credentials(orangehrm_config):
    creds = orangehrm_config.get("orangehrm", {}).get("credentials", {})
    return {
        "username": creds.get("admin_username", "Admin"),
        "password": creds.get("admin_password", "admin123"),
    }


@pytest.fixture(scope="session")
def session_authed_page(request, browser, orangehrm_credentials):
    """Session-scoped authenticated Playwright page for OrangeHRM."""
    if not request.config.getoption("--session-login", default=False):
        yield None
        return
    from pages.web.login_page import LoginPage
    ctx = browser.new_context()
    pg = ctx.new_page()
    lp = LoginPage(pg)
    lp.navigate_to_login()
    lp.login(orangehrm_credentials["username"], orangehrm_credentials["password"])
    yield pg
    ctx.close()


@pytest.fixture(scope="session")
def orangehrm_client(browser, session_authed_page, orangehrm_credentials):
    """Session-scoped OrangeHRM API client, reuses web session cookies when available."""
    from pages.web.login_page import LoginPage
    from api.orangehrm_client import OrangeHRMClient

    if session_authed_page is not None:
        client = OrangeHRMClient.from_playwright_cookies(
            session_authed_page.context.cookies()
        )
        yield client
        client.close()
        return

    ctx = browser.new_context()
    pg = ctx.new_page()
    lp = LoginPage(pg)
    lp.navigate_to_login()
    lp.login(orangehrm_credentials["username"], orangehrm_credentials["password"])
    client = OrangeHRMClient.from_playwright_cookies(ctx.cookies())
    yield client
    ctx.close()
    client.close()


@pytest.fixture(scope="session")
def shared_state():
    """Mutable bag for passing IDs/data between dependent tests in a session.

    Use with @pytest.mark.dependency (pytest-depends) to declare ordering.
    Example:
        shared_state["employee_id"] = resp.json()["data"]["empNumber"]
    """
    return {}


@pytest.fixture(scope="function", autouse=True)
def _api_log_reset(request):
    if "orangehrm_client" in request.fixturenames:
        try:
            request.getfixturevalue("orangehrm_client").clear_log()
        except Exception:
            pass
    yield
