import pytest
import requests


@pytest.mark.api
def test_OH_API_001_list_system_users_returns_200(orangehrm_client):
    resp = orangehrm_client.get("/admin/users")
    assert resp.status_code == 200
    assert isinstance(resp.json().get("data"), list)


@pytest.mark.api
def test_OH_API_002_list_system_users_has_admin_user(orangehrm_client):
    resp = orangehrm_client.get("/admin/users")
    users = resp.json().get("data", [])
    assert any(u.get("userName") == "Admin" for u in users)


@pytest.mark.api
def test_OH_API_003_list_system_users_without_auth_returns_401(orangehrm_api_base_url):
    resp = requests.get(f"{orangehrm_api_base_url}/admin/users")
    assert resp.status_code == 401


@pytest.mark.api
def test_OH_API_004_create_user_with_weak_password_returns_400(orangehrm_client):
    resp = orangehrm_client.post("/admin/users", json={
        "username": "testuser_weakpwd",
        "password": "weak",
        "status": 1,
        "userRoleId": 2,
        "empNumber": 1,
    })
    assert resp.status_code in (400, 422)


@pytest.mark.api
def test_OH_API_005_create_user_with_duplicate_username_returns_400(orangehrm_client):
    resp = orangehrm_client.post("/admin/users", json={
        "username": "Admin",
        "password": "Admin1234!",
        "status": 1,
        "userRoleId": 2,
        "empNumber": 1,
    })
    assert resp.status_code in (400, 422)
