"""Page object for OrangeHRM API Documentation – OrangeHRM — selectors verified against live app."""
from __future__ import annotations

from pages.base_page import BasePage


class HcEnUsArticles900001765703OrangehrmApiDocumentationPage(BasePage):
    URL = "/hc/en-us/articles/900001765703-OrangeHRM-API-Documentation"

    def navigate(self) -> None:
        self.page.goto(f"{self.base_url}/hc/en-us/articles/900001765703-OrangeHRM-API-Documentation")

    def fill_query(self, value: str) -> None:
        self.page.fill('#query', value)

    def click_search(self) -> None:
        self.page.click("input[name='commit']")

    def click_follow(self) -> None:
        self.page.click("button:has-text('Follow')")

    def get_validation_error(self, field_name: str) -> str:
        """Return visible validation message for field_name, or empty string."""
        try:
            sel = f"[data-testid='{field_name}-error'], .oxd-input-field-error-message, .error-message"
            return self.page.locator(sel).first.inner_text().strip()
        except Exception:
            return ""
