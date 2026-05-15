from pages.base_page import BasePage
from utils.step import step_method


class PIMEmployeePage(BasePage):
    def __init__(self, page, base_url: str, locale: str = "en-US"):
        super().__init__(page, locale)
        self._base_url = base_url

    # --- navigation ---

    @step_method("Navigate to employee list")
    def navigate_to_list(self):
        self.navigate(f"{self._base_url}/web/index.php/pim/viewEmployeeList")
        self.page.wait_for_load_state("domcontentloaded")

    @step_method("Navigate to add employee form")
    def navigate_to_add(self):
        self.navigate(f"{self._base_url}/web/index.php/pim/addEmployee")
        self.page.wait_for_load_state("domcontentloaded")

    # --- employee list page ---

    @step_method("Search by employee name")
    def search_by_name(self, name: str):
        # Two "Type for hints..." autocomplete inputs on page — first is Employee Name filter
        inp = self.page.get_by_placeholder("Type for hints...").first
        inp.clear()
        inp.fill(name)
        self.page.get_by_role("button", name="Search").click()
        self.page.wait_for_load_state("networkidle")

    @step_method("Search by employee ID")
    def search_by_id(self, emp_id: str):
        self.page.get_by_placeholder("Employee Id").fill(emp_id)
        self.page.get_by_role("button", name="Search").click()
        self.page.wait_for_load_state("networkidle")

    @step_method("Click Add button")
    def click_add(self):
        self.page.get_by_role("button", name="Add").click()

    def get_record_count_text(self) -> str:
        # Scope to span to avoid matching the toast element which also says "Records Found"
        return self.page.locator("span.oxd-text--span", has_text="Records Found").first.inner_text()

    def is_no_records_shown(self) -> bool:
        return self.page.locator("span.oxd-text--span", has_text="No Records Found").first.is_visible()

    def is_on_list_page(self) -> bool:
        return "viewEmployeeList" in self.page.url

    # --- add employee form ---

    @step_method("Fill first name")
    def fill_firstname(self, name: str):
        self.page.get_by_placeholder("First Name").fill(name)

    @step_method("Fill middle name")
    def fill_middlename(self, name: str):
        self.page.get_by_placeholder("Middle Name").fill(name)

    @step_method("Fill last name")
    def fill_lastname(self, name: str):
        self.page.get_by_placeholder("Last Name").fill(name)

    @step_method("Fill employee ID")
    def fill_employee_id(self, emp_id: str):
        # OrangeHRM uses .oxd-input-group wrapper per field — find the group containing "Employee Id" label
        self.page.locator(".oxd-input-group:has(label:has-text('Employee Id')) input").fill(emp_id)

    @step_method("Save employee form")
    def save(self):
        self.page.get_by_role("button", name="Save").click()
        try:
            # Success: OrangeHRM navigates to the new employee's profile page
            self.page.wait_for_url(
                lambda url: "viewPersonalDetails" in url or "editEmployee" in url,
                timeout=15000,
            )
        except Exception:
            # Validation errors (client-side immediate or server-side) — wait briefly
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

    def get_validation_error(self) -> str:
        return self.page.locator(".oxd-input-field-error-message").first.inner_text()

    def is_on_profile_page(self) -> bool:
        # OrangeHRM 5.x navigates to viewPersonalDetails after employee creation
        return "editEmployee" in self.page.url or "viewPersonalDetails" in self.page.url
