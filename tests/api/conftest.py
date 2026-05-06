import pytest
from api.orangehrm_client import OrangeHRMClient


@pytest.fixture(scope="session")
def orangehrm_client():
    """Session-scoped OrangeHRM API client authenticated as Admin."""
    client = OrangeHRMClient()
    client.login()
    yield client
    client.close()
