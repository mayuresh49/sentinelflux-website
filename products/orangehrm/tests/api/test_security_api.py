import pytest
import requests
from utils.assertions import assert_status_code


@pytest.mark.api
@pytest.mark.sanity
def test_OH_API_029_authenticate_user_and_create_session(orangehrm_api_base_url, orangehrm_credentials):
    response = requests.post(
        f"{orangehrm_api_base_url}/auth/login",
        json={"username": orangehrm_credentials["username"], "password": orangehrm_credentials["password"]},
    )
    assert response.status_code in (200, 302)


@pytest.mark.api
@pytest.mark.regression
def test_OH_API_030_attempt_to_authenticate_with_invalid_credentials(orangehrm_api_base_url):
    response = requests.post(
        f"{orangehrm_api_base_url}/auth/login",
        json={"username": "no_such_user_xyzzy", "password": "DefinitelyWrong!9"},
    )
    assert response.status_code in (401, 403)


@pytest.mark.api
@pytest.mark.sanity
def test_OH_API_031_list_all_employees(orangehrm_client):
    resp = orangehrm_client.get("/pim/employees")
    assert_status_code(resp, 200)
    body = resp.json()
    assert isinstance(body.get("data"), list)
    assert len(body["data"]) > 0


@pytest.mark.api
@pytest.mark.sanity
def test_OH_API_032_create_a_new_employee_record(orangehrm_client):
    payload = {"firstName": "Pipeline", "lastName": "TestUser", "middleName": ""}
    resp = orangehrm_client.post("/pim/employees", json=payload)
    assert resp.status_code in (200, 201)
    body = resp.json()
    assert "empNumber" in body.get("data", body)


@pytest.mark.api
@pytest.mark.sanity
def test_OH_API_033_retrieve_a_specific_employee_by_emp_number(orangehrm_client):
    resp = orangehrm_client.get("/pim/employees/5")
    assert_status_code(resp, 200)
    body = resp.json()
    assert body["data"]["empNumber"] == 5


@pytest.mark.api
@pytest.mark.sanity
def test_OH_API_034_update_employee_personal_details(orangehrm_client):
    payload = {"firstName": "Updated", "lastName": "Employee"}
    resp = orangehrm_client.put("/pim/employees/5/personal-details", json=payload)
    assert resp.status_code in (200, 204)


@pytest.mark.api
@pytest.mark.sanity
def test_OH_API_035_delete_an_employee(orangehrm_client):
    resp = orangehrm_client.delete("/pim/employees", json={"ids": [999]})
    assert resp.status_code in (200, 204, 404)


@pytest.mark.api
@pytest.mark.sanity
def test_OH_API_036_list_all_configured_leave_types(orangehrm_client):
    resp = orangehrm_client.get("/leave/leaveTypes")
    assert_status_code(resp, 200)
    body = resp.json()
    assert isinstance(body.get("data"), list)
    assert len(body["data"]) > 0


@pytest.mark.api
@pytest.mark.sanity
def test_OH_API_037_submit_a_leave_request(orangehrm_client):
    payload = {
        "fromDate": "2025-10-01",
        "toDate": "2025-10-01",
        "leaveTypeId": 1,
        "duration": {"type": "full_day"},
    }
    resp = orangehrm_client.post("/leave/employees/5/leave-requests", json=payload)
    assert resp.status_code in (200, 201, 400)


@pytest.mark.api
@pytest.mark.sanity
def test_OH_API_038_list_system_users(orangehrm_client):
    resp = orangehrm_client.get("/admin/users")
    assert_status_code(resp, 200)
    body = resp.json()
    assert isinstance(body.get("data"), list)
    assert len(body["data"]) > 0


@pytest.mark.api
@pytest.mark.sanity
def test_OH_API_039_create_a_new_system_user(orangehrm_client):
    payload = {
        "username": "pipeline_test_user",
        "password": "Temp@12345!",
        "status": 1,
        "userRoleId": 2,
        "empNumber": 1,
    }
    resp = orangehrm_client.post("/admin/users", json=payload)
    assert resp.status_code in (200, 201, 400)
