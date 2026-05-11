import pytest
from utils.assertions import assert_status_code

VALID_BOOKING = {
    "firstname": "John",
    "lastname": "Doe",
    "totalprice": 100,
    "depositpaid": True,
    "bookingdates": {
        "checkin": "2026-09-01",
        "checkout": "2026-09-05",
    },
    "additionalneeds": "Breakfast included",
}


@pytest.mark.api
def test_create_booking_returns_200(booking_client):
    resp = booking_client.create_booking(VALID_BOOKING)
    assert_status_code(resp, 200)


@pytest.mark.api
def test_get_existing_booking_returns_200(booking_client):
    booking_id = booking_client.create_booking(VALID_BOOKING).json()["bookingid"]
    resp = booking_client.get_booking(booking_id)
    assert_status_code(resp, 200)


@pytest.mark.api
def test_update_existing_booking_returns_200(booking_client):
    booking_id = booking_client.create_booking(VALID_BOOKING).json()["bookingid"]
    updated = {**VALID_BOOKING, "firstname": "Jane", "totalprice": 150}
    resp = booking_client.update_booking(booking_id, updated)
    assert_status_code(resp, 200)


@pytest.mark.api
def test_delete_existing_booking_returns_success(booking_client):
    booking_id = booking_client.create_booking(VALID_BOOKING).json()["bookingid"]
    resp = booking_client.delete_booking(booking_id)
    assert resp.status_code in (200, 201)


@pytest.mark.api
def test_create_booking_missing_firstname_returns_error(booking_client):
    incomplete = {k: v for k, v in VALID_BOOKING.items() if k != "firstname"}
    resp = booking_client.create_booking(incomplete)
    assert resp.status_code in (400, 422, 500)


@pytest.mark.api
def test_create_booking_invalid_totalprice_type_returns_error(booking_client):
    payload = {**VALID_BOOKING, "totalprice": "not-a-number"}
    resp = booking_client.create_booking(payload)
    assert resp.status_code in (400, 422, 500)


@pytest.mark.api
def test_get_nonexistent_booking_returns_404(booking_client):
    resp = booking_client.get_booking(999999999)
    assert_status_code(resp, 404)


@pytest.mark.api
def test_update_nonexistent_booking_returns_error(booking_client):
    updated = {**VALID_BOOKING, "firstname": "Jane"}
    resp = booking_client.update_booking(999999999, updated)
    assert resp.status_code in (403, 404, 405)


@pytest.mark.api
def test_delete_nonexistent_booking_returns_error(booking_client):
    resp = booking_client.delete_booking(999999999)
    assert resp.status_code in (403, 404, 405)


@pytest.mark.api
def test_partial_update_booking_returns_200(booking_client):
    booking_id = booking_client.create_booking(VALID_BOOKING).json()["bookingid"]
    resp = booking_client.partial_update_booking(booking_id, {"additionalneeds": "Lunch"})
    assert_status_code(resp, 200)
    assert resp.json()["additionalneeds"] == "Lunch"


@pytest.mark.api
def test_get_large_booking_id_returns_error(booking_client):
    resp = booking_client.get_booking(9223372036854775807)
    assert resp.status_code in (400, 404, 500)
