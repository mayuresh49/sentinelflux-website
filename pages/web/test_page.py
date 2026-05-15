from playwright.sync_api import Page

from pages.base_page import BasePage


class SeleniumTestPage(BasePage):
    def __init__(self, page: Page, locale: str = "en-US", ai_client=None, ai_self_healing=False):
        super().__init__(page, locale, ai_client, ai_self_healing)
        self.load_locators("web/test_page.json")
        self.locator_file = "web/test_page.json"

    def fill_first_name(self, value: str):
        self.fill("first_name", value, self.locator_file)

    def fill_surname(self, value: str):
        self.fill("surname", value, self.locator_file)

    def select_gender(self, value: str):
        loc = self.healed_locator("gender", self.locator_file)
        self.page.select_option(loc, value)

    def select_color(self, color: str):
        if color == "red":
            loc = self.healed_locator("red_radio", self.locator_file)
            self.page.check(loc)
        elif color == "blue":
            loc = self.healed_locator("blue_radio", self.locator_file)
            self.page.check(loc)

    def check_contact(self, contact: str):
        if contact == "email":
            loc = self.healed_locator("email_checkbox", self.locator_file)
            self.page.check(loc)
        elif contact == "sms":
            loc = self.healed_locator("sms_checkbox", self.locator_file)
            self.page.check(loc)

    def fill_message(self, message: str):
        self.fill("tell_more", message, self.locator_file)

    def select_continents(self, continents: list):
        loc = self.healed_locator("continents", self.locator_file)
        self.page.select_option(loc, continents)

    def submit_form(self):
        self.click("submit_button", self.locator_file)

    def get_first_name_value(self) -> str:
        loc = self.healed_locator("first_name", self.locator_file)
        return self.page.input_value(loc)

    def get_surname_value(self) -> str:
        loc = self.healed_locator("surname", self.locator_file)
        return self.page.input_value(loc)

    def get_selected_gender(self) -> str:
        loc = self.healed_locator("gender", self.locator_file)
        return self.page.locator(loc).input_value()

    def is_color_selected(self, color: str) -> bool:
        if color == "red":
            loc = self.healed_locator("red_radio", self.locator_file)
            return self.page.locator(loc).is_checked()
        elif color == "blue":
            loc = self.healed_locator("blue_radio", self.locator_file)
            return self.page.locator(loc).is_checked()
        return False

    def is_contact_checked(self, contact: str) -> bool:
        if contact == "email":
            loc = self.healed_locator("email_checkbox", self.locator_file)
            return self.page.locator(loc).is_checked()
        elif contact == "sms":
            loc = self.healed_locator("sms_checkbox", self.locator_file)
            return self.page.locator(loc).is_checked()
        return False

    def get_message_value(self) -> str:
        loc = self.healed_locator("tell_more", self.locator_file)
        return self.page.input_value(loc)

    def get_selected_continents(self) -> list:
        loc = self.healed_locator("continents", self.locator_file)
        return self.page.locator(loc).evaluate("el => Array.from(el.selectedOptions).map(o => o.value)")