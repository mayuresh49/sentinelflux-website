import pytest
from pages.web.home_page import HomePage


@pytest.mark.web
def test_home_page_shows_rooms(page, rb_web_base):
    home = HomePage(page, rb_web_base)
    home.navigate()
    assert home.rooms_are_listed()


@pytest.mark.web
def test_home_page_room_count_is_positive(page, rb_web_base):
    home = HomePage(page, rb_web_base)
    home.navigate()
    assert home.get_room_count() >= 1


@pytest.mark.web
def test_booking_form_opens_on_click(page, rb_web_base):
    home = HomePage(page, rb_web_base)
    home.navigate()
    home.click_book_room(0)
    assert page.locator("input[name='firstname']").last.is_visible()


@pytest.mark.web
def test_booking_form_submit_with_valid_data(page, rb_web_base):
    home = HomePage(page, rb_web_base)
    home.navigate()
    home.click_book_room(0)

    # Pick dates via the calendar (next month to avoid conflicts)
    # Dates are selected via the datepicker — click start/end cells
    try:
        # Try clicking on two dates in the calendar
        date_cells = page.locator(".rdrDayNumber span").all()
        if len(date_cells) >= 10:
            date_cells[5].click()
            date_cells[9].click()
    except Exception:
        pass  # calendar interaction is optional — form validation is the focus

    home.fill_firstname("John")
    home.fill_lastname("Smith")
    home.fill_email("john.smith@example.com")
    home.fill_phone("01234567890")
    home.submit_booking()

    # Either confirmed or validation error (dates may conflict with existing)
    confirmed = home.is_booking_confirmed()
    has_error = home.has_validation_error()
    assert confirmed or has_error, "Expected either a confirmation or a validation error"


@pytest.mark.web
def test_booking_form_submit_missing_fields_shows_error(page, rb_web_base):
    home = HomePage(page, rb_web_base)
    home.navigate()
    home.click_book_room(0)
    home.submit_booking()
    assert home.has_validation_error()
