import requests
import pytest


@pytest.mark.api
@pytest.mark.security
@pytest.mark.sanity
def test_RB_SEC_001_delete_booking_without_auth_returns_403(booking_client, rb_api_base):
    # Create a booking first, then attempt to delete it without credentials
    create_resp = booking_client.create_booking({
        "firstname": "SecTest",
        "lastname": "Delete",
        "totalprice": 50,
        "depositpaid": False,
        "bookingdates": {"checkin": "2026-10-01", "checkout": "2026-10-05"},
    })
    booking_id = create_resp.json()["bookingid"]

    resp = requests.delete(f"{rb_api_base}/booking/{booking_id}")
    assert resp.status_code in (403, 401), \
        f"Expected 401/403 without auth, got {resp.status_code}"


@pytest.mark.api
@pytest.mark.security
@pytest.mark.regression
def test_RB_SEC_002_update_booking_without_auth_returns_403(booking_client, rb_api_base):
    create_resp = booking_client.create_booking({
        "firstname": "SecTest",
        "lastname": "Update",
        "totalprice": 50,
        "depositpaid": False,
        "bookingdates": {"checkin": "2026-10-01", "checkout": "2026-10-03"},
    })
    booking_id = create_resp.json()["bookingid"]

    resp = requests.put(
        f"{rb_api_base}/booking/{booking_id}",
        json={
            "firstname": "Hacked",
            "lastname": "Update",
            "totalprice": 1,
            "depositpaid": False,
            "bookingdates": {"checkin": "2026-10-01", "checkout": "2026-10-03"},
        },
    )
    assert resp.status_code in (403, 401), \
        f"Expected 401/403 without auth, got {resp.status_code}"


@pytest.mark.api
@pytest.mark.security
@pytest.mark.regression
def test_RB_SEC_003_sql_injection_in_search_does_not_cause_500(rb_api_base):
    resp = requests.get(
        f"{rb_api_base}/booking",
        params={"firstname": "' OR '1'='1", "lastname": "' OR '1'='1"},
    )
    assert resp.status_code != 500, "SQL injection caused a server error"
    assert "sql" not in resp.text.lower()


@pytest.mark.api
@pytest.mark.security
@pytest.mark.regression
def test_RB_SEC_004_api_response_content_type_is_json(rb_api_base):
    resp = requests.get(f"{rb_api_base}/booking")
    assert resp.status_code == 200
    ct = resp.headers.get("Content-Type", "")
    assert "application/json" in ct or "json" in ct, \
        f"Expected JSON content-type, got: {ct}"


@pytest.mark.api
@pytest.mark.security
@pytest.mark.regression
def test_RB_SEC_005_nonexistent_booking_id_returns_404(rb_api_base):
    resp = requests.get(f"{rb_api_base}/booking/999999999")
    assert resp.status_code == 404, \
        f"Expected 404 for nonexistent booking, got {resp.status_code}"
