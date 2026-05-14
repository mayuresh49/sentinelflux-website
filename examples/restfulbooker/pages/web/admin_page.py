from pages.base_page import BasePage
from utils.step import step_method


class AdminPage(BasePage):

    def __init__(self, page, base_url: str):
        super().__init__(page)
        self._base_url = base_url

    @step_method("Navigate to admin panel")
    def navigate(self):
        self.page.goto(f"{self._base_url}/admin", wait_until="domcontentloaded")

    @step_method("Enter admin username")
    def enter_username(self, username: str):
        self.page.locator("#username").fill(username)

    @step_method("Enter admin password")
    def enter_password(self, password: str):
        self.page.locator("#password").fill(password)

    @step_method("Click login button")
    def click_login(self):
        self.page.locator("#doLogin").click()

    def login(self, username: str, password: str):
        self.navigate()
        self.enter_username(username)
        self.enter_password(password)
        self.click_login()
        # Next.js navigates to /admin/rooms on success; wait up to 8s for that
        try:
            self.page.wait_for_url("**/admin/rooms**", timeout=8000)
            # wait for nav to hydrate — Rooms link appears after JS settles
            self.page.locator("a[href='/admin/rooms']").wait_for(state="visible", timeout=5000)
        except Exception:
            self.page.wait_for_timeout(2000)

    @step_method("Verify admin panel is visible")
    def is_admin_panel_visible(self) -> bool:
        # Logout is now a <button>, not a link
        return self.page.get_by_role("button", name="Logout").is_visible()

    @step_method("Click Rooms menu")
    def click_rooms(self):
        self.page.locator("a[href='/admin/rooms']").click()

    @step_method("Click Reports menu")
    def click_report(self):
        self.page.get_by_role("link", name="Report").click()

    @step_method("Click Branding menu")
    def click_branding(self):
        self.page.get_by_role("link", name="Branding").click()

    @step_method("Logout")
    def logout(self):
        self.page.get_by_role("button", name="Logout").click()
        # Site redirects to home page after logout
        try:
            self.page.wait_for_url(lambda url: "/admin" not in url, timeout=5000)
        except Exception:
            pass
