import json
import logging
from pathlib import Path
from typing import Callable

from playwright.sync_api import Page, TimeoutError

from utils.constants import LOCATOR_HEAL_TIMEOUT_MS

_log = logging.getLogger(__name__)

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
                self.page.wait_for_selector(loc, timeout=LOCATOR_HEAL_TIMEOUT_MS)
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
        self.page.goto(url, wait_until="domcontentloaded")

    def assert_text(self, key: str, expected: str, locator_file: str = None):
        actual = self.get_text(key, locator_file)
        assert actual == expected, f"Expected text '{expected}' but found '{actual}'"

    def try_resilient(self, description: str, action_fn: Callable, *args, **kwargs):
        """
        Three-tier resilient action wrapper — ALL tiers operate inside the existing browser session.
        SPA state, stepper position, form data, and auth cookies are preserved across all tiers.

        Tier 1 — Playwright semantic locator (deterministic, zero overhead on success).
        Tier 2 — AI reads page HTML → generates JS → page.evaluate() in same session.
        Tier 3 — AI reads accessibility tree (richer semantic context) → JS → same session.

        Tiers 2 and 3 require sentinelflux.ai.enabled: true in config.
        """
        try:
            return action_fn(*args, **kwargs)
        except TimeoutError:
            _log.warning("[Tier1] Playwright timeout for '%s' — escalating to AI JS healing", description)

        from core.ai_registry import get_ai_client
        ai_client = get_ai_client()
        if ai_client is None:
            raise RuntimeError(
                f"Playwright timeout on '{description}' and AI client is not configured "
                "(set sentinelflux.ai.enabled: true to enable self-healing)"
            )

        # Tier 2: AI + page HTML → JS in same session
        t2_exc: Exception | None = None
        try:
            html = self.page.content()[:8000]
            js = self._ai_js(ai_client, description, context=f"Page HTML:\n{html}")
            _log.info("[Tier2] Executing AI JS (HTML context): %s", js[:200])
            result = self.page.evaluate(js)
            _log.info("[Tier2] succeeded for '%s'", description)
            return result
        except Exception as exc:
            t2_exc = exc
            _log.warning("[Tier2] failed for '%s': %s — trying accessibility tree", description, t2_exc)

        # Tier 3: AI + accessibility tree (semantic, richer than HTML) → JS in same session
        try:
            import json as _json
            a11y = _json.dumps(self.page.accessibility.snapshot() or {}, indent=2)[:4000]
            js = self._ai_js(ai_client, description, context=f"Accessibility tree:\n{a11y}", temperature=0.0)
            _log.info("[Tier3] Executing AI JS (a11y context): %s", js[:200])
            result = self.page.evaluate(js)
            _log.info("[Tier3] succeeded for '%s'", description)
            return result
        except Exception as t3_exc:
            raise RuntimeError(
                f"All three tiers failed for '{description}'. "
                f"Tier2: {t2_exc}. Tier3: {t3_exc}."
            ) from t3_exc

    @staticmethod
    def _ai_js(ai_client, description: str, context: str, temperature: float = 0.1) -> str:
        prompt = (
            f"You are a web automation expert. A Playwright locator timed out for: '{description}'.\n"
            f"Write ONE JavaScript statement to perform this action on the current page.\n"
            f"Return ONLY the JavaScript. No explanation, no markdown, no comments.\n"
            f"Example: document.querySelector('button[type=submit]').click()\n\n"
            f"{context}"
        )
        js = ai_client.generate(prompt, max_tokens=200, temperature=temperature).strip()
        if js.startswith("```"):
            js = "\n".join(js.splitlines()[1:]).rstrip("`").strip()
        return js
