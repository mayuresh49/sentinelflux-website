import pytest
from pages.web.login_page import LoginPage


@pytest.mark.web
@pytest.mark.a11y
def test_OH_A11Y_001_login_inputs_have_placeholders_as_labels(page, orangehrm_base_url):
    # OrangeHRM is a Vue SPA — inputs use placeholder text as visible labels, no <label for>
    # navigate() waits for domcontentloaded; networkidle ensures Vue components are rendered
    LoginPage(page, orangehrm_base_url).navigate_to_login()
    page.wait_for_load_state("networkidle")
    for placeholder in ("Username", "Password"):
        inp = page.get_by_placeholder(placeholder)
        assert inp.count() >= 1, f"No input with placeholder '{placeholder}' found"


@pytest.mark.web
@pytest.mark.a11y
def test_OH_A11Y_002_login_page_has_brand_or_title(page, orangehrm_base_url):
    LoginPage(page, orangehrm_base_url).navigate_to_login()
    page.wait_for_load_state("networkidle")
    # OrangeHRM login uses an img logo — no standard <h1>
    has_title = page.title() != ""
    has_logo = page.locator("img").count() > 0
    assert has_title or has_logo, "Login page has neither a page title nor a logo image"


@pytest.mark.web
@pytest.mark.a11y
def test_OH_A11Y_003_login_form_reachable_by_keyboard(page, orangehrm_base_url):
    LoginPage(page, orangehrm_base_url).navigate_to_login()
    page.wait_for_load_state("networkidle")
    page.locator("body").click()  # trigger browser focus on the document before tabbing
    page.keyboard.press("Tab")
    focused_tag = page.evaluate("document.activeElement.tagName")
    assert focused_tag in ("INPUT", "BUTTON", "A", "SELECT", "TEXTAREA"), \
        f"Tab key did not focus a form element; focused: {focused_tag}"


@pytest.mark.web
@pytest.mark.a11y
def test_OH_A11Y_004_login_page_images_have_alt_text(page, orangehrm_base_url):
    LoginPage(page, orangehrm_base_url).navigate_to_login()
    page.wait_for_load_state("networkidle")
    images = page.locator("img")
    count = images.count()
    for i in range(count):
        img = images.nth(i)
        alt = img.get_attribute("alt")
        src = img.get_attribute("src") or f"image[{i}]"
        assert alt is not None, f"Image missing alt attribute: {src}"


@pytest.mark.web
@pytest.mark.a11y
def test_OH_A11Y_005_login_error_is_visible_when_credentials_invalid(page, orangehrm_base_url):
    lp = LoginPage(page, orangehrm_base_url)
    lp.navigate_to_login()
    page.wait_for_load_state("networkidle")
    lp.login("baduser", "badpass")
    assert lp.is_error_displayed(), "Error message not visible for invalid credentials"
    error_locator = page.locator(".oxd-alert, [class*='alert'], [class*='error']").first
    assert error_locator.is_visible(), "Error element is in DOM but not visible"


@pytest.mark.web
@pytest.mark.a11y
def test_OH_A11Y_006_dashboard_nav_items_have_text(page, orangehrm_base_url, orangehrm_credentials):
    lp = LoginPage(page, orangehrm_base_url)
    lp.navigate_to_login()
    lp.login(orangehrm_credentials["username"], orangehrm_credentials["password"])
    assert lp.is_on_dashboard()
    page.wait_for_load_state("networkidle")
    # OrangeHRM sidebar uses .oxd-main-menu-item elements
    nav_items = page.locator(".oxd-main-menu-item")
    assert nav_items.count() > 0, "No nav items found on dashboard"
    for i in range(nav_items.count()):
        text = (nav_items.nth(i).inner_text() or "").strip()
        assert text, f"Nav item {i} has no visible text"
