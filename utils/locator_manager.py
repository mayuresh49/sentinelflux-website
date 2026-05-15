import json
import logging
from typing import Any, Dict

from utils.paths import ROOT as ROOT_DIR

_log = logging.getLogger(__name__)


class LocatorManager:
    def __init__(self, locale: str = "en-US"):
        self.locale = locale
        self.cache: Dict[str, Dict[str, Any]] = {}

    def load(self, locator_file: str) -> Dict[str, Any]:
        if locator_file in self.cache:
            return self.cache[locator_file]
        path = ROOT_DIR / "locators" / locator_file
        with path.open("r", encoding="utf-8") as stream:
            locator_data = json.load(stream)
        self.cache[locator_file] = locator_data
        return locator_data

    def get(self, locator_file: str, key: str) -> str:
        locators = self.load(locator_file)
        locator = locators.get(key)
        if locator is None:
            raise KeyError(f"Locator '{key}' not found in {locator_file}")
        if isinstance(locator, dict):
            value = locator.get(self.locale)
            if value is None:
                _log.warning("Locale '%s' not found for '%s' in %s — using default", self.locale, key, locator_file)
                value = locator.get("default")
            return value
        return locator

    def get_alternatives(self, locator_file: str, key: str) -> list:
        """Get alternative locators for self-healing."""
        locators = self.load(locator_file)
        locator = locators.get(key)
        if isinstance(locator, dict):
            alternatives = locator.get("alternatives", [])
            return alternatives
        return []
