import json
import time
import requests

_REDACT = {"authorization", "cookie", "x-xsrf-token"}


class BookingClient:
    """Restful Booker API client with per-test request/response logging."""

    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json", "Accept": "application/json"})
        self._token: str | None = None
        self._username = username
        self._password = password
        self._request_log: list[dict] = []

    def clear_log(self):
        self._request_log.clear()

    def close(self):
        self.session.close()

    # ── auth ──────────────────────────────────────────────────────────────────

    def authenticate(self) -> str:
        resp = self._call("POST", "/auth", json={"username": self._username, "password": self._password})
        self._token = resp.json().get("token")
        return self._token

    def _auth_headers(self) -> dict:
        if not self._token:
            self.authenticate()
        return {"Cookie": f"token={self._token}"}

    # ── booking CRUD ──────────────────────────────────────────────────────────

    def get_booking_ids(self, params: dict = None) -> requests.Response:
        return self._call("GET", "/booking", params=params)

    def get_booking(self, booking_id: int) -> requests.Response:
        return self._call("GET", f"/booking/{booking_id}")

    def create_booking(self, payload: dict) -> requests.Response:
        return self._call("POST", "/booking", json=payload)

    def update_booking(self, booking_id: int, payload: dict) -> requests.Response:
        return self._call("PUT", f"/booking/{booking_id}", json=payload, headers=self._auth_headers())

    def partial_update_booking(self, booking_id: int, payload: dict) -> requests.Response:
        return self._call("PATCH", f"/booking/{booking_id}", json=payload, headers=self._auth_headers())

    def delete_booking(self, booking_id: int) -> requests.Response:
        return self._call("DELETE", f"/booking/{booking_id}", headers=self._auth_headers())

    # ── internals ─────────────────────────────────────────────────────────────

    def _call(self, method: str, path: str, **kwargs) -> requests.Response:
        url = self.base_url + path
        start = time.monotonic()
        resp = self.session.request(method, url, **kwargs)
        elapsed = round((time.monotonic() - start) * 1000)
        self._request_log.append({
            "curl": self._to_curl(method, url, kwargs),
            "status": resp.status_code,
            "elapsed_ms": elapsed,
            "response": resp.json() if resp.content and "json" in resp.headers.get("Content-Type", "") else resp.text,
        })
        return resp

    @staticmethod
    def _to_curl(method: str, url: str, kwargs: dict) -> str:
        parts = [f"curl -X {method.upper()} '{url}'"]
        for k, v in (kwargs.get("headers") or {}).items():
            if k.lower() in _REDACT:
                v = "***"
            parts.append(f"  -H '{k}: {v}'")
        if "json" in kwargs:
            body = json.dumps(kwargs["json"])
            parts.append(f"  -d '{body}'")
        return " \\\n".join(parts)
