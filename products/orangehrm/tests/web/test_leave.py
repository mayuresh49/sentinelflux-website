import pytest
from pages.web.leave_page import LeavePage
from products.orangehrm.pages.web.login_page import LoginPage

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
def test_OH_WEB_124_leave_list_loads_with_current_period(logged_in_page, orangehrm_base_url):
    leave = LeavePage(logged_in_page, orangehrm_base_url)
    leave.navigate_to_list()
    assert leave.is_within_current_period()

@pytest.mark.web
@pytest.mark.regression
def test_OH_WEB_125_filter_by_date_range_narrows_results(logged_in_page, orangehrm_base_url):
    leave = LeavePage(logged_in_page, orangehrm_base_url)
    leave.navigate_to_list()
    leave.filter_by_date("2023-01-01", "2023-01-31")
    assert leave.are_requests_within_date_range("2023-01-01", "2023-01-31")

@pytest.mark.web
@pytest.mark.sanity
def test_OH_WEB_126_admin_can_approve_pending_leave_request(logged_in_page, orangehrm_base_url):
    leave = LeavePage(logged_in_page, orangehrm_base_url)
    leave.navigate_to_list()
    leave.approve_leave_request("12345")
    assert leave.is_status_approved("12345")
    assert leave.is_success_message_displayed("Leave request approved successfully.")

@pytest.mark.web
@pytest.mark.sanity
def test_OH_WEB_127_admin_can_reject_pending_leave_request(logged_in_page, orangehrm_base_url):
    leave = LeavePage(logged_in_page, orangehrm_base_url)
    leave.navigate_to_list()
    leave.reject_leave_request("12345")
    assert leave.is_status_rejected("12345")
    assert leave.is_success_message_displayed("Leave request rejected successfully.")

@pytest.mark.web
@pytest.mark.regression
def test_OH_WEB_128_date_to_before_date_from_validation(logged_in_page, orangehrm_base_url):
    leave = LeavePage(logged_in_page, orangehrm_base_url)
    leave.navigate_to_list()
    leave.filter_by_date("2023-01-31", "2023-01-01")
    assert leave.is_validation_error_displayed("Date To must be on or after Date From") or leave.are_no_results_displayed()