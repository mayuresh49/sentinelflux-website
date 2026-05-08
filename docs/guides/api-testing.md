# API Testing

## REST client

```python
import pytest
from api.rest_client import RestClient

@pytest.mark.api
def test_get_booking(rest_client):
    resp = rest_client.get("/booking/1")
    assert resp.status_code == 200
    assert resp.json()["firstname"]
```

The `rest_client` fixture is session-scoped and reads `config.api.rest_base_url`.

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
