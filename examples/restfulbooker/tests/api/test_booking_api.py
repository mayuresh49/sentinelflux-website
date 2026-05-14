import pytest

VALID_BOOKING = {
    "firstname": "James",
    "lastname": "Brown",
    "totalprice": 150,
    "depositpaid": True,
    "bookingdates": {"checkin": "2026-08-01", "checkout": "2026-08-07"},
    "additionalneeds": "Breakfast",
}


@pytest.mark.api
@pytest.mark.sanity
def test_RB_API_001_get_all_bookings(booking_client):
    resp = booking_client.get_booking_ids()
    assert resp.status_code == 200
    ids = resp.json()
    assert isinstance(ids, list)
    assert len(ids) > 0
    assert "bookingid" in ids[0]


@pytest.mark.api
@pytest.mark.sanity
def test_RB_API_002_create_booking_returns_id(booking_client):
    resp = booking_client.create_booking(VALID_BOOKING)
    assert resp.status_code == 200
    body = resp.json()
    assert "bookingid" in body
    assert isinstance(body["bookingid"], int)
    assert body["booking"]["firstname"] == VALID_BOOKING["firstname"]
    assert body["booking"]["lastname"] == VALID_BOOKING["lastname"]


@pytest.mark.api
@pytest.mark.sanity
def test_RB_API_003_get_booking_by_id(booking_client):
    create_resp = booking_client.create_booking(VALID_BOOKING)
    booking_id = create_resp.json()["bookingid"]

    resp = booking_client.get_booking(booking_id)
    assert resp.status_code == 200
    body = resp.json()
    assert body["firstname"] == VALID_BOOKING["firstname"]
    assert body["lastname"] == VALID_BOOKING["lastname"]
    assert body["totalprice"] == VALID_BOOKING["totalprice"]
    assert body["depositpaid"] == VALID_BOOKING["depositpaid"]
    assert body["bookingdates"]["checkin"] == VALID_BOOKING["bookingdates"]["checkin"]
    assert body["bookingdates"]["checkout"] == VALID_BOOKING["bookingdates"]["checkout"]


@pytest.mark.api
@pytest.mark.regression
def test_RB_API_004_update_booking(booking_client):
    create_resp = booking_client.create_booking(VALID_BOOKING)
    booking_id = create_resp.json()["bookingid"]

    updated = {**VALID_BOOKING, "firstname": "Updated", "totalprice": 200}
    resp = booking_client.update_booking(booking_id, updated)
    assert resp.status_code == 200
    body = resp.json()
    assert body["firstname"] == "Updated"
    assert body["totalprice"] == 200


@pytest.mark.api
@pytest.mark.regression
def test_RB_API_005_partial_update_booking(booking_client):
    create_resp = booking_client.create_booking(VALID_BOOKING)
    booking_id = create_resp.json()["bookingid"]

    resp = booking_client.partial_update_booking(booking_id, {"additionalneeds": "Lunch"})
    assert resp.status_code == 200
    assert resp.json()["additionalneeds"] == "Lunch"


@pytest.mark.api
@pytest.mark.regression
def test_RB_API_006_delete_booking(booking_client):
    create_resp = booking_client.create_booking(VALID_BOOKING)
    booking_id = create_resp.json()["bookingid"]

    del_resp = booking_client.delete_booking(booking_id)
    assert del_resp.status_code in (200, 201)

    get_resp = booking_client.get_booking(booking_id)
    assert get_resp.status_code == 404


@pytest.mark.api
@pytest.mark.regression
def test_RB_API_007_get_nonexistent_booking_returns_404(booking_client):
    resp = booking_client.get_booking(999999999)
    assert resp.status_code == 404


@pytest.mark.api
@pytest.mark.regression
def test_RB_API_008_filter_bookings_by_name(booking_client):
    booking_client.create_booking({**VALID_BOOKING, "firstname": "FilterTest"})
    resp = booking_client.get_booking_ids(params={"firstname": "FilterTest"})
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


@pytest.mark.api
@pytest.mark.regression
def test_RB_API_009_create_booking_missing_required_field(booking_client):
    incomplete = {k: v for k, v in VALID_BOOKING.items() if k != "firstname"}
    resp = booking_client.create_booking(incomplete)
    assert resp.status_code in (400, 422, 500)


@pytest.mark.api
@pytest.mark.regression
def test_RB_API_010_create_booking_without_optional_field(booking_client):
    minimal = {k: v for k, v in VALID_BOOKING.items() if k != "additionalneeds"}
    resp = booking_client.create_booking(minimal)
    assert resp.status_code == 200
    assert "bookingid" in resp.json()
