import pytest
import requests


@pytest.mark.api
def test_OH_API_006_list_leave_types_returns_200(orangehrm_client):
    resp = orangehrm_client.get("/leave/leave-types")
    assert resp.status_code == 200
    assert isinstance(resp.json().get("data"), list)


@pytest.mark.api
def test_OH_API_007_list_leave_types_data_has_id_and_name(orangehrm_client):
    resp = orangehrm_client.get("/leave/leave-types")
    data = resp.json().get("data", [])
    assert len(data) > 0
    first = data[0]
    assert "id" in first
    assert "name" in first


@pytest.mark.api
def test_OH_API_008_list_leave_types_without_auth_returns_401():
    resp = requests.get(
        "https://opensource-demo.orangehrmlive.com/web/index.php/api/v2/leave/leave-types"
    )
    assert resp.status_code == 401


@pytest.mark.api
def test_OH_API_009_create_leave_request_with_invalid_type_returns_400(orangehrm_client):
    resp = orangehrm_client.post("/leave/leave-requests", json={
        "leaveTypeId": 99999,
        "fromDate": "2099-01-01",
        "toDate": "2099-01-02",
    })
    assert resp.status_code in (400, 422)


@pytest.mark.api
def test_OH_API_010_create_leave_request_with_date_to_before_from_returns_400(orangehrm_client):
    types_resp = orangehrm_client.get("/leave/leave-types")
    leave_type_id = types_resp.json()["data"][0]["id"]
    resp = orangehrm_client.post("/leave/leave-requests", json={
        "leaveTypeId": leave_type_id,
        "fromDate": "2099-06-30",
        "toDate": "2099-01-01",
    })
    assert resp.status_code in (400, 422)
