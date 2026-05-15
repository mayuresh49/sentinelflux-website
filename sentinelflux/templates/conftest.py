from pathlib import Path

import pytest
import yaml

ROOT_DIR = Path(__file__).resolve().parent


def pytest_addoption(parser):
    parser.addoption("--env", action="store", default="qa", help="Environment profile")
    parser.addoption("--locale", action="store", default="en-US", help="Locale code")
    parser.addoption("--session-login", action="store_true", default=False)


@pytest.fixture(scope="session")
def config(request):
    env = request.config.getoption("--env")
    f = ROOT_DIR / "config" / f"env_{env}.yaml"
    if not f.exists():
        raise FileNotFoundError(f"Config not found: {f}")
    with f.open() as fh:
        return yaml.safe_load(fh)


@pytest.fixture(scope="session")
def locale(request):
    return request.config.getoption("--locale")
