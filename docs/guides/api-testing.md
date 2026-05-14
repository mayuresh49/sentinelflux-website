# API Testing

## REST client

The built-in `RestClient` uses named endpoints defined in `api/endpoints/rest_endpoints.json` and payloads from `api/payloads/rest_payloads/*.json`.

```python
import pytest

@pytest.mark.api
def test_get_booking(rest_client):
    # First create a booking to get a valid ID
    create = rest_client.post("create_booking", payload_name="create_booking")
    booking_id = create.json()["bookingid"]

    resp = rest_client.get("get_booking", path_params={"booking_id": booking_id})
    assert resp.status_code == 200
    assert resp.json()["firstname"]
```

The `rest_client` fixture is session-scoped and reads `config.api.rest_base_url`.

For example projects, it is common to write a dedicated API client class instead (see `products/restfulbooker/booking_client.py` for a pattern using `requests.Session` directly with per-test request logging built in).

## GraphQL client

```python
@pytest.mark.api
def test_countries(graphql_client):
    query = "{ countries { code name } }"
    data = graphql_client.execute(query)
    assert data["countries"]
```

## Request/response logging

Every API client that inherits from `RestClient` automatically logs each request. On test failure, `reports/artifacts/<test>/api_calls.log` contains:

```
### Request 1  [200  142ms]
curl -X GET 'https://api.example.com/booking/1' \
  -H 'Content-Type: application/json'

Response (200):
{
  "firstname": "John",
  "lastname": "Smith"
}
```

Auth headers (`Authorization`, `Cookie`, `X-XSRF-Token`) are redacted automatically.

## Custom API clients

Extend `RestClient` to add cookie-based auth, custom headers, or domain-specific methods:

```python
from api.rest_client import RestClient

class MyAppClient(RestClient):

    def login(self, username: str, password: str):
        resp = self.post("/auth", json={"username": username, "password": password})
        self.session.headers["Authorization"] = f"Bearer {resp.json()['token']}"
        return resp
```
