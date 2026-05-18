import pytest
from pages.web.login_page import LoginPage
from products.orangehrm.pages.web.timesheets import TimesheetsPage


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
def test_OH_WEB_072_authenticated_user_can_access_timesheets_form(logged_in_page, orangehrm_base_url):
    timesheets = TimesheetsPage(logged_in_page, orangehrm_base_url)
    timesheets.navigate_to_timesheets()
    assert timesheets.is_on_timesheets_form()


@pytest.mark.web
@pytest.mark.sanity
def test_OH_WEB_073_valid_timesheet_submitted_with_all_required_fields(logged_in_page, orangehrm_base_url):
    timesheets = TimesheetsPage(logged_in_page, orangehrm_base_url)
    timesheets.navigate_to_timesheets()
    timesheets.fill_timesheet(employee_id="12345", from_date="2023-01-01", to_date="2023-01-07", hours_worked="40")
    assert timesheets.is_submission_successful()


@pytest.mark.web
@pytest.mark.regression
def test_OH_WEB_074_missing_employee_id_and_hours_worked_shows_validation_errors(logged_in_page, orangehrm_base_url):
    timesheets = TimesheetsPage(logged_in_page, orangehrm_base_url)
    timesheets.navigate_to_timesheets()
    timesheets.fill_timesheet(from_date="2023-01-01", to_date="2023-01-07")
    assert timesheets.has_validation_error_for_employee_id()
    assert timesheets.has_validation_error_for_hours_worked()


@pytest.mark.web
@pytest.mark.regression
def test_OH_WEB_075_excessive_hours_worked_value_shows_validation_error(logged_in_page, orangehrm_base_url):
    timesheets = TimesheetsPage(logged_in_page, orangehrm_base_url)
    timesheets.navigate_to_timesheets()
    timesheets.fill_timesheet(employee_id="12345", from_date="2023-01-01", to_date="2023-01-07", hours_worked="999")
    assert timesheets.has_validation_error_for_hours_worked()


@pytest.mark.web
@pytest.mark.regression
def test_OH_WEB_076_empty_from_date_shows_validation_error(logged_in_page, orangehrm_base_url):
    timesheets = TimesheetsPage(logged_in_page, orangehrm_base_url)
    timesheets.navigate_to_timesheets()
    timesheets.fill_timesheet(employee_id="12345", from_date="", to_date="2023-01-07")
    assert timesheets.has_validation_error_for_from_date()


@pytest.mark.web
@pytest.mark.regression
def test_OH_WEB_077_duplicate_employee_id_for_same_period_shows_conflict_error(logged_in_page, orangehrm_base_url):
    timesheets = TimesheetsPage(logged_in_page, orangehrm_base_url)
    timesheets.navigate_to_timesheets()
    timesheets.fill_timesheet(employee_id="12345", from_date="2023-01-01", to_date="2023-01-07", hours_worked="40")
    assert timesheets.has_duplicate_entry_error()


@pytest.mark.web
@pytest.mark.regression
def test_OH_WEB_078_session_expires_after_inactivity_timeout(logged_in_page, orangehrm_base_url):
    # Stub: requires session timeout simulation setup
    pass


@pytest.mark.web
@pytest.mark.regression
def test_OH_WEB_079_password_complexity_rules_enforced(logged_in_page, orangehrm_base_url):
    # Stub: requires password-change page navigation setup
    pass


@pytest.mark.web
@pytest.mark.regression
def test_OH_WEB_080_admin_cannot_delete_their_own_account(logged_in_page, orangehrm_base_url):
    # Stub: requires admin account management page navigation setup
    pass


@pytest.mark.web
@pytest.mark.regression
def test_OH_WEB_081_ess_user_can_only_edit_their_own_profile(page, orangehrm_base_url, orangehrm_credentials):
    # Stub: requires ESS permission and cross-profile access test setup
    pass


@pytest.mark.web
@pytest.mark.sanity
def test_OH_WEB_082_supervisor_can_view_direct_reports_timesheets(logged_in_page, orangehrm_base_url):
    # Stub: requires supervisor role assignment and direct report data setup
    pass
