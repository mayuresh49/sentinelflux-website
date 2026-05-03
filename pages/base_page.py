import json
from pathlib import Path
from typing import Any, Dict
from playwright.sync_api import Page, TimeoutError

ROOT_DIR = Path(__file__).resolve().parent.parent


class BasePage:
    def __init__(self, page: Page, locale: str = "en-US"):
        self.page = page
        self.locale = locale
        self.locators = {}
        from utils.locator_manager import LocatorManager
        self.locator_manager = LocatorManager(locale=locale)

    def load_locators(self, locator_file: str):
        path = ROOT_DIR / "locators" / locator_file
        with path.open("r", encoding="utf-8") as stream:
            self.locators = json.load(stream)

    def locator(self, key: str) -> str:
        value = self.locators.get(key)
        if not value:
            raise KeyError(f"Locator '{key}' not defined")
        if isinstance(value, dict):
            return value.get(self.locale, value.get("default"))
        return value

    def healed_locator(self, key: str, locator_file: str) -> str:
        """Self-healing locator: try primary, then alternatives."""
        primary = self.locator_manager.get(locator_file, key)
        alternatives = self.locator_manager.get_alternatives(locator_file, key)
        locators_to_try = [primary] + alternatives
        for loc in locators_to_try:
            try:
                self.page.wait_for_selector(loc, timeout=2000)
                return loc
            except TimeoutError:
                continue
        raise TimeoutError(f"No valid locator found for '{key}' after trying {len(locators_to_try)} options")

    def click(self, key: str, locator_file: str = None):
        if locator_file:
            loc = self.healed_locator(key, locator_file)
        else:
            loc = self.locator(key)
        self.page.click(loc)

    def fill(self, key: str, text: str, locator_file: str = None):
        if locator_file:
            loc = self.healed_locator(key, locator_file)
        else:
            loc = self.locator(key)
        self.page.fill(loc, text)

    def get_text(self, key: str, locator_file: str = None) -> str:
        if locator_file:
            loc = self.healed_locator(key, locator_file)
        else:
            loc = self.locator(key)
        return self.page.inner_text(loc)

    def is_visible(self, key: str, locator_file: str = None) -> bool:
        if locator_file:
            loc = self.healed_locator(key, locator_file)
        else:
            loc = self.locator(key)
        return self.page.is_visible(loc)

    def wait_for_selector(self, key: str, timeout: int = 10000, locator_file: str = None):
        if locator_file:
            loc = self.healed_locator(key, locator_file)
        else:
            loc = self.locator(key)
        self.page.wait_for_selector(loc, timeout=timeout)

    def navigate(self, url: str):
        self.page.goto(url)

    def assert_text(self, key: str, expected: str, locator_file: str = None):
        actual = self.get_text(key, locator_file)
        assert actual == expected, f"Expected text '{expected}' but found '{actual}'"
