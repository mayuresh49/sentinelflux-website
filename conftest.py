import os
from pathlib import Path
import yaml
import pytest
from utils.logger import create_logger
from api.rest_client import RestClient
from api.graphql_client import GraphQLClient

ROOT_DIR = Path(__file__).resolve().parent


def load_yaml(path: Path):
    with path.open("r", encoding="utf-8") as stream:
        return yaml.safe_load(stream)


def pytest_addoption(parser):
    parser.addoption(
        "--env",
        action="store",
        default="qa",
        help="Environment profile to use: qa, staging, prod",
    )
    parser.addoption(
        "--locale",
        action="store",
        default="en-US",
        help="Localization locale code",
    )


@pytest.fixture(scope="session")
def config(request):
    env = request.config.getoption("--env")
    config_file = ROOT_DIR / "config" / f"env_{env}.yaml"
    if not config_file.exists():
        raise FileNotFoundError(f"Environment config not found: {config_file}")
    return load_yaml(config_file)


@pytest.fixture(scope="session")
def locale(request):
    return request.config.getoption("--locale")


@pytest.fixture(scope="session")
def logger(config):
    return create_logger(config.get("logging", {}))


@pytest.fixture(scope="session")
def rest_client(config, logger):
    return RestClient(base_url=config["api"]["rest_base_url"], logger=logger)


@pytest.fixture(scope="session")
def graphql_client(config, logger):
    return GraphQLClient(endpoint=config["api"]["graphql_endpoint"], logger=logger)


@pytest.fixture(scope="function")
def browser_page(page, config, logger, locale, ai_client, ai_config):
    page.set_default_timeout(config.get("browser", {}).get("timeout", 10000))
    ai_self_healing = ai_config.get("self_healing", False)
    # Note: ai_client is passed to page objects, but for now, we can store it in a way
    # Since page is from playwright, we can't modify it directly, but page objects will get it
    yield page


@pytest.fixture(scope="session")
def ai_config(config):
    return config.get("sentinelflux", {}).get("ai", {})


@pytest.fixture(scope="session")
def ai_client(ai_config):
    if not ai_config.get("enabled", False):
        return None
    mode = ai_config.get("mode", "mistral")
    api_key = ai_config.get("api_key")
    if mode == "mistral":
        from ai.clients.mistral_client import MistralClient
        return MistralClient(api_key)
    return None


@pytest.fixture(scope="function")
def locator_manager(locale):
    from utils.locator_manager import LocatorManager

    return LocatorManager(locale=locale)
