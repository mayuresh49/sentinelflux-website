"""Page object for 404 Not Found — selectors verified against live app."""
from __future__ import annotations

from pages.base_page import BasePage


class LeavePage(BasePage):
    URL = "/leave"

    def navigate(self) -> None:
        self.page.goto(f"{self.base_url}/leave")

    def get_validation_error(self, field_name: str) -> str:
        """Return visible validation message for field_name, or empty string."""
        try:
            sel = f"[data-testid='{field_name}-error'], .oxd-input-field-error-message, .error-message"
            return self.page.locator(sel).first.inner_text().strip()
        except Exception:
            return ""
