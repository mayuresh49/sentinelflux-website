from utils.assertions import assert_status_code


def test_create_booking(rest_client):
    response = rest_client.post(
        endpoint_name="create_booking",
        payload_name="create_booking",
        schema_name="booking_schema",
    )
    assert_status_code(response, 200)
    body = response.json()
    assert "bookingid" in body
    assert "booking" in body


def test_get_booking(rest_client):
    create_response = rest_client.post(
        endpoint_name="create_booking",
        payload_name="create_booking",
        schema_name="booking_schema",
    )
    booking_id = create_response.json()["bookingid"]
    response = rest_client.get(
        endpoint_name="get_booking",
        path_params={"booking_id": booking_id},
        schema_name="booking_details_schema",
    )
    assert_status_code(response, 200)
