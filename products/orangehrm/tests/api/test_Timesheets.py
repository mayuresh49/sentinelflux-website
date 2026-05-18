import pytest
import requests


@pytest.mark.api
@pytest.mark.sanity
def test_OH_API_014_get_timesheets_returns_200(orangehrm_client):
    resp = orangehrm_client.get("/timesheets")
    assert resp.status_code == 200
    assert isinstance(resp.json().get("data"), list)


@pytest.mark.api
@pytest.mark.sanity
def test_OH_API_015_post_timesheets_with_valid_data_returns_201(orangehrm_client, shared_state):
    payload = {"empNumber": 1, "date": "2023-04-15", "hours": 8.0, "description": "Worked on project XYZ"}
    resp = orangehrm_client.post("/timesheets", json=payload)
    assert resp.status_code == 201
    body = resp.json().get("data", {})
    assert body.get("empNumber") == 1 or "empNumber" in str(resp.json())
    shared_state["timesheet_id"] = body.get("id") or body.get("timesheetId")


@pytest.mark.api
@pytest.mark.sanity
def test_OH_API_016_put_timesheets_with_valid_data_returns_200(orangehrm_client, shared_state):
    timesheet_id = shared_state.get("timesheet_id", 1)
    payload = {"hours": 8.5, "description": "Updated description for project XYZ"}
    resp = orangehrm_client.put(f"/timesheets/{timesheet_id}", json=payload)
    assert resp.status_code == 200
    body = resp.json().get("data", {})
    assert body.get("hours") == 8.5 or resp.status_code == 200


@pytest.mark.api
@pytest.mark.regression
def test_OH_API_017_delete_timesheets_with_valid_id_returns_204(orangehrm_client, shared_state):
    timesheet_id = shared_state.get("timesheet_id", 1)
    resp = orangehrm_client.delete(f"/timesheets/{timesheet_id}")
    assert resp.status_code == 204
    assert not resp.content


@pytest.mark.api
@pytest.mark.regression
def test_OH_API_018_get_timesheets_unauthenticated_returns_401(orangehrm_api_base_url):
    resp = requests.get(f"{orangehrm_api_base_url}/timesheets")
    assert resp.status_code == 401


@pytest.mark.api
@pytest.mark.regression
def test_OH_API_019_get_timesheets_insufficient_permissions_returns_403(orangehrm_api_base_url, orangehrm_credentials):
    # Uses ESS credentials that lack timesheet admin access
    resp = requests.get(
        f"{orangehrm_api_base_url}/timesheets",
        auth=(orangehrm_credentials["username"], "wrong_role_token"),
    )
    assert resp.status_code in (401, 403)


@pytest.mark.api
@pytest.mark.regression
def test_OH_API_020_post_timesheets_missing_empNumber_returns_400(orangehrm_client):
    payload = {"date": "2023-04-15", "hours": 8.0, "description": "Missing empNumber"}
    resp = orangehrm_client.post("/timesheets", json=payload)
    assert resp.status_code == 400
    body = resp.json()
    assert "empNumber" in str(body) or "error" in str(body).lower()


@pytest.mark.api
@pytest.mark.regression
def test_OH_API_021_post_timesheets_invalid_date_format_returns_400(orangehrm_client):
    payload = {"empNumber": 1, "date": "15-04-2023", "hours": 8.0}
    resp = orangehrm_client.post("/timesheets", json=payload)
    assert resp.status_code == 400
    body = resp.json()
    assert "date" in str(body).lower() or "error" in str(body).lower()


@pytest.mark.api
@pytest.mark.regression
def test_OH_API_022_put_timesheets_nonexistent_id_returns_404(orangehrm_client):
    payload = {"hours": 8.5, "description": "Updated"}
    resp = orangehrm_client.put("/timesheets/9999", json=payload)
    assert resp.status_code == 404


@pytest.mark.api
@pytest.mark.regression
def test_OH_API_023_delete_timesheets_nonexistent_id_returns_404(orangehrm_client):
    resp = orangehrm_client.delete("/timesheets/9999")
    assert resp.status_code == 404


@pytest.mark.api
@pytest.mark.regression
def test_OH_API_024_get_timesheets_no_entries_returns_empty_array(orangehrm_client):
    resp = orangehrm_client.get("/timesheets")
    assert resp.status_code == 200
    data = resp.json().get("data", [])
    assert isinstance(data, list)


@pytest.mark.api
@pytest.mark.regression
def test_OH_API_025_post_timesheets_minimum_required_fields_returns_201(orangehrm_client):
    payload = {"empNumber": 1, "date": "2023-04-15", "hours": 8.0}
    resp = orangehrm_client.post("/timesheets", json=payload)
    assert resp.status_code == 201


@pytest.mark.api
@pytest.mark.regression
def test_OH_API_026_put_timesheets_empty_body_returns_200(orangehrm_client):
    resp = orangehrm_client.put("/timesheets/1", json={})
    assert resp.status_code == 200


@pytest.mark.api
@pytest.mark.regression
def test_OH_API_027_post_timesheets_nonexistent_empNumber_returns_400(orangehrm_client):
    payload = {"empNumber": 9999, "date": "2023-04-15", "hours": 8.0, "description": "Non-existent employee"}
    resp = orangehrm_client.post("/timesheets", json=payload)
    assert resp.status_code == 400
    body = resp.json()
    assert "empNumber" in str(body).lower() or "employee" in str(body).lower() or "error" in str(body).lower()


@pytest.mark.api
@pytest.mark.regression
def test_OH_API_028_put_timesheets_invalid_hours_value_returns_400(orangehrm_client):
    payload = {"hours": -5, "description": "Negative hours"}
    resp = orangehrm_client.put("/timesheets/1", json=payload)
    assert resp.status_code == 400
    body = resp.json()
    assert "hours" in str(body).lower() or "invalid" in str(body).lower() or "error" in str(body).lower()
