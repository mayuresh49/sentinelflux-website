import pytest

VALID_BOOKING = {
    "firstname": "John",
    "lastname": "Doe",
    "totalprice": 250,
    "depositpaid": True,
    "bookingdates": {"checkin": "2024-01-15", "checkout": "2024-01-20"},
    "additionalneeds": "Breakfast",
}


@pytest.mark.api
def test_RB_API_011_create_booking_returns_ok(booking_client):
    response = booking_client.create_booking(VALID_BOOKING)
    assert response.status_code == 200
    body = response.json()
    assert "bookingid" in body
    assert isinstance(body["bookingid"], int)


@pytest.mark.api
def test_RB_API_012_get_booking_returns_details(booking_client):
    created = booking_client.create_booking(VALID_BOOKING)
    booking_id = created.json()["bookingid"]
    response = booking_client.get_booking(booking_id)
    assert response.status_code == 200
    body = response.json()
    assert body["firstname"] == "John"
    assert body["lastname"] == "Doe"
    assert body["totalprice"] == 250
    assert body["depositpaid"] is True
    assert body["bookingdates"]["checkin"] == "2024-01-15"
    assert body["bookingdates"]["checkout"] == "2024-01-20"


@pytest.mark.api
def test_RB_API_013_update_booking_returns_updated(booking_client):
    created = booking_client.create_booking(VALID_BOOKING)
    booking_id = created.json()["bookingid"]
    updated_payload = {**VALID_BOOKING, "firstname": "Jane", "totalprice": 350}
    response = booking_client.update_booking(booking_id, updated_payload)
    assert response.status_code == 200
    body = response.json()
    assert body["firstname"] == "Jane"
    assert body["totalprice"] == 350


@pytest.mark.api
def test_RB_API_014_delete_booking_returns_created(booking_client):
    created = booking_client.create_booking(VALID_BOOKING)
    booking_id = created.json()["bookingid"]
    response = booking_client.delete_booking(booking_id)
    assert response.status_code == 201


@pytest.mark.api
def test_RB_API_015_get_booking_ids_returns_list(booking_client):
    response = booking_client.get_booking_ids()
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert len(body) > 0
    assert all("bookingid" in item for item in body[:5])


@pytest.mark.api
def test_RB_API_016_get_nonexistent_booking_returns_not_found(booking_client):
    response = booking_client.get_booking(9999999)
    assert response.status_code == 404


@pytest.mark.api
def test_RB_API_017_partial_update_booking_returns_ok(booking_client):
    created = booking_client.create_booking(VALID_BOOKING)
    booking_id = created.json()["bookingid"]
    response = booking_client.partial_update_booking(booking_id, {"firstname": "UpdatedName"})
    assert response.status_code == 200
    assert response.json()["firstname"] == "UpdatedName"


@pytest.mark.api
def test_RB_API_018_create_booking_with_min_names_returns_ok(booking_client):
    payload = {**VALID_BOOKING, "firstname": "A", "lastname": "B"}
    response = booking_client.create_booking(payload)
    assert response.status_code == 200
    assert "bookingid" in response.json()


@pytest.mark.api
def test_RB_API_019_filter_bookings_by_name_returns_subset(booking_client):
    booking_client.create_booking({**VALID_BOOKING, "firstname": "UniqueFilterTest"})
    response = booking_client.get_booking_ids(params={"firstname": "UniqueFilterTest"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)
