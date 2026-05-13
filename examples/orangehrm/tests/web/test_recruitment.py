import pytest
from pages.web.login_page import LoginPage
from pages.web.recruitment_job_vacancies import RecruitmentJobVacanciesPage


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
def test_OH_WEB_031_vacancies_list_loads_with_active_vacancies(logged_in_page):
    rjv = RecruitmentJobVacanciesPage(logged_in_page)
    rjv.navigate_to_job_vacancies()
    assert rjv.is_table_displaying_active_vacancies()


@pytest.mark.web
def test_OH_WEB_032_filter_by_job_title_narrows_vacancy_list(logged_in_page):
    rjv = RecruitmentJobVacanciesPage(logged_in_page)
    rjv.navigate_to_job_vacancies()
    rjv.filter_by_job_title("Software Engineer")
    assert rjv.is_table_displaying_only_filtered_vacancies("Software Engineer")


@pytest.mark.web
def test_OH_WEB_033_filter_by_status_active_shows_only_active_vacancies(logged_in_page):
    rjv = RecruitmentJobVacanciesPage(logged_in_page)
    rjv.navigate_to_job_vacancies()
    rjv.filter_by_status("Active")
    assert rjv.is_table_displaying_only_active_vacancies()


@pytest.mark.web
def test_OH_WEB_034_clicking_add_navigates_to_add_vacancy_form(logged_in_page):
    rjv = RecruitmentJobVacanciesPage(logged_in_page)
    rjv.navigate_to_job_vacancies()
    rjv.click_add_button()
    assert rjv.is_on_add_vacancy_page()


@pytest.mark.web
def test_OH_WEB_035_filter_no_matching_criteria_shows_no_records(logged_in_page):
    rjv = RecruitmentJobVacanciesPage(logged_in_page)
    rjv.navigate_to_job_vacancies()
    rjv.filter_by_job_title("NonExistentJobTitle")
    assert rjv.is_table_displaying_no_records_found()
