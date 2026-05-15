"""Booking screen POM for mobile (Appium)."""

from pathlib import Path

from pages.mobile.base_mobile_page import BaseMobilePage

_PRODUCT_ROOT = Path(__file__).resolve().parent.parent.parent  # products/restfulbooker
LOCATOR_FILE = _PRODUCT_ROOT / "locators" / "mobile" / "booking_screen.json"


class BookingScreen(BaseMobilePage):
    def __init__(self, driver, platform: str = "android"):
        super().__init__(driver, platform)
        self.load_locators(LOCATOR_FILE)

    # --- form interactions ---

    def fill_firstname(self, name: str):
        self.fill("firstname_field", name)

    def fill_lastname(self, name: str):
        self.fill("lastname_field", name)

    def fill_total_price(self, price: str):
        self.fill("total_price_field", str(price))

    def fill_checkin(self, date: str):
        """Date format: YYYY-MM-DD"""
        self.fill("checkin_field", date)

    def fill_checkout(self, date: str):
        """Date format: YYYY-MM-DD"""
        self.fill("checkout_field", date)

    def toggle_deposit_paid(self):
        self.tap("deposit_paid_toggle")

    def submit(self):
        self.scroll_to_element("submit_button")
        self.tap("submit_button")

    # --- queries ---

    def get_firstname(self) -> str:
        return self.get_attribute("firstname_field", "text")

    def get_lastname(self) -> str:
        return self.get_attribute("lastname_field", "text")

    def is_confirmed(self) -> bool:
        return self.is_visible("confirmation_message")

    def get_error(self) -> str:
        return self.get_text("error_message")

    def is_error_shown(self) -> bool:
        return self.is_visible("error_message")

    def is_booking_list_visible(self) -> bool:
        return self.is_visible("booking_list")

    # --- compound flows ---

    def create_booking(
        self,
        firstname: str,
        lastname: str,
        total_price: float,
        checkin: str,
        checkout: str,
        deposit_paid: bool = False,
    ):
        self.fill_firstname(firstname)
        self.fill_lastname(lastname)
        self.fill_total_price(str(total_price))
        self.fill_checkin(checkin)
        self.fill_checkout(checkout)
        if deposit_paid:
            self.toggle_deposit_paid()
        self.submit()
