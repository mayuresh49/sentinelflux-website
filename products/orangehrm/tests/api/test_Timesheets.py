import pytest

from utils.assertions import assert_status_code


@pytest.mark.api
@pytest.mark.sanity
def test_get_timesheets_returns_200(rest_client):
    response = rest_client.get(endpoint_name="timesheets")
    assert_status_code(response, 200)
    body = response.json()
    assert isinstance(body, list)

@pytest.mark.api
@pytest.mark.regression
def test_post_timesheets_with_valid_data_returns_201(rest_client):
    payload = {
        "empNumber": 1,
        "date": "2023-04-15",
        "hours": 8.0,
        "description": "Worked on project XYZ"
    }
    response = rest_client.post(endpoint_name="timesheets", json=payload)
    assert_status_code(response, 201)
    body = response.json()
    assert "empNumber" in body
    assert "date" in body
    assert "hours" in body

@pytest.mark.api
@pytest.mark.regression
def test_put_timesheet_with_valid_data_returns_200(rest_client):
    timesheet_id = 1
    payload = {
        "hours": 8.5,
        "description": "Updated description for project XYZ"
    }
    response = rest_client.put(endpoint_name="timesheets/{timesheetId}", path_params={"timesheetId": timesheet_id}, json=payload)
    assert_status_code(response, 200)
    body = response.json()
    assert "hours" in body
    assert "description" in body

@pytest.mark.api
@pytest.mark.regression
def test_delete_timesheet_with_valid_data_returns_204(rest_client):
    timesheet_id = 1
    response = rest_client.delete(endpoint_name="timesheets/{timesheetId}", path_params={"timesheetId": timesheet_id})
    assert_status_code(response, 204)
    assert not response.text

@pytest.mark.api
@pytest.mark.security
def test_get_timesheets_unauthenticated_returns_401(rest_client):
    response = rest_client.get(endpoint_name="timesheets")
    assert_status_code(response, 401)

@pytest.mark.api
@pytest.mark.security
def test_get_timesheets_insufficient_permissions_returns_403(rest_client):
    response = rest_client.get(endpoint_name="timesheets")
    assert_status_code(response, 403)

@pytest.mark.api
@pytest.mark.regression
def test_post_timesheets_missing_empNumber_returns_400(rest_client):
    payload = {
        "date": "2023-04-15",
        "hours": 8.0,
        "description": "Worked on project XYZ"
    }
    response = rest_client.post(endpoint_name="timesheets", json=payload)
    assert_status_code(response, 400)

@pytest.mark.api
@pytest.mark.regression
def test_post_timesheets_invalid_date_format_returns_400(rest_client):
    payload = {
        "empNumber": 1,
        "date": "15-04-2023",
        "hours": 8.0,
        "description": "Worked on project XYZ"
    }
    response = rest_client.post(endpoint_name="timesheets", json=payload)
    assert_status_code(response, 400)

@pytest.mark.api
@pytest.mark.regression
def test_put_non_existent_timesheet_returns_404(rest_client):
    timesheet_id = 9999
    payload = {
        "hours": 8.5,
        "description": "Updated description for project XYZ"
    }
    response = rest_client.put(endpoint_name="timesheets/{timesheetId}", path_params={"timesheetId": timesheet_id}, json=payload)
    assert_status_code(response, 404)

@pytest.mark.api
@pytest.mark.regression
def test_delete_non_existent_timesheet_returns_404(rest_client):
    timesheet_id = 9999
    response = rest_client.delete(endpoint_name="timesheets/{timesheetId}", path_params={"timesheetId": timesheet_id})
    assert_status_code(response, 404)

@pytest.mark.api
@pytest.mark.sanity
def test_get_timesheets_no_entries_returns_empty_array(rest_client):
    response = rest_client.get(endpoint_name="timesheets")
    assert_status_code(response, 200)
    body = response.json()
    assert isinstance(body, list)
    assert len(body) == 0

@pytest.mark.api
@pytest.mark.regression
def test_post_timesheets_minimum_required_fields_returns_201(rest_client):
    payload = {
        "empNumber": 1,
        "date": "2023-04-15",
        "hours": 8.0
    }
    response = rest_client.post(endpoint_name="timesheets", json=payload)
    assert_status_code(response, 201)

@pytest.mark.api
@pytest.mark.regression
def test_put_timesheet_no_changes_returns_200(rest_client):
    timesheet_id = 1
    payload = {}
    response = rest_client.put(endpoint_name="timesheets/{timesheetId}", path_params={"timesheetId": timesheet_id}, json=payload)
    assert_status_code(response, 200)

@pytest.mark.api
@pytest.mark.sanity
def test_post_timesheets_unique_empNumber_returns_201(rest_client):
    payload = {
        "empNumber": 9999,
        "date": "2023-04-15",
        "hours": 8.0,
        "description": "Worked on project XYZ"
    }
    response = rest_client.post(endpoint_name="timesheets", json=payload)
    assert_status_code(response, 400)

@pytest.mark.api
@pytest.mark.regression
def test_put_timesheet_invalid_hours_returns_400(rest_client):
    timesheet_id = 1
    payload = {
        "hours": -5,
        "description": "Updated description for project XYZ"
    }
    response = rest_client.put(endpoint_name="timesheets/{timesheetId}", path_params={"timesheetId": timesheet_id}, json=payload)
    assert_status_code(response, 400)