import pytest


@pytest.mark.mobile
def test_create_booking_shows_confirmation(booking_screen):
    booking_screen.create_booking(
        firstname="John",
        lastname="Doe",
        total_price=150.0,
        checkin="2026-06-01",
        checkout="2026-06-05",
        deposit_paid=True,
    )
    assert booking_screen.is_confirmed()


@pytest.mark.mobile
def test_create_booking_without_firstname_shows_error(booking_screen):
    booking_screen.fill_lastname("Doe")
    booking_screen.fill_total_price("150")
    booking_screen.fill_checkin("2026-06-01")
    booking_screen.fill_checkout("2026-06-05")
    booking_screen.submit()
    assert booking_screen.is_error_shown()


@pytest.mark.mobile
def test_create_booking_without_lastname_shows_error(booking_screen):
    booking_screen.fill_firstname("John")
    booking_screen.fill_total_price("150")
    booking_screen.fill_checkin("2026-06-01")
    booking_screen.fill_checkout("2026-06-05")
    booking_screen.submit()
    assert booking_screen.is_error_shown()


@pytest.mark.mobile
def test_checkout_before_checkin_shows_error(booking_screen):
    booking_screen.create_booking(
        firstname="John",
        lastname="Doe",
        total_price=100.0,
        checkin="2026-06-10",
        checkout="2026-06-05",
    )
    assert booking_screen.is_error_shown()


@pytest.mark.mobile
def test_booking_list_is_visible_on_home(booking_screen):
    assert booking_screen.is_booking_list_visible()


@pytest.mark.mobile
@pytest.mark.parametrize("firstname,lastname,price,checkin,checkout", [
    ("Alice", "Smith", 200.0, "2026-07-01", "2026-07-03"),
    ("Bob", "Jones", 99.0, "2026-08-15", "2026-08-16"),
])
def test_create_booking_parametrized(booking_screen, firstname, lastname, price, checkin, checkout):
    booking_screen.create_booking(
        firstname=firstname,
        lastname=lastname,
        total_price=price,
        checkin=checkin,
        checkout=checkout,
    )
    assert booking_screen.is_confirmed()
