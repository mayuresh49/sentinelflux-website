import sys
from pathlib import Path

_EXAMPLE_ROOT = Path(__file__).resolve().parent
_FRAMEWORK_ROOT = _EXAMPLE_ROOT.parent.parent

for _p in (str(_EXAMPLE_ROOT), str(_FRAMEWORK_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import pytest  # noqa: E402
import yaml  # noqa: E402


def _load_config(request) -> dict:
    env = request.config.getoption("--env", default="qa")
    config_file = _EXAMPLE_ROOT / "config" / f"env_{env}.yaml"
    if not config_file.exists():
        raise FileNotFoundError(f"Config not found: {config_file}")
    with config_file.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="session")
def rb_config(request):
    return _load_config(request)


@pytest.fixture(scope="session")
def rb_credentials(rb_config):
    """API auth credentials (password123)."""
    creds = rb_config.get("restfulbooker", {}).get("credentials", {})
    return {
        "username": creds.get("username", "admin"),
        "password": creds.get("password", "password123"),
    }


@pytest.fixture(scope="session")
def rb_web_credentials(rb_config):
    """Web admin UI credentials (password)."""
    creds = rb_config.get("restfulbooker", {}).get("web_credentials", {})
    return {
        "username": creds.get("username", "admin"),
        "password": creds.get("password", "password"),
    }


@pytest.fixture(scope="session")
def rb_api_base(rb_config):
    return rb_config.get("restfulbooker", {}).get("api_base_url", "https://restful-booker.herokuapp.com")


@pytest.fixture(scope="session")
def rb_web_base(rb_config):
    return rb_config.get("restfulbooker", {}).get("web_base_url", "https://automationintesting.online")


@pytest.fixture(scope="session")
def booking_client(rb_api_base, rb_credentials):
    from booking_client import BookingClient
    client = BookingClient(rb_api_base, rb_credentials["username"], rb_credentials["password"])
    yield client
    client.close()


@pytest.fixture(scope="session")
def shared_state():
    """Mutable bag for passing IDs/data between dependent tests in a session.

    Use with @pytest.mark.dependency (pytest-depends) to declare ordering.
    Example:
        shared_state["booking_id"] = resp.json()["bookingid"]
    """
    return {}


@pytest.fixture(scope="function", autouse=True)
def _api_log_reset(request):
    for name in request.fixturenames:
        try:
            val = request.getfixturevalue(name)
            if hasattr(val, "clear_log"):
                val.clear_log()
        except Exception:
            pass
    yield
