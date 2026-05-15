"""Login screen POM for OrangeHRM mobile (Appium)."""

from pathlib import Path

from pages.mobile.base_mobile_page import BaseMobilePage

_PRODUCT_ROOT = Path(__file__).resolve().parent.parent.parent  # products/orangehrm
LOCATOR_FILE = _PRODUCT_ROOT / "locators" / "mobile" / "login_screen.json"


class LoginScreen(BaseMobilePage):
    def __init__(self, driver, platform: str = "android"):
        super().__init__(driver, platform)
        self.load_locators(LOCATOR_FILE)

    def fill_username(self, username: str):
        self.fill("username_field", username)

    def fill_password(self, password: str):
        self.fill("password_field", password)

    def submit(self):
        self.tap("login_button")

    def login(self, username: str, password: str):
        self.fill_username(username)
        self.fill_password(password)
        self.submit()

    def is_on_dashboard(self) -> bool:
        return self.is_visible("dashboard_header")

    def is_error_shown(self) -> bool:
        return self.is_visible("error_message")

    def get_error(self) -> str:
        return self.get_text("error_message")

    def is_username_error_shown(self) -> bool:
        return self.is_visible("username_error")

    def is_password_error_shown(self) -> bool:
        return self.is_visible("password_error")
