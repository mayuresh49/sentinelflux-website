"""Mobile-specific fixtures — Appium driver lifecycle."""

import pytest

try:
    from appium import webdriver as appium_webdriver
    from appium.options import AppiumOptions
    APPIUM_AVAILABLE = True
except ImportError:
    APPIUM_AVAILABLE = False

_skip_no_appium = pytest.mark.skipif(
    not APPIUM_AVAILABLE,
    reason="appium-python-client not installed",
)


def pytest_collection_modifyitems(items):
    for item in items:
        if "mobile" in item.nodeid:
            item.add_marker(_skip_no_appium)


@pytest.fixture(scope="session")
def mobile_config(config):
    return config.get("mobile", {})


@pytest.fixture(scope="session")
def appium_driver(mobile_config):
    if not APPIUM_AVAILABLE:
        pytest.skip("appium-python-client not installed")

    appium_url = mobile_config.get("appium_url", "http://localhost:4723")
    caps = mobile_config.get("capabilities", {})

    if not caps:
        pytest.skip("No Appium capabilities configured in env config")

    options = AppiumOptions()
    for key, value in caps.items():
        options.set_capability(key, value)

    driver = appium_webdriver.Remote(appium_url, options=options)
    yield driver
    driver.quit()


@pytest.fixture(scope="function")
def booking_screen(appium_driver, mobile_config):
    from pages.mobile.booking_screen import BookingScreen
    platform = mobile_config.get("platform", "android")
    return BookingScreen(appium_driver, platform=platform)
