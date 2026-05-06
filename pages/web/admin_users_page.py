from pages.base_page import BasePage


class AdminUsersPage(BasePage):
    BASE_URL = "https://opensource-demo.orangehrmlive.com"

    def __init__(self, page, locale: str = "en-US"):
        super().__init__(page, locale)

    def navigate_to_list(self):
        self.navigate(f"{self.BASE_URL}/web/index.php/admin/viewSystemUsers")
        self.page.wait_for_load_state("domcontentloaded")

    def navigate_to_add(self):
        self.navigate(f"{self.BASE_URL}/web/index.php/admin/saveSystemUser")
        self.page.wait_for_load_state("domcontentloaded")

    def search_by_username(self, username: str):
        self.page.get_by_role("textbox", name="Username").fill(username)
        self.page.get_by_role("button", name="Search").click()
        self.page.wait_for_load_state("networkidle")

    def click_add(self):
        self.page.get_by_role("button", name="Add").click()

    def is_on_list_page(self) -> bool:
        return "viewSystemUsers" in self.page.url

    def is_no_records_shown(self) -> bool:
        return self.page.locator("span.oxd-text--span", has_text="No Records Found").first.is_visible()

    def get_record_count_text(self) -> str:
        return self.page.locator("span.oxd-text--span", has_text="Record").first.inner_text()

    def select_user_role(self, role: str):
        self.page.locator(".oxd-select-text").first.click()
        self.page.get_by_role("option", name=role).click()

    def select_status(self, status: str):
        self.page.locator(".oxd-select-text").nth(1).click()
        self.page.get_by_role("option", name=status).click()

    def fill_username(self, username: str):
        self.page.locator(".oxd-input-group:has(label:has-text('Username')) input").fill(username)

    def fill_password(self, password: str):
        self.page.locator(".oxd-input-group:has(label:has-text('Password')) input").fill(password)

    def fill_confirm_password(self, password: str):
        self.page.locator(".oxd-input-group:has(label:has-text('Confirm Password')) input").fill(password)

    def fill_employee_name(self, name: str):
        inp = self.page.get_by_placeholder("Type for hints...")
        inp.fill(name)
        # Wait for the autocomplete dropdown to appear then pick first suggestion
        self.page.locator(".oxd-autocomplete-dropdown").wait_for(state="visible", timeout=10000)
        self.page.locator(".oxd-autocomplete-option").first.click()

    def save(self):
        self.page.get_by_role("button", name="Save").click()
        try:
            self.page.wait_for_url(
                lambda url: "saveSystemUser" not in url and "viewSystemUsers" not in url,
                timeout=15000,
            )
        except Exception:
            try:
                self.page.locator(".oxd-input-field-error-message").first.wait_for(
                    state="visible", timeout=5000
                )
            except Exception:
                pass

    def cancel(self):
        self.page.get_by_role("button", name="Cancel").click()

    def is_success_shown(self) -> bool:
        return self.page.locator(".oxd-toast--success").is_visible()

    def is_validation_error_shown(self) -> bool:
        return self.page.locator(".oxd-input-field-error-message").first.is_visible()

    def is_on_profile_page(self) -> bool:
        return "saveSystemUser" not in self.page.url and "viewSystemUsers" not in self.page.url
