import json
import shlex
import time

import requests

_REDACT = {"x-xsrf-token", "cookie", "authorization"}


def _to_curl(prep: requests.PreparedRequest, body) -> str:
    parts = [f"curl -X {prep.method}"]
    for k, v in prep.headers.items():
        if k.lower() in _REDACT:
            v = "<redacted>"
        parts.append(f"  -H {shlex.quote(f'{k}: {v}')}")
    if body:
        parts.append(f"  -d {shlex.quote(json.dumps(body) if isinstance(body, dict) else str(body))}")
    parts.append(f"  {shlex.quote(prep.url)}")
    return " \\\n".join(parts)


class OrangeHRMClient:
    def __init__(self, api_base_url: str):
        self._api_base_url = api_base_url
        self._session = requests.Session()
        self._session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json",
        })
        self._xsrf = ""
        self._request_log: list[dict] = []

    @classmethod
    def from_playwright_cookies(cls, cookies: list, api_base_url: str) -> "OrangeHRMClient":
        instance = cls(api_base_url)
        for c in cookies:
            instance._session.cookies.set(
                c["name"], c["value"], domain=c.get("domain", "")
            )
        instance._xsrf = instance._session.cookies.get("XSRF-TOKEN", "")
        if instance._xsrf:
            instance._session.headers["X-XSRF-TOKEN"] = instance._xsrf
        return instance

    def _call(self, method: str, path: str, json_body=None, **kw) -> requests.Response:
        url = f"{self._api_base_url}{path}"
        t0 = time.monotonic()
        resp = getattr(self._session, method)(url, json=json_body, **kw)
        elapsed = round((time.monotonic() - t0) * 1000)
        try:
            resp_body = resp.json()
        except Exception:
            resp_body = resp.text
        self._request_log.append({
            "curl": _to_curl(resp.request, json_body),
            "status": resp.status_code,
            "elapsed_ms": elapsed,
            "response": resp_body,
        })
        return resp

    def clear_log(self):
        self._request_log.clear()

    def get(self, path: str, **kw) -> requests.Response:
        return self._call("get", path, **kw)

    def post(self, path: str, json=None, **kw) -> requests.Response:
        return self._call("post", path, json_body=json, **kw)

    def put(self, path: str, json=None, **kw) -> requests.Response:
        return self._call("put", path, json_body=json, **kw)

    def delete(self, path: str, json=None, **kw) -> requests.Response:
        return self._call("delete", path, json_body=json, **kw)

    def close(self):
        self._session.close()
