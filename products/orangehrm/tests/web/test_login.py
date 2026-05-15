import pytest
from pages.web.login_page import LoginPage


@pytest.mark.web
def test_OH_WEB_001_valid_admin_login_redirects_to_dashboard(page, orangehrm_base_url, orangehrm_credentials):
    login_page = LoginPage(page, orangehrm_base_url)
    login_page.navigate_to_login()
    login_page.login(orangehrm_credentials["username"], orangehrm_credentials["password"])
    assert login_page.is_on_dashboard()


@pytest.mark.web
def test_OH_WEB_002_wrong_password_shows_error(page, orangehrm_base_url, orangehrm_credentials):
    login_page = LoginPage(page, orangehrm_base_url)
    login_page.navigate_to_login()
    login_page.login(orangehrm_credentials["username"], "wrongpassword")
    assert login_page.is_error_displayed()
    assert not login_page.is_on_dashboard()


@pytest.mark.web
def test_OH_WEB_003_wrong_username_shows_error(page, orangehrm_base_url, orangehrm_credentials):
    login_page = LoginPage(page, orangehrm_base_url)
    login_page.navigate_to_login()
    login_page.login("nonexistentuser", orangehrm_credentials["password"])
    assert login_page.is_error_displayed()
    assert not login_page.is_on_dashboard()


@pytest.mark.web
def test_OH_WEB_004_empty_username_shows_error(page, orangehrm_base_url, orangehrm_credentials):
    login_page = LoginPage(page, orangehrm_base_url)
    login_page.navigate_to_login()
    login_page.login("", orangehrm_credentials["password"])
    assert login_page.is_error_displayed()


@pytest.mark.web
def test_OH_WEB_005_empty_password_shows_error(page, orangehrm_base_url, orangehrm_credentials):
    login_page = LoginPage(page, orangehrm_base_url)
    login_page.navigate_to_login()
    login_page.login(orangehrm_credentials["username"], "")
    assert login_page.is_error_displayed()


@pytest.mark.web
def test_OH_WEB_006_both_fields_empty_shows_error(page, orangehrm_base_url):
    login_page = LoginPage(page, orangehrm_base_url)
    login_page.navigate_to_login()
    login_page.login("", "")
    assert login_page.is_error_displayed()


@pytest.mark.web
@pytest.mark.xfail(
    reason="OrangeHRM demo site has a separate 'admin' (lowercase) user — case-sensitivity "
           "cannot be verified on the public demo; passes on a fresh OrangeHRM instance",
    strict=False,
)
def test_OH_WEB_007_username_is_case_sensitive(page, orangehrm_base_url, orangehrm_credentials):
    login_page = LoginPage(page, orangehrm_base_url)
    login_page.navigate_to_login()
    login_page.login("admin", orangehrm_credentials["password"])
    assert login_page.is_error_displayed()
    assert not login_page.is_on_dashboard()


@pytest.mark.web
def test_OH_WEB_008_sql_injection_in_username_does_not_crash(page, orangehrm_base_url, orangehrm_credentials):
    login_page = LoginPage(page, orangehrm_base_url)
    login_page.navigate_to_login()
    login_page.login("' OR '1'='1", orangehrm_credentials["password"])
    assert login_page.is_error_displayed()
    assert not login_page.is_on_dashboard()
