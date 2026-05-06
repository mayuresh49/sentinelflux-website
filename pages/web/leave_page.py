from pages.base_page import BasePage
from utils.step import step_method


class LeavePage(BasePage):
    BASE_URL = "https://opensource-demo.orangehrmlive.com"

    def __init__(self, page, locale: str = "en-US"):
        super().__init__(page, locale)

    @step_method("Navigate to leave list")
    def navigate_to_list(self):
        self.navigate(f"{self.BASE_URL}/web/index.php/leave/viewLeaveList")
        self.page.wait_for_load_state("domcontentloaded")

    @step_method("Fill date from")
    def fill_date_from(self, date_str: str):
        self.page.locator(".oxd-date-input input").first.fill(date_str)

    @step_method("Fill date to")
    def fill_date_to(self, date_str: str):
        self.page.locator(".oxd-date-input input").nth(1).fill(date_str)

    @step_method("Select status filter")
    def select_status(self, status: str):
        self.page.locator(".oxd-select-text").first.click()
        self.page.get_by_role("option", name=status).click()

    @step_method("Click Search")
    def click_search(self):
        self.page.get_by_role("button", name="Search").click()
        self.page.wait_for_load_state("networkidle")

    def get_record_count_text(self) -> str:
        return self.page.locator("span.oxd-text--span", has_text="Record").first.inner_text()

    def is_no_records_shown(self) -> bool:
        return self.page.locator("span.oxd-text--span", has_text="No Records Found").first.is_visible()

    def is_on_list_page(self) -> bool:
        return "viewLeaveList" in self.page.url

    def get_row_count(self) -> int:
        return self.page.locator(".oxd-table-body .oxd-table-row").count()
