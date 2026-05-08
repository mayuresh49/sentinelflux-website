from pages.base_page import BasePage
from utils.step import step_method


class AdminPage(BasePage):

    def __init__(self, page, base_url: str):
        super().__init__(page)
        self._base_url = base_url

    @step_method("Navigate to admin panel")
    def navigate(self):
        self.page.goto(f"{self._base_url}/#/admin", wait_until="domcontentloaded")

    @step_method("Enter admin username")
    def enter_username(self, username: str):
        self.page.locator("input[data-testid='username']").fill(username)

    @step_method("Enter admin password")
    def enter_password(self, password: str):
        self.page.locator("input[data-testid='password']").fill(password)

    @step_method("Click login button")
    def click_login(self):
        self.page.locator("button[data-testid='submit']").click()

    def login(self, username: str, password: str):
        self.navigate()
        self.enter_username(username)
        self.enter_password(password)
        self.click_login()
        self.page.wait_for_load_state("networkidle")

    @step_method("Verify admin panel is visible")
    def is_admin_panel_visible(self) -> bool:
        return self.page.locator("#root").is_visible()

    @step_method("Click Rooms menu")
    def click_rooms(self):
        self.page.locator("a[href='#/admin/rooms']").click()

    @step_method("Click Reports menu")
    def click_report(self):
        self.page.get_by_role("link", name="Report").click()

    @step_method("Click Branding menu")
    def click_branding(self):
        self.page.get_by_role("link", name="Branding").click()

    @step_method("Logout")
    def logout(self):
        self.page.get_by_role("link", name="Logout").click()
