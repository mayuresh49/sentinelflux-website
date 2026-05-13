from pages.base_page import BasePage
from utils.step import step_method


class HomePage(BasePage):

    def __init__(self, page, base_url: str):
        super().__init__(page)
        self._base_url = base_url

    @step_method("Navigate to home page")
    def navigate(self):
        self.page.goto(self._base_url, wait_until="networkidle")

    @step_method("Verify rooms are listed")
    def rooms_are_listed(self) -> bool:
        return self.page.locator(".room-card").count() > 0

    @step_method("Get room count")
    def get_room_count(self) -> int:
        return self.page.locator(".room-card").count()

    @step_method("Click Book This Room")
    def click_book_room(self, index: int = 0):
        # Clicks "Book now" link → navigates to /reservation/... then reveals contact form
        self.page.locator(".room-card").nth(index).locator("a.btn-primary").click()
        self.page.wait_for_load_state("networkidle")
        self.page.locator("button:has-text('Reserve Now')").click()
        self.page.wait_for_timeout(500)

    @step_method("Fill booking first name")
    def fill_firstname(self, value: str):
        self.page.locator("input[placeholder='Firstname']").fill(value)

    @step_method("Fill booking last name")
    def fill_lastname(self, value: str):
        self.page.locator("input[placeholder='Lastname']").fill(value)

    @step_method("Fill booking email")
    def fill_email(self, value: str):
        self.page.locator("input[placeholder='Email']").fill(value)

    @step_method("Fill booking phone")
    def fill_phone(self, value: str):
        self.page.locator("input[placeholder='Phone']").fill(value)

    @step_method("Submit booking form")
    def submit_booking(self):
        self.page.locator("button:has-text('Reserve Now')").click()

    @step_method("Verify booking confirmation shown")
    def is_booking_confirmed(self) -> bool:
        return self.page.get_by_text("Booking Confirmed").is_visible()

    @step_method("Verify validation error shown")
    def has_validation_error(self) -> bool:
        return self.page.locator(".alert-danger").is_visible()
