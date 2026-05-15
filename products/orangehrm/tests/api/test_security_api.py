import pytest
import requests


@pytest.mark.api
@pytest.mark.security
def test_OH_SEC_001_unauthenticated_request_to_users_returns_401(orangehrm_api_base_url):
    resp = requests.get(f"{orangehrm_api_base_url}/admin/users")
    assert resp.status_code == 401


@pytest.mark.api
@pytest.mark.security
def test_OH_SEC_002_unauthenticated_request_to_employees_returns_401(orangehrm_api_base_url):
    resp = requests.get(f"{orangehrm_api_base_url}/pim/employees")
    assert resp.status_code == 401


@pytest.mark.api
@pytest.mark.security
def test_OH_SEC_003_sql_injection_in_search_does_not_return_500(orangehrm_client):
    resp = orangehrm_client.get("/pim/employees", params={"nameOrId": "' OR '1'='1"})
    assert resp.status_code != 500, "SQL injection caused a server error"
    assert "sql" not in resp.text.lower()
    assert "syntax error" not in resp.text.lower()


@pytest.mark.api
@pytest.mark.security
def test_OH_SEC_004_api_response_content_type_is_json(orangehrm_client):
    resp = orangehrm_client.get("/pim/employees")
    assert resp.status_code == 200
    ct = resp.headers.get("Content-Type", "")
    assert "application/json" in ct, f"Expected JSON content-type, got: {ct}"


@pytest.mark.api
@pytest.mark.security
def test_OH_SEC_005_x_content_type_options_header_present(orangehrm_client):
    resp = orangehrm_client.get("/pim/employees")
    assert resp.status_code == 200
    header = resp.headers.get("X-Content-Type-Options", "")
    assert header.lower() == "nosniff", f"X-Content-Type-Options missing or wrong: {header!r}"


@pytest.mark.api
@pytest.mark.security
def test_OH_SEC_006_delete_employee_without_auth_is_rejected(orangehrm_api_base_url):
    # Server may return 401 (auth required) or 405 (method rejected before auth check)
    resp = requests.delete(f"{orangehrm_api_base_url}/pim/employees/1")
    assert resp.status_code in (401, 405), \
        f"Expected 401 or 405 without auth, got {resp.status_code}"


@pytest.mark.api
@pytest.mark.security
def test_OH_SEC_007_arbitrary_origin_not_reflected_in_cors(orangehrm_client):
    resp = orangehrm_client.get(
        "/pim/employees",
        headers={"Origin": "https://evil.example.com"},
    )
    acao = resp.headers.get("Access-Control-Allow-Origin", "")
    assert acao != "https://evil.example.com", "Arbitrary origin reflected in CORS header"
