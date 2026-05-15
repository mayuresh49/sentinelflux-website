from pages.base_page import BasePage
from utils.step import step_method


class AdminUsersPage(BasePage):
    def __init__(self, page, base_url: str, locale: str = "en-US"):
        super().__init__(page, locale)
        self._base_url = base_url

    @step_method("Navigate to system users list")
    def navigate_to_list(self):
        self.navigate(f"{self._base_url}/web/index.php/admin/viewSystemUsers")
        self.page.wait_for_load_state("domcontentloaded")

    @step_method("Navigate to add user form")
    def navigate_to_add(self):
        self.navigate(f"{self._base_url}/web/index.php/admin/saveSystemUser")
        self.page.wait_for_load_state("domcontentloaded")

    @step_method("Search by username")
    def search_by_username(self, username: str):
        # OrangeHRM Vue labels are not wired via for= attribute; scope to the group container
        self.page.locator(".oxd-input-group:has(label:has-text('Username')) input").fill(username)
        self.page.get_by_role("button", name="Search").click()
        self.page.wait_for_load_state("networkidle")

    @step_method("Click Add button")
    def click_add(self):
        self.page.get_by_role("button", name="Add").click()

    def is_on_list_page(self) -> bool:
        return "viewSystemUsers" in self.page.url

    def is_no_records_shown(self) -> bool:
        return self.page.locator("span.oxd-text--span", has_text="No Records Found").first.is_visible()

    def get_record_count_text(self) -> str:
        return self.page.locator("span.oxd-text--span", has_text="Record").first.inner_text()

    @step_method("Select user role")
    def select_user_role(self, role: str):
        self.page.locator(".oxd-select-text").first.click()
        self.page.get_by_role("option", name=role).click()

    @step_method("Select status")
    def select_status(self, status: str):
        self.page.locator(".oxd-select-text").nth(1).click()
        self.page.get_by_role("option", name=status).click()

    @step_method("Fill username")
    def fill_username(self, username: str):
        self.page.locator(".oxd-input-group:has(label:has-text('Username')) input").fill(username)

    @step_method("Fill password")
    def fill_password(self, password: str):
        self.page.locator(".oxd-input-group:has(label:has-text('Password')) input").fill(password)

    @step_method("Fill confirm password")
    def fill_confirm_password(self, password: str):
        self.page.locator(".oxd-input-group:has(label:has-text('Confirm Password')) input").fill(password)

    @step_method("Fill employee name (autocomplete)")
    def fill_employee_name(self, name: str):
        inp = self.page.get_by_placeholder("Type for hints...")
        inp.fill(name)
        # Wait for the autocomplete dropdown to appear then pick first suggestion
        self.page.locator(".oxd-autocomplete-dropdown").wait_for(state="visible", timeout=10000)
        self.page.locator(".oxd-autocomplete-option").first.click()

    @step_method("Save user form")
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

    @step_method("Cancel and return to list")
    def cancel(self):
        self.page.get_by_role("button", name="Cancel").click()

    def is_success_shown(self) -> bool:
        return self.page.locator(".oxd-toast--success").is_visible()

    def is_validation_error_shown(self) -> bool:
        return self.page.locator(".oxd-input-field-error-message").first.is_visible()

    def is_on_profile_page(self) -> bool:
        return "saveSystemUser" not in self.page.url and "viewSystemUsers" not in self.page.url
