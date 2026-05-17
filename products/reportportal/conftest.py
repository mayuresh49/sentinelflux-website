import sys
from pathlib import Path

_PRODUCT_ROOT = Path(__file__).resolve().parent
_FRAMEWORK_ROOT = _PRODUCT_ROOT.parent.parent

for _p in (str(_PRODUCT_ROOT), str(_FRAMEWORK_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import pytest
import yaml


def _load_config(request) -> dict:
    env = request.config.getoption("--env", default="qa")
    config_file = _PRODUCT_ROOT / "config" / f"env_{env}.yaml"
    if not config_file.exists():
        raise FileNotFoundError(f"ReportPortal config not found: {config_file}")
    with config_file.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="session")
def rp_config(request):
    return _load_config(request)


@pytest.fixture(scope="session")
def rp_base_url(rp_config):
    return rp_config.get("reportportal", {}).get("base_url", "http://localhost:8080")


@pytest.fixture(scope="session")
def rp_api_token(rp_config):
    return rp_config.get("reportportal", {}).get("api_token")


@pytest.fixture(scope="session")
def rp_project(rp_config):
    return rp_config.get("reportportal", {}).get("project", "default_project")


@pytest.fixture(scope="session")
def shared_state():
    return {}
