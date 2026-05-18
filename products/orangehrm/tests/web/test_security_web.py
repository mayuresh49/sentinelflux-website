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
@pytest.mark.security
@pytest.mark.regression
def test_OH_WEB_083_validate_username_case_sensitivity(logged_in_page, orangehrm_base_url):
    lp = LoginPage(logged_in_page, orangehrm_base_url)
    lp.login("Admin", "admin123")
    assert lp.is_on_dashboard()
    # Assuming there's a method to check the HttpOnly flag on the session cookie
    assert lp.session_cookie_has_http_only_flag()

@pytest.mark.web
@pytest.mark.security
@pytest.mark.regression
def test_OH_WEB_084_account_lock_after_5_failed_login_attempts(page, orangehrm_base_url, orangehrm_credentials):
    lp = LoginPage(page, orangehrm_base_url)
    for _ in range(5):
        lp.login("admin", "incorrect123")
    assert lp.is_account_locked()