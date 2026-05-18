import pytest
from products.orangehrm.pages.mobile.login_screen import LoginScreen


@pytest.mark.mobile
@pytest.mark.sanity
def test_OH_MOB_017_admin_logs_in_successfully(appium_driver, orangehrm_credentials):
    login_screen = LoginScreen(appium_driver)
    login_screen.fill_username(orangehrm_credentials["username"])
    login_screen.fill_password(orangehrm_credentials["password"])
    login_screen.tap_login()
    assert "dashboard" in appium_driver.current_url.lower()


@pytest.mark.mobile
@pytest.mark.sanity
def test_OH_MOB_018_ess_logs_in_successfully(appium_driver, orangehrm_ess_credentials):
    login_screen = LoginScreen(appium_driver)
    login_screen.fill_username(orangehrm_ess_credentials["username"])
    login_screen.fill_password(orangehrm_ess_credentials["password"])
    login_screen.tap_login()
    assert "dashboard" in appium_driver.current_url.lower()


@pytest.mark.mobile
@pytest.mark.regression
def test_OH_MOB_019_wrong_password_shows_invalid_credentials(appium_driver, orangehrm_credentials):
    login_screen = LoginScreen(appium_driver)
    login_screen.fill_username(orangehrm_credentials["username"])
    login_screen.fill_password("wrong_password_intentional")
    login_screen.tap_login()
    assert "Invalid credentials" in login_screen.get_error_message()


@pytest.mark.mobile
@pytest.mark.regression
def test_OH_MOB_020_empty_username_shows_validation_error(appium_driver, orangehrm_credentials):
    login_screen = LoginScreen(appium_driver)
    login_screen.fill_password(orangehrm_credentials["password"])
    login_screen.tap_login()
    assert "Username is required" in login_screen.get_error_message()


@pytest.mark.mobile
@pytest.mark.regression
def test_OH_MOB_021_empty_password_shows_validation_error(appium_driver, orangehrm_credentials):
    login_screen = LoginScreen(appium_driver)
    login_screen.fill_username(orangehrm_credentials["username"])
    login_screen.tap_login()
    assert "Password is required" in login_screen.get_error_message()


@pytest.mark.mobile
@pytest.mark.regression
def test_OH_MOB_022_both_fields_empty_shows_validation_error(appium_driver):
    login_screen = LoginScreen(appium_driver)
    login_screen.tap_login()
    error = login_screen.get_error_message()
    assert "required" in error.lower()


@pytest.mark.mobile
@pytest.mark.security
def test_OH_MOB_023_sql_injection_username_shows_error(appium_driver, orangehrm_credentials):
    login_screen = LoginScreen(appium_driver)
    login_screen.fill_username("' OR '1'='1")
    login_screen.fill_password(orangehrm_credentials["password"])
    login_screen.tap_login()
    assert "Invalid credentials" in login_screen.get_error_message()


@pytest.mark.mobile
@pytest.mark.regression
def test_OH_MOB_024_username_is_case_sensitive(appium_driver, orangehrm_credentials):
    login_screen = LoginScreen(appium_driver)
    login_screen.fill_username(orangehrm_credentials["username"].lower())
    login_screen.fill_password(orangehrm_credentials["password"])
    login_screen.tap_login()
    assert "Invalid credentials" in login_screen.get_error_message()


@pytest.mark.mobile
@pytest.mark.edge
def test_OH_MOB_025_back_button_after_login_redirects_to_login(appium_driver, orangehrm_credentials):
    login_screen = LoginScreen(appium_driver)
    login_screen.fill_username(orangehrm_credentials["username"])
    login_screen.fill_password(orangehrm_credentials["password"])
    login_screen.tap_login()
    appium_driver.back()
    assert "login" in appium_driver.current_url.lower()


@pytest.mark.mobile
@pytest.mark.edge
@pytest.mark.skip(reason="session timeout requires 15-minute wait — not suitable for automated run")
def test_OH_MOB_026_session_expires_after_inactivity(appium_driver, orangehrm_credentials):
    login_screen = LoginScreen(appium_driver)
    login_screen.fill_username(orangehrm_credentials["username"])
    login_screen.fill_password(orangehrm_credentials["password"])
    login_screen.tap_login()
    assert "login" in appium_driver.current_url.lower()
