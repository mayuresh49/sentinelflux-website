import pytest
from pages.web.login_page import LoginPage
from pages.web.admin_users_page import AdminUsersPage

ADMIN_USER = "Admin"
ADMIN_PASS = "admin123"


@pytest.fixture(scope="function")
def logged_in_page(page, session_authed_page):
    """Authenticated page. Uses shared session if --session-login is active."""
    if session_authed_page is not None:
        return session_authed_page
    login_page = LoginPage(page)
    login_page.navigate_to_login()
    login_page.login(ADMIN_USER, ADMIN_PASS)
    assert login_page.is_on_dashboard()
    return page


@pytest.mark.web
def test_user_list_loads_on_navigation(logged_in_page):
    admin = AdminUsersPage(logged_in_page)
    admin.navigate_to_list()
    assert admin.is_on_list_page()


@pytest.mark.web
def test_user_list_shows_record_count(logged_in_page):
    admin = AdminUsersPage(logged_in_page)
    admin.navigate_to_list()
    assert "Record" in admin.get_record_count_text()


@pytest.mark.web
def test_search_by_admin_username_filters_results(logged_in_page):
    admin = AdminUsersPage(logged_in_page)
    admin.navigate_to_list()
    admin.search_by_username("Admin")
    assert "Record" in admin.get_record_count_text()


@pytest.mark.web
def test_search_with_nonexistent_username_shows_no_records(logged_in_page):
    admin = AdminUsersPage(logged_in_page)
    admin.navigate_to_list()
    admin.search_by_username("ZZZnonexistentXXX999")
    assert admin.is_no_records_shown()


@pytest.mark.web
def test_cancel_returns_to_list(logged_in_page):
    admin = AdminUsersPage(logged_in_page)
    admin.navigate_to_add()
    admin.cancel()
    assert admin.is_on_list_page()


@pytest.mark.web
@pytest.mark.xfail(strict=False, reason="Demo site add-user form requires employee lookup which may time out")
def test_save_without_username_shows_validation_error(logged_in_page):
    admin = AdminUsersPage(logged_in_page)
    admin.navigate_to_add()
    admin.select_user_role("Admin")
    admin.select_status("Enabled")
    admin.fill_employee_name("Admin")
    admin.fill_password("Admin1234!")
    admin.fill_confirm_password("Admin1234!")
    # deliberately skip fill_username
    admin.save()
    assert admin.is_validation_error_shown()


@pytest.mark.web
@pytest.mark.xfail(strict=False, reason="Demo site add-user form requires employee lookup which may time out")
def test_save_without_password_shows_validation_error(logged_in_page):
    admin = AdminUsersPage(logged_in_page)
    admin.navigate_to_add()
    admin.select_user_role("Admin")
    admin.select_status("Enabled")
    admin.fill_employee_name("Admin")
    admin.fill_username("testuser_nopwd_99")
    # deliberately skip fill_password / fill_confirm_password
    admin.save()
    assert admin.is_validation_error_shown()
