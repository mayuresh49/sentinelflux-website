import pytest
from pages.web.login_page import LoginPage

@pytest.fixture(scope="function")
def logged_in_page(page, session_authed_page, orangehrm_base_url, orangehrm_credentials):
    if session_authed_page is not None:
        return session_authed_page
    lp = LoginPage(page, orangehrm_base_url)
    lp.navigate_to_login()
    lp.login(orangehrm_credentials["username"], orangehrm_credentials["password"])
    assert lp.is_on_dashboard()
    return page

@pytest.mark.web
@pytest.mark.sanity
def test_admin_user_logs_in_with_valid_credentials_and_lands_on_dashboard(logged_in_page, orangehrm_base_url):
    # No specific page object needed for this test case as it is about landing on dashboard
    pass

@pytest.fixture(scope="function")
def logged_in_ess_page(page, session_authed_page, orangehrm_base_url, ess_credentials):
    if session_authed_page is not None:
        return session_authed_page
    lp = LoginPage(page, orangehrm_base_url)
    lp.navigate_to_login()
    lp.login(ess_credentials["username"], ess_credentials["password"])
    assert lp.is_on_limited_navigation_menu()
    return page

@pytest.mark.web
@pytest.mark.regression
def test_ess_user_logs_in_and_sees_limited_navigation_menu(logged_in_ess_page, orangehrm_base_url):
    # No specific page object needed for this test case as it is about limited navigation menu
    pass

@pytest.mark.web
@pytest.mark.negative
def test_wrong_password_shows_invalid_credentials_error(page, orangehrm_base_url, orangehrm_credentials):
    lp = LoginPage(page, orangehrm_base_url)
    lp.navigate_to_login()
    lp.login(orangehrm_credentials["username"], "wrong_password")
    assert lp.is_error_message_displayed("Invalid credentials")

@pytest.mark.web
@pytest.mark.negative
def test_empty_username_shows_validation_error(page, orangehrm_base_url, orangehrm_credentials):
    lp = LoginPage(page, orangehrm_base_url)
    lp.navigate_to_login()
    lp.login("", orangehrm_credentials["password"])
    assert lp.is_username_field_error_displayed()

@pytest.mark.web
@pytest.mark.negative
def test_empty_password_shows_validation_error(page, orangehrm_base_url, orangehrm_credentials):
    lp = LoginPage(page, orangehrm_base_url)
    lp.navigate_to_login()
    lp.login(orangehrm_credentials["username"], "")
    assert lp.is_password_field_error_displayed()

@pytest.mark.web
@pytest.mark.negative
def test_sql_injection_in_username_shows_error_not_500(page, orangehrm_base_url, orangehrm_credentials):
    lp = LoginPage(page, orangehrm_base_url)
    lp.navigate_to_login()
    lp.login("Admin'; DROP TABLE users; --", orangehrm_credentials["password"])
    assert lp.is_error_message_displayed("Invalid credentials")

@pytest.mark.web
@pytest.mark.regression
def test_username_is_case_sensitive(page, orangehrm_base_url, orangehrm_credentials):
    lp = LoginPage(page, orangehrm_base_url)
    lp.navigate_to_login()
    lp.login("admin", orangehrm_credentials["password"])
    assert lp.is_error_message_displayed("Invalid credentials")

# Security tests are typically not automated in the same way as functional tests
# and would require a deep understanding of the application's codebase.
# They are usually performed manually or through penetration testing tools.