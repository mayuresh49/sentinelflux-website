import pytest
from pages.web.login_page import LoginPage

ADMIN_USER = "Admin"
ADMIN_PASS = "admin123"


@pytest.mark.web
def test_valid_admin_login_redirects_to_dashboard(page):
    login_page = LoginPage(page)
    login_page.navigate_to_login()
    login_page.login(ADMIN_USER, ADMIN_PASS)
    assert login_page.is_on_dashboard()


@pytest.mark.web
def test_wrong_password_shows_error(page):
    login_page = LoginPage(page)
    login_page.navigate_to_login()
    login_page.login(ADMIN_USER, "wrongpassword")
    assert login_page.is_error_displayed()
    assert not login_page.is_on_dashboard()


@pytest.mark.web
def test_wrong_username_shows_error(page):
    login_page = LoginPage(page)
    login_page.navigate_to_login()
    login_page.login("nonexistentuser", ADMIN_PASS)
    assert login_page.is_error_displayed()
    assert not login_page.is_on_dashboard()


@pytest.mark.web
def test_empty_username_shows_error(page):
    login_page = LoginPage(page)
    login_page.navigate_to_login()
    login_page.login("", ADMIN_PASS)
    assert login_page.is_error_displayed()


@pytest.mark.web
def test_empty_password_shows_error(page):
    login_page = LoginPage(page)
    login_page.navigate_to_login()
    login_page.login(ADMIN_USER, "")
    assert login_page.is_error_displayed()


@pytest.mark.web
def test_both_fields_empty_shows_error(page):
    login_page = LoginPage(page)
    login_page.navigate_to_login()
    login_page.login("", "")
    assert login_page.is_error_displayed()


@pytest.mark.web
@pytest.mark.xfail(
    reason="OrangeHRM demo site has a separate 'admin' (lowercase) user — case-sensitivity "
           "cannot be verified on the public demo; passes on a fresh OrangeHRM instance",
    strict=False,
)
def test_username_is_case_sensitive(page):
    login_page = LoginPage(page)
    login_page.navigate_to_login()
    login_page.login("admin", ADMIN_PASS)
    assert login_page.is_error_displayed()
    assert not login_page.is_on_dashboard()


@pytest.mark.web
def test_sql_injection_in_username_does_not_crash(page):
    login_page = LoginPage(page)
    login_page.navigate_to_login()
    login_page.login("' OR '1'='1", ADMIN_PASS)
    assert login_page.is_error_displayed()
    assert not login_page.is_on_dashboard()
