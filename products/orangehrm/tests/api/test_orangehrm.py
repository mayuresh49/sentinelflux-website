import pytest
import requests  # only for unauthenticated raw calls
from utils.assertions import assert_status_code

@pytest.mark.api
def test_TC_001_successful_login_with_valid_credentials(orangehrm_api_base_url, orangehrm_credentials):
    resp = requests.post(f"{orangehrm_api_base_url}/auth/login",
                         json={"username": "admin", "password": "admin123"})
    assert_status_code(resp, 200)
    body = resp.json()
    assert "sessionToken" in body

@pytest.mark.api
def test_TC_002_failed_login_with_invalid_credentials(orangehrm_api_base_url):
    resp = requests.post(f"{orangehrm_api_base_url}/auth/login",
                         json={"username": "admin", "password": "wrongpassword"})
    assert_status_code(resp, 401)
    body = resp.json()
    assert body["errorCode"] == "INVALID_CREDENTIALS"

@pytest.mark.api
def test_TC_004_successful_login_with_case_sensitive_username(orangehrm_api_base_url):
    resp = requests.post(f"{orangehrm_api_base_url}/auth/login",
                         json={"username": "Admin", "password": "admin123"})
    assert_status_code(resp, 200)
    body = resp.json()
    assert "sessionToken" in body