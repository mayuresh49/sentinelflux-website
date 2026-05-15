import pytest
from pages.mobile.login_page import LoginPage

@pytest.mark.mobile
@pytest.mark.sanity
def test_admin_user_logs_in_with_valid_credentials_and_lands_on_dashboard(appium_driver):
    screen = LoginPage(appium_driver)
    screen.fill_username("Admin")
    screen.fill_password("admin123")
    screen.tap_login()
    assert "dashboard" in appium_driver.current_url

@pytest.mark.mobile
@pytest.mark.sanity
def test_ess_user_logs_in_and_sees_limited_navigation_menu(appium_driver):
    screen = LoginPage(appium_driver)
    screen.fill_username("Kris.Chapman")
    screen.fill_password("Admin123")
    screen.tap_login()
    assert "My Info" in screen.get_nav_menu_items()
    assert "Apply for leave" in screen.get_nav_menu_items()
    assert "View own leave balance" in screen.get_nav_menu_items()

@pytest.mark.mobile
@pytest.mark.regression
def test_wrong_password_shows_invalid_credentials_error(appium_driver):
    screen = LoginPage(appium_driver)
    screen.fill_username("Admin")
    screen.fill_password("wrongpassword")
    screen.tap_login()
    assert "Invalid credentials" == screen.get_error_message()

@pytest.mark.mobile
@pytest.mark.regression
def test_empty_username_shows_validation_error(appium_driver):
    screen = LoginPage(appium_driver)
    screen.fill_username("")
    screen.fill_password("admin123")
    screen.tap_login()
    assert "Username is required" in screen.get_error_message()

@pytest.mark.mobile
@pytest.mark.regression
def test_empty_password_shows_validation_error(appium_driver):
    screen = LoginPage(appium_driver)
    screen.fill_username("Admin")
    screen.fill_password("")
    screen.tap_login()
    assert "Password is required" in screen.get_error_message()

@pytest.mark.mobile
@pytest.mark.regression
def test_both_fields_empty_shows_validation_error(appium_driver):
    screen = LoginPage(appium_driver)
    screen.fill_username("")
    screen.fill_password("")
    screen.tap_login()
    assert "Both fields are required" in screen.get_error_message()

@pytest.mark.mobile
@pytest.mark.security
def test_sql_injection_in_username_shows_error_not_500(appium_driver):
    screen = LoginPage(appium_driver)
    screen.fill_username("' OR '1'='1")
    screen.fill_password("admin123")
    screen.tap_login()
    assert "error" in screen.get_error_message().lower()
    assert 500 != appium_driver.status_code

@pytest.mark.mobile
@pytest.mark.regression
def test_username_is_case_sensitive(appium_driver):
    screen = LoginPage(appium_driver)
    screen.fill_username("admin")
    screen.fill_password("admin123")
    screen.tap_login()
    assert "Invalid credentials" == screen.get_error_message()

@pytest.mark.mobile
@pytest.mark.security
def test_browser_back_button_after_login_does_not_expose_session(appium_driver):
    screen = LoginPage(appium_driver)
    screen.fill_username("Admin")
    screen.fill_password("admin123")
    screen.tap_login()
    appium_driver.back()
    assert "login" in appium_driver.current_url or "session expired" in screen.get_error_message()

@pytest.mark.mobile
@pytest.mark.regression
def test_session_expires_after_inactivity(appium_driver):
    # Note: This test requires waiting for the session to expire, which can be time-consuming.
    # Implementing a sleep or polling mechanism is necessary here.
    screen = LoginPage(appium_driver)
    screen.fill_username("Admin")
    screen.fill_password("admin123")
    screen.tap_login()
    appium_driver.sleep(1800)  # Wait for 30 minutes
    assert "login" in appium_driver.current_url or "session expired" in screen.get_error_message()