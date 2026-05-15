import random

import pytest
from pages.web.login_page import LoginPage
from pages.web.pim_employee_page import PIMEmployeePage

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
def test_OH_WEB_009_employee_list_loads_on_navigation(logged_in_page):
    pim = PIMEmployeePage(logged_in_page)
    pim.navigate_to_list()
    assert pim.is_on_list_page()
    assert "Records Found" in pim.get_record_count_text()


@pytest.mark.web
def test_OH_WEB_010_add_employee_with_required_fields_only(logged_in_page):
    pim = PIMEmployeePage(logged_in_page)
    pim.navigate_to_add()
    pim.fill_firstname("Test")
    pim.fill_lastname("User")
    pim.save()
    assert pim.is_success_shown() or pim.is_on_profile_page()


@pytest.mark.web
def test_OH_WEB_011_add_employee_with_all_fields(logged_in_page):
    pim = PIMEmployeePage(logged_in_page)
    pim.navigate_to_add()
    pim.fill_firstname("John")
    pim.fill_middlename("Robert")
    pim.fill_lastname("Doe")
    pim.fill_employee_id(f"EMP-{random.randint(10000, 99999)}")
    pim.save()
    assert pim.is_success_shown() or pim.is_on_profile_page()


@pytest.mark.web
def test_OH_WEB_012_save_without_firstname_shows_validation_error(logged_in_page):
    pim = PIMEmployeePage(logged_in_page)
    pim.navigate_to_add()
    pim.fill_lastname("Doe")
    pim.save()
    assert pim.is_validation_error_shown()


@pytest.mark.web
def test_OH_WEB_013_save_without_lastname_shows_validation_error(logged_in_page):
    pim = PIMEmployeePage(logged_in_page)
    pim.navigate_to_add()
    pim.fill_firstname("John")
    pim.save()
    assert pim.is_validation_error_shown()


@pytest.mark.web
def test_OH_WEB_014_firstname_exceeding_30_chars_shows_validation_error(logged_in_page):
    pim = PIMEmployeePage(logged_in_page)
    pim.navigate_to_add()
    pim.fill_firstname("A" * 31)
    pim.fill_lastname("Doe")
    pim.save()
    assert pim.is_validation_error_shown()


@pytest.mark.web
def test_OH_WEB_015_cancel_returns_to_list_without_saving(logged_in_page):
    pim = PIMEmployeePage(logged_in_page)
    pim.navigate_to_add()
    pim.fill_firstname("ShouldNotSave")
    pim.fill_lastname("Test")
    pim.cancel()
    assert pim.is_on_list_page()


@pytest.mark.web
def test_OH_WEB_016_search_by_name_filters_results(logged_in_page):
    pim = PIMEmployeePage(logged_in_page)
    pim.navigate_to_list()
    pim.search_by_name("Admin")
    assert "Records Found" in pim.get_record_count_text()


@pytest.mark.web
@pytest.mark.xfail(reason="OrangeHRM demo has shared data; nonexistent name search may still return results", strict=False)
def test_OH_WEB_017_search_with_nonexistent_name_shows_no_records(logged_in_page):
    pim = PIMEmployeePage(logged_in_page)
    pim.navigate_to_list()
    pim.search_by_name("ZZZnonexistentXXX")
    assert pim.is_no_records_shown()


@pytest.mark.web
@pytest.mark.parametrize("firstname,lastname", [
    ("Alice", "Smith"),
    ("Bob", "Jones"),
])
def test_OH_WEB_018_add_employee_parametrized(logged_in_page, firstname, lastname):
    pim = PIMEmployeePage(logged_in_page)
    pim.navigate_to_add()
    pim.fill_firstname(firstname)
    pim.fill_lastname(lastname)
    pim.save()
    assert pim.is_success_shown() or pim.is_on_profile_page()
