from pages.base_page import BasePage
from utils.step import step_method


class LoginPage(BasePage):
    BASE_URL = "https://opensource-demo.orangehrmlive.com"

    def __init__(self, page, locale: str = "en-US"):
        super().__init__(page, locale)

    @step_method("Navigate to login page")
    def navigate_to_login(self):
        self.navigate(f"{self.BASE_URL}/web/index.php/auth/login")
        self.page.wait_for_load_state("domcontentloaded")

    @step_method("Fill username")
    def fill_username(self, username: str):
        self.page.get_by_placeholder("Username").fill(username)

    @step_method("Fill password")
    def fill_password(self, password: str):
        self.page.get_by_placeholder("Password").fill(password)

    @step_method("Submit login form")
    def submit(self):
        self.page.get_by_role("button", name="Login").click()
        try:
            # Valid login: server redirects to dashboard
            self.page.wait_for_url("**/dashboard/**", timeout=10000)
        except Exception:
            # Invalid login variants:
            #   wrong credentials → .oxd-alert (server response, ~4s on demo)
            #   empty fields      → .oxd-input-field-error-message (Vue client validation, immediate)
            self.page.locator(".oxd-alert, .oxd-input-field-error-message").first.wait_for(
                state="visible", timeout=15000
            )

    def login(self, username: str, password: str):
        self.fill_username(username)
        self.fill_password(password)
        self.submit()

    def get_error_message(self) -> str:
        if self.page.locator(".oxd-alert").is_visible():
            return self.page.locator(".oxd-alert").inner_text()
        return self.page.locator(".oxd-input-field-error-message").first.inner_text()

    def is_error_displayed(self) -> bool:
        return (
            self.page.locator(".oxd-alert").is_visible()
            or self.page.locator(".oxd-input-field-error-message").first.is_visible()
        )

    def is_on_dashboard(self) -> bool:
        return "dashboard" in self.page.url
