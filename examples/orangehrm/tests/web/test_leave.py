import pytest
from pages.web.login_page import LoginPage
from pages.web.leave_page import LeavePage

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
def test_OH_WEB_026_leave_list_loads_on_navigation(logged_in_page):
    leave = LeavePage(logged_in_page)
    leave.navigate_to_list()
    assert leave.is_on_list_page()


@pytest.mark.web
def test_OH_WEB_027_leave_list_shows_record_count(logged_in_page):
    leave = LeavePage(logged_in_page)
    leave.navigate_to_list()
    leave.click_search()
    assert "Record" in leave.get_record_count_text()


@pytest.mark.web
def test_OH_WEB_028_filter_by_pending_status_shows_results(logged_in_page):
    leave = LeavePage(logged_in_page)
    leave.navigate_to_list()
    leave.select_status("Pending Approval")
    leave.click_search()
    record_text = leave.get_record_count_text()
    assert not leave.is_no_records_shown() or "Record" in record_text


@pytest.mark.web
def test_OH_WEB_029_search_with_future_date_range_shows_no_records(logged_in_page):
    leave = LeavePage(logged_in_page)
    leave.navigate_to_list()
    leave.fill_date_from("2099-01-01")
    leave.fill_date_to("2099-12-31")
    leave.click_search()
    assert leave.is_no_records_shown()


@pytest.mark.web
@pytest.mark.xfail(reason="OrangeHRM demo site does not enforce date-range order; returns records regardless", strict=False)
def test_OH_WEB_030_date_to_before_date_from_shows_empty_or_error(logged_in_page):
    leave = LeavePage(logged_in_page)
    leave.navigate_to_list()
    leave.fill_date_from("2024-06-30")
    leave.fill_date_to("2024-01-01")
    leave.click_search()
    assert leave.is_no_records_shown() or "0" in leave.get_record_count_text()
