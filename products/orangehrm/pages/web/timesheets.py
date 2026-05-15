from pages.base_page import BasePage
from utils.step import step_method


class TimesheetsPage(BasePage):
    def __init__(self, page, base_url: str, locale: str = "en-US"):
        super().__init__(page, locale)
        self._base_url = base_url

    @step_method("Navigate to Add Timesheet form")
    def navigate_to_timesheets_form(self):
        self.navigate(f"{self._base_url}/web/index.php/time/addTimesheet")
        self.page.wait_for_load_state("domcontentloaded")

    def is_on_timesheets_form(self) -> bool:
        return "time/addTimesheet" in self.page.url

    @step_method("Fill employee ID")
    def fill_employee_id(self, emp_id: str):
        inp = self.page.get_by_placeholder("Type for hints...")
        inp.fill(emp_id)
        try:
            self.page.locator(".oxd-autocomplete-dropdown").wait_for(state="visible", timeout=5000)
            self.page.locator(".oxd-autocomplete-option").first.click()
        except Exception:
            pass

    @step_method("Fill from date")
    def fill_from_date(self, date_str: str):
        self.page.locator(".oxd-date-input input").first.fill(date_str)

    @step_method("Fill to date")
    def fill_to_date(self, date_str: str):
        self.page.locator(".oxd-date-input input").nth(1).fill(date_str)

    @step_method("Fill hours worked")
    def fill_hours_worked(self, hours: int):
        # Hours are entered per-day in a table; fill the first available hours cell
        self.page.locator("input[type='number'], .oxd-input[type='text']").first.fill(str(hours))

    @step_method("Submit timesheet")
    def submit_timesheet(self):
        self.page.get_by_role("button", name="Save").click()
        self.page.wait_for_load_state("networkidle")

    def is_submission_successful(self) -> bool:
        return self.page.locator(".oxd-toast--success").is_visible()

    def is_employee_id_missing_error(self) -> bool:
        return self.page.locator(".oxd-input-field-error-message").is_visible()

    def is_hours_worked_missing_error(self) -> bool:
        return self.page.locator(".oxd-input-field-error-message").is_visible()

    def is_invalid_hours_worked_error(self) -> bool:
        return self.page.locator(".oxd-input-field-error-message").is_visible()

    def is_invalid_from_date_error(self) -> bool:
        return self.page.locator(".oxd-input-field-error-message").is_visible()

    def is_duplicate_employee_id_error(self) -> bool:
        return (
            self.page.locator(".oxd-toast--error").is_visible()
            or self.page.locator(".oxd-input-field-error-message").is_visible()
        )
