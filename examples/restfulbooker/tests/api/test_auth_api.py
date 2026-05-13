import pytest


@pytest.mark.api
def test_RB_API_020_authenticate_valid_credentials(booking_client):
    token = booking_client.authenticate()
    assert token is not None
    assert len(token) > 0
    assert token != "Bad credentials"


@pytest.mark.api
def test_RB_API_021_authenticate_invalid_credentials(rb_api_base):
    from booking_client import BookingClient
    client = BookingClient(rb_api_base, "wrong_user", "wrong_pass")
    try:
        token = client.authenticate()
        assert token is None  # API returns {"reason": "Bad credentials"}, no token key
    finally:
        client.close()


@pytest.mark.api
def test_RB_API_022_delete_without_auth_is_rejected(booking_client, rb_api_base):
    from booking_client import BookingClient
    create_resp = booking_client.create_booking({
        "firstname": "NoAuth",
        "lastname": "Test",
        "totalprice": 99,
        "depositpaid": False,
        "bookingdates": {"checkin": "2026-09-01", "checkout": "2026-09-05"},
    })
    booking_id = create_resp.json()["bookingid"]

    unauthed = BookingClient(rb_api_base, "", "")
    try:
        resp = unauthed._call("DELETE", f"/booking/{booking_id}")
        assert resp.status_code in (403, 401)
    finally:
        unauthed.close()
