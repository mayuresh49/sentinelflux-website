import pytest
import requests
from utils.assertions import assert_status_code


@pytest.mark.api
@pytest.mark.sanity
def test_OH_API_029_configure_kpis_valid_payload_positive(orangehrm_client):
    payload = {"jobTitleId": 1, "kpiList": [{"name": "Productivity", "description": "Tasks completed per sprint"}]}
    resp = orangehrm_client.post("/performance/configure/kpi", json=payload)
    assert_status_code(resp, 200)


@pytest.mark.api
@pytest.mark.regression
def test_OH_API_030_configure_kpis_missing_required_field_negative(orangehrm_client):
    payload = {"kpiList": [{"name": "Productivity"}]}
    resp = orangehrm_client.post("/performance/configure/kpi", json=payload)
    assert_status_code(resp, 400)


@pytest.mark.api
@pytest.mark.regression
def test_OH_API_031_configure_kpis_unauthorized_negative(orangehrm_api_base_url):
    resp = requests.post(
        f"{orangehrm_api_base_url}/performance/configure/kpi",
        headers={"Authorization": "Bearer invalid_token"},
        json={"jobTitleId": 1, "kpiList": [{"name": "Productivity"}]},
    )
    assert_status_code(resp, 401)


@pytest.mark.api
@pytest.mark.sanity
def test_OH_API_032_assign_kpis_by_job_title_valid_payload_positive(orangehrm_client):
    payload = {"jobTitleId": 1, "kpiIds": [1, 2]}
    resp = orangehrm_client.put("/performance/configure/kpi/assign", json=payload)
    assert_status_code(resp, 200)


@pytest.mark.api
@pytest.mark.regression
def test_OH_API_033_assign_kpis_invalid_job_title_id_negative(orangehrm_client):
    payload = {"jobTitleId": 99999, "kpiIds": [1]}
    resp = orangehrm_client.put("/performance/configure/kpi/assign", json=payload)
    assert_status_code(resp, 404)


@pytest.mark.api
@pytest.mark.sanity
def test_OH_API_034_create_performance_tracker_valid_payload_positive(orangehrm_client):
    payload = {"employeeId": 1, "trackerData": [{"kpiId": 1, "value": 4.5}]}
    resp = orangehrm_client.post("/performance/trackers", json=payload)
    assert_status_code(resp, 200)


@pytest.mark.api
@pytest.mark.regression
def test_OH_API_035_create_performance_tracker_missing_employee_id_negative(orangehrm_client):
    payload = {"trackerData": [{"kpiId": 1, "value": 4.5}]}
    resp = orangehrm_client.post("/performance/trackers", json=payload)
    assert_status_code(resp, 400)


@pytest.mark.api
@pytest.mark.sanity
def test_OH_API_036_create_performance_review_valid_payload_positive(orangehrm_client):
    payload = {"employeeId": 1, "reviewData": [{"kpiId": 1, "rating": 4.0}]}
    resp = orangehrm_client.post("/performance/reviews", json=payload)
    assert_status_code(resp, 200)


@pytest.mark.api
@pytest.mark.regression
def test_OH_API_037_create_performance_review_missing_review_data_negative(orangehrm_client):
    payload = {"employeeId": 1}
    resp = orangehrm_client.post("/performance/reviews", json=payload)
    assert_status_code(resp, 400)
