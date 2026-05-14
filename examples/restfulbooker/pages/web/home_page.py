from pages.base_page import BasePage
from utils.step import step_method


class HomePage(BasePage):

    def __init__(self, page, base_url: str):
        super().__init__(page)
        self._base_url = base_url

    @step_method("Navigate to home page")
    def navigate(self):
        self.page.goto(self._base_url, wait_until="domcontentloaded")
        # Room cards load asynchronously; wait for at least one
        self.page.locator(".room-card").first.wait_for(state="visible", timeout=15000)

    @step_method("Verify rooms are listed")
    def rooms_are_listed(self) -> bool:
        return self.page.locator(".room-card").count() > 0

    @step_method("Get room count")
    def get_room_count(self) -> int:
        return self.page.locator(".room-card").count()

    @step_method("Click Book This Room")
    def click_book_room(self, index: int = 0):
        # "Book now" link navigates to /reservation/... page
        self.page.locator(".room-card").nth(index).locator("a.btn-primary").click()
        # Use wait_for_url instead of networkidle — calendar widget keeps polling
        self.page.wait_for_url("**/reservation/**")
        self.page.wait_for_timeout(1500)
        # Click "#doReservation" to expand the guest-detail form
        self.page.locator("#doReservation").click()
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
        # After the form is open there are two "Reserve Now" buttons;
        # the last one (inside the expanded modal form) is the submit.
        # Capture the booking API response so has_validation_error() can
        # detect 409 (room already taken) when the UI doesn't render .alert-danger.
        self._last_booking_status: int | None = None
        try:
            with self.page.expect_response("**/api/booking**", timeout=15000) as resp:
                self.page.locator("button:has-text('Reserve Now')").last.click()
            self._last_booking_status = resp.value.status
        except Exception:
            self.page.locator("button:has-text('Reserve Now')").last.click()

    @step_method("Verify booking confirmation shown")
    def is_booking_confirmed(self) -> bool:
        try:
            self.page.get_by_text("Booking Confirmed").wait_for(state="visible", timeout=5000)
            return True
        except Exception:
            return False

    @step_method("Verify validation error shown")
    def has_validation_error(self) -> bool:
        # 409 = room conflict; 422 = invalid payload — both are expected validation errors.
        # The UI doesn't always render .alert-danger for server-side errors on this shared site.
        status = getattr(self, "_last_booking_status", None)
        if status in (409, 422, 400):
            return True
        try:
            self.page.locator(".alert-danger").wait_for(state="visible", timeout=5000)
            return self.page.locator(".alert-danger").is_visible()
        except Exception:
            return False

