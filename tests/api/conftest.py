import pytest
from api.orangehrm_client import OrangeHRMClient


@pytest.fixture(scope="session")
def orangehrm_client(browser, session_authed_page):
    """
    Session-scoped OrangeHRM API client.

    When --session-login is active, borrows cookies from the already-logged-in
    web session page — avoids a second concurrent browser login hitting the demo
    site at the same time as the web suite.

    Without --session-login, creates a dedicated Playwright context to authenticate.
    """
    from pages.web.login_page import LoginPage

    if session_authed_page is not None:
        client = OrangeHRMClient.from_playwright_cookies(
            session_authed_page.context.cookies()
        )
        yield client
        client.close()
        return

    ctx = browser.new_context()
    pg = ctx.new_page()
    LoginPage(pg).login("Admin", "admin123")
    client = OrangeHRMClient.from_playwright_cookies(ctx.cookies())
    yield client
    ctx.close()
    client.close()
