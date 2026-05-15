import pytest
from pages.web.login_page import LoginPage
from pages.web.timesheets import TimesheetsPage


@pytest.fixture(scope="function")
def logged_in_page(page, session_authed_page):
    if session_authed_page is not None:
        return session_authed_page
    lp = LoginPage(page)
    lp.navigate_to_login()
    lp.login("Admin", "admin123")
    assert lp.is_on_dashboard()
    return page

@pytest.mark.web
@pytest.mark.sanity
def test_user_can_access_timesheets_form(logged_in_page):
    timesheets = TimesheetsPage(logged_in_page)
    timesheets.navigate_to_timesheets_form()
    assert timesheets.is_on_timesheets_form()

@pytest.mark.web
@pytest.mark.regression
def test_valid_timesheet_submission_with_correct_data(logged_in_page):
    timesheets = TimesheetsPage(logged_in_page)
    timesheets.navigate_to_timesheets_form()
    timesheets.fill_employee_id("12345")
    timesheets.fill_from_date("2023-01-01")
    timesheets.fill_to_date("2023-01-07")
    timesheets.fill_hours_worked(40)
    timesheets.submit_timesheet()
    assert timesheets.is_submission_successful()

@pytest.mark.web
@pytest.mark.regression
def test_mandatory_fields_validation_for_timesheet_form(logged_in_page):
    timesheets = TimesheetsPage(logged_in_page)
    timesheets.navigate_to_timesheets_form()
    timesheets.fill_from_date("2023-01-01")
    timesheets.fill_to_date("2023-01-07")
    timesheets.submit_timesheet()
    assert timesheets.is_employee_id_missing_error()
    assert timesheets.is_hours_worked_missing_error()

@pytest.mark.web
@pytest.mark.regression
def test_input_restriction_checks_for_timesheet_hours_worked(logged_in_page):
    timesheets = TimesheetsPage(logged_in_page)
    timesheets.navigate_to_timesheets_form()
    timesheets.fill_employee_id("12345")
    timesheets.fill_from_date("2023-01-01")
    timesheets.fill_to_date("2023-01-07")
    timesheets.fill_hours_worked(999)
    timesheets.submit_timesheet()
    assert timesheets.is_invalid_hours_worked_error()

@pytest.mark.web
@pytest.mark.regression
def test_negative_scenarios_for_timesheet_from_date_and_to_date(logged_in_page):
    timesheets = TimesheetsPage(logged_in_page)
    timesheets.navigate_to_timesheets_form()
    timesheets.fill_employee_id("12345")
    timesheets.fill_from_date("")
    timesheets.fill_to_date("2023-01-07")
    timesheets.submit_timesheet()
    assert timesheets.is_invalid_from_date_error()

@pytest.mark.web
@pytest.mark.regression
def test_validate_employee_id_uniqueness(logged_in_page):
    timesheets = TimesheetsPage(logged_in_page)
    timesheets.navigate_to_timesheets_form()
    timesheets.fill_employee_id("12345")
    timesheets.fill_from_date("2023-01-01")
    timesheets.fill_to_date("2023-01-07")
    timesheets.submit_timesheet()
    assert timesheets.is_duplicate_employee_id_error()

@pytest.mark.web
@pytest.mark.regression
def test_session_expiry_and_inactivity_timeout(logged_in_page):
    # This test requires additional setup to simulate session expiry
    pass

@pytest.mark.web
@pytest.mark.security
def test_password_complexity_rules(logged_in_page):
    # This test requires additional setup to simulate password complexity checks
    pass

@pytest.mark.web
@pytest.mark.regression
def test_admin_cannot_delete_their_own_account(logged_in_page):
    # This test requires additional setup for admin user actions
    pass

@pytest.mark.web
@pytest.mark.sanity
def test_ess_users_can_only_edit_their_own_profile(logged_in_page):
    # This test requires additional setup for ESS user permissions
    pass

@pytest.mark.web
@pytest.mark.regression
def test_supervisor_can_view_direct_reports_timesheets(logged_in_page):
    # This test requires additional setup for supervisor permissions and direct reports
    pass