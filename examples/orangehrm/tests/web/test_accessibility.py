import pytest
from pages.web.login_page import LoginPage

_BASE = "https://opensource-demo.orangehrmlive.com"


@pytest.mark.web
@pytest.mark.a11y
def test_OH_A11Y_001_login_inputs_have_associated_labels(page):
    LoginPage(page).navigate_to_login()
    for field in ("username", "password"):
        # Playwright's get_by_label uses <label> for= or aria-label
        inp = page.get_by_label(field, exact=False)
        assert inp.count() >= 1, f"No labeled input found for '{field}'"


@pytest.mark.web
@pytest.mark.a11y
def test_OH_A11Y_002_login_page_has_heading(page):
    LoginPage(page).navigate_to_login()
    headings = page.get_by_role("heading")
    assert headings.count() >= 1, "No heading found on login page"


@pytest.mark.web
@pytest.mark.a11y
def test_OH_A11Y_003_login_form_reachable_by_keyboard(page):
    LoginPage(page).navigate_to_login()
    page.keyboard.press("Tab")
    focused_tag = page.evaluate("document.activeElement.tagName")
    assert focused_tag in ("INPUT", "BUTTON", "A", "SELECT", "TEXTAREA"), \
        f"Tab key did not focus a form element; focused: {focused_tag}"


@pytest.mark.web
@pytest.mark.a11y
def test_OH_A11Y_004_login_page_images_have_alt_text(page):
    LoginPage(page).navigate_to_login()
    images = page.locator("img")
    count = images.count()
    for i in range(count):
        img = images.nth(i)
        alt = img.get_attribute("alt")
        src = img.get_attribute("src") or f"image[{i}]"
        assert alt is not None, f"Image missing alt attribute: {src}"


@pytest.mark.web
@pytest.mark.a11y
def test_OH_A11Y_005_login_error_is_visible_when_credentials_invalid(page):
    lp = LoginPage(page)
    lp.navigate_to_login()
    lp.login("baduser", "badpass")
    assert lp.is_error_displayed(), "Error message not visible for invalid credentials"
    error_locator = page.locator(".oxd-alert, [class*='alert'], [class*='error']").first
    assert error_locator.is_visible(), "Error element is in DOM but not visible"


@pytest.mark.web
@pytest.mark.a11y
def test_OH_A11Y_006_dashboard_nav_links_have_text(page):
    lp = LoginPage(page)
    lp.navigate_to_login()
    lp.login("Admin", "admin123")
    assert lp.is_on_dashboard()
    nav_links = page.locator("nav a, .oxd-main-menu a")
    count = nav_links.count()
    assert count > 0, "No nav links found on dashboard"
    for i in range(count):
        link = nav_links.nth(i)
        text = (link.inner_text() or "").strip()
        aria_label = link.get_attribute("aria-label") or ""
        assert text or aria_label, f"Nav link {i} has no visible text or aria-label"
