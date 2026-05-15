import pytest


@pytest.mark.mobile
def test_valid_login_navigates_to_dashboard(login_screen, orangehrm_credentials):
    login_screen.login(
        orangehrm_credentials["username"],
        orangehrm_credentials["password"],
    )
    assert login_screen.is_on_dashboard()


@pytest.mark.mobile
def test_invalid_password_shows_error(login_screen, orangehrm_credentials):
    login_screen.login(orangehrm_credentials["username"], "wrong_password")
    assert login_screen.is_error_shown()


@pytest.mark.mobile
def test_invalid_username_shows_error(login_screen):
    login_screen.login("nonexistent_user", "admin123")
    assert login_screen.is_error_shown()


@pytest.mark.mobile
def test_empty_username_shows_validation_error(login_screen, orangehrm_credentials):
    login_screen.fill_password(orangehrm_credentials["password"])
    login_screen.submit()
    assert login_screen.is_error_shown() or login_screen.is_username_error_shown()


@pytest.mark.mobile
def test_empty_password_shows_validation_error(login_screen, orangehrm_credentials):
    login_screen.fill_username(orangehrm_credentials["username"])
    login_screen.submit()
    assert login_screen.is_error_shown() or login_screen.is_password_error_shown()


@pytest.mark.mobile
def test_empty_credentials_shows_validation_error(login_screen):
    login_screen.submit()
    assert login_screen.is_error_shown() or login_screen.is_username_error_shown()
