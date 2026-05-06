"""Base class for all mobile screen objects (Appium)."""

import json
import logging
from pathlib import Path
from typing import Any

from appium.webdriver import Remote as AppiumDriver
from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from utils.constants import LOCATOR_HEAL_TIMEOUT_MS

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
_log = logging.getLogger(__name__)

# Timeout in seconds (Selenium-style, not ms)
_HEAL_TIMEOUT_S = LOCATOR_HEAL_TIMEOUT_MS / 1000


def _parse_locator(locator_str: str) -> tuple[str, str]:
    """Convert a locator string to an (AppiumBy, value) tuple.

    Conventions:
      ~name           → ACCESSIBILITY_ID
      //...           → XPATH
      id:value        → ID
      class:value     → CLASS_NAME
      predicate:value → IOS_PREDICATE_STRING
      uia:value       → ANDROID_UIAUTOMATOR
      (anything else) → XPATH
    """
    if locator_str.startswith("~"):
        return AppiumBy.ACCESSIBILITY_ID, locator_str[1:]
    if locator_str.startswith("//") or locator_str.startswith("(//"):
        return AppiumBy.XPATH, locator_str
    if locator_str.startswith("id:"):
        return AppiumBy.ID, locator_str[3:]
    if locator_str.startswith("class:"):
        return AppiumBy.CLASS_NAME, locator_str[6:]
    if locator_str.startswith("predicate:"):
        return AppiumBy.IOS_PREDICATE, locator_str[10:]
    if locator_str.startswith("uia:"):
        return AppiumBy.ANDROID_UIAUTOMATOR, locator_str[4:]
    return AppiumBy.XPATH, locator_str


class BaseMobilePage:
    def __init__(self, driver: AppiumDriver, platform: str = "android"):
        self.driver = driver
        self.platform = platform.lower()  # "android" or "ios"
        self._locators: dict[str, Any] = {}
        self._locator_file: str = ""

    def load_locators(self, locator_file: str):
        path = ROOT_DIR / "locators" / locator_file
        with path.open("r", encoding="utf-8") as f:
            self._locators = json.load(f)
        self._locator_file = locator_file

    # --- locator resolution ---

    def _get_locator_def(self, key: str) -> Any:
        locator_def = self._locators.get(key)
        if locator_def is None:
            raise KeyError(f"Locator '{key}' not defined in {self._locator_file}")
        return locator_def

    def _primary_locator(self, key: str) -> str:
        locator_def = self._get_locator_def(key)
        if isinstance(locator_def, str):
            return locator_def
        # Platform-specific override takes precedence over primary
        if self.platform in locator_def:
            return locator_def[self.platform]
        return locator_def.get("primary", locator_def)

    def _alternative_locators(self, key: str) -> list[str]:
        locator_def = self._get_locator_def(key)
        if isinstance(locator_def, str):
            return []
        return locator_def.get("alternatives", [])

    def healed_element(self, key: str):
        """Try primary locator then alternatives; return the first matching element."""
        primary = self._primary_locator(key)
        candidates = [primary] + self._alternative_locators(key)
        for loc in candidates:
            by, value = _parse_locator(loc)
            try:
                el = WebDriverWait(self.driver, _HEAL_TIMEOUT_S).until(
                    EC.presence_of_element_located((by, value))
                )
                if loc != primary:
                    _log.warning("Healed locator for '%s' using alternative: %s", key, loc)
                return el
            except TimeoutException:
                continue
        raise TimeoutException(
            f"No valid locator for '{key}' after trying {len(candidates)} options"
        )

    # --- interactions ---

    def tap(self, key: str):
        self.healed_element(key).click()

    def fill(self, key: str, text: str):
        el = self.healed_element(key)
        el.clear()
        el.send_keys(text)

    def get_text(self, key: str) -> str:
        return self.healed_element(key).text

    def get_attribute(self, key: str, attribute: str) -> str:
        return self.healed_element(key).get_attribute(attribute)

    def is_visible(self, key: str) -> bool:
        try:
            el = self.healed_element(key)
            return el.is_displayed()
        except (TimeoutException, NoSuchElementException):
            return False

    def wait_for_element(self, key: str, timeout: float = 10.0):
        primary = self._primary_locator(key)
        by, value = _parse_locator(primary)
        WebDriverWait(self.driver, timeout).until(
            EC.visibility_of_element_located((by, value))
        )

    def wait_for_text(self, key: str, expected: str, timeout: float = 10.0):
        primary = self._primary_locator(key)
        by, value = _parse_locator(primary)
        WebDriverWait(self.driver, timeout).until(
            EC.text_to_be_present_in_element((by, value), expected)
        )

    # --- gestures ---

    def swipe_up(self, duration_ms: int = 800):
        size = self.driver.get_window_size()
        start_x = size["width"] // 2
        start_y = int(size["height"] * 0.7)
        end_y = int(size["height"] * 0.3)
        self.driver.swipe(start_x, start_y, start_x, end_y, duration_ms)

    def swipe_down(self, duration_ms: int = 800):
        size = self.driver.get_window_size()
        start_x = size["width"] // 2
        start_y = int(size["height"] * 0.3)
        end_y = int(size["height"] * 0.7)
        self.driver.swipe(start_x, start_y, start_x, end_y, duration_ms)

    def scroll_to_element(self, key: str, max_swipes: int = 5):
        for _ in range(max_swipes):
            if self.is_visible(key):
                return
            self.swipe_up()
        raise TimeoutException(f"Element '{key}' not visible after {max_swipes} swipes")

    # --- assertions ---

    def assert_text(self, key: str, expected: str):
        actual = self.get_text(key)
        assert actual == expected, f"Expected '{expected}' but got '{actual}' for '{key}'"

    def assert_visible(self, key: str):
        assert self.is_visible(key), f"Element '{key}' is not visible"
