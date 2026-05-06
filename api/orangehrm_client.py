import requests

BASE_URL = "https://opensource-demo.orangehrmlive.com"
API_V2 = "/web/index.php/api/v2"


class OrangeHRMClient:
    def __init__(self):
        self._session = requests.Session()
        self._session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json",
        })
        self._xsrf = ""

    def login(self, username: str = "Admin", password: str = "admin123") -> requests.Response:
        # Prime session to receive CSRF cookie
        self._session.get(f"{BASE_URL}/web/index.php/auth/login")
        self._xsrf = self._session.cookies.get("XSRF-TOKEN", "")
        resp = self._session.post(
            f"{BASE_URL}/web/index.php/auth/validateCredentials",
            json={"username": username, "password": password},
            headers={"X-XSRF-TOKEN": self._xsrf},
            allow_redirects=True,
        )
        # Refresh XSRF after auth
        self._xsrf = self._session.cookies.get("XSRF-TOKEN", self._xsrf)
        self._session.headers["X-XSRF-TOKEN"] = self._xsrf
        return resp

    def get(self, path: str, **kw) -> requests.Response:
        return self._session.get(f"{BASE_URL}{API_V2}{path}", **kw)

    def post(self, path: str, json=None, **kw) -> requests.Response:
        return self._session.post(f"{BASE_URL}{API_V2}{path}", json=json, **kw)

    def put(self, path: str, json=None, **kw) -> requests.Response:
        return self._session.put(f"{BASE_URL}{API_V2}{path}", json=json, **kw)

    def delete(self, path: str, json=None, **kw) -> requests.Response:
        return self._session.delete(f"{BASE_URL}{API_V2}{path}", json=json, **kw)

    def close(self):
        self._session.close()
