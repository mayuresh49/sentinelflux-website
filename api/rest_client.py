import json
import shlex
import time
from pathlib import Path
from typing import Any, Dict, Optional

import requests
from jsonschema import ValidationError, validate

_DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent


class RestClient:
    def __init__(self, base_url: str, logger=None, data_dir: Path = None):
        self.base_url = base_url.rstrip("/")
        self.logger = logger
        self._data_dir = Path(data_dir) if data_dir else _DEFAULT_DATA_DIR
        self._request_log: list[dict] = []

    def clear_log(self) -> None:
        self._request_log.clear()

    def _load_json(self, relative_path: str) -> Dict[str, Any]:
        path = self._data_dir / relative_path
        with path.open("r", encoding="utf-8") as stream:
            return json.load(stream)

    def _build_url(self, path: str) -> str:
        return f"{self.base_url}/{path.lstrip('/')}"

    def _format_path(self, path: str, path_params: Optional[Dict[str, Any]]) -> str:
        if path_params:
            return path.format(**path_params)
        return path

    def _log(self, message: str):
        if self.logger:
            self.logger.info(message)

    def _validate_schema(self, response: requests.Response, schema_name: str):
        ct = response.headers.get("Content-Type", "")
        if "application/json" not in ct:
            raise AssertionError(f"Expected JSON response but got Content-Type: {ct!r}")
        schema = self._load_json(f"schemas/rest_schemas/{schema_name}.json")
        try:
            validate(instance=response.json(), schema=schema)
        except ValidationError as exc:
            raise AssertionError(f"Schema validation failed for {schema_name}: {exc.message}")

    def _load_endpoint(self, endpoint_name: str) -> Dict[str, Any]:
        endpoints = self._load_json("api/endpoints/rest_endpoints.json")
        if endpoint_name not in endpoints:
            raise KeyError(f"Endpoint not found: {endpoint_name}")
        return endpoints[endpoint_name]

    def _load_payload(self, payload_name: str) -> Optional[Dict[str, Any]]:
        if not payload_name:
            return None
        return self._load_json(f"api/payloads/rest_payloads/{payload_name}.json")

    def _send_request(
        self,
        method: str,
        endpoint_name: str,
        payload_name: Optional[str] = None,
        path_params: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        schema_name: Optional[str] = None,
    ) -> requests.Response:
        endpoint = self._load_endpoint(endpoint_name)
        path = self._format_path(endpoint["path"], path_params)
        url = self._build_url(path)
        data = self._load_payload(payload_name) if payload_name else None

        self._log(f"Request {method.upper()} {url}")
        if data:
            self._log(f"Payload: {data}")

        t0 = time.monotonic()
        response = requests.request(method=method, url=url, json=data, params=params, headers=headers)
        elapsed_ms = round((time.monotonic() - t0) * 1000)

        self._log(f"Response code: {response.status_code}")
        self._request_log.append(self._build_log_entry(method, url, data, params, headers or {}, response, elapsed_ms))

        if schema_name:
            self._validate_schema(response, schema_name)

        return response

    @staticmethod
    def _build_log_entry(
        method: str,
        url: str,
        data: Optional[dict],
        params: Optional[dict],
        headers: dict,
        response: requests.Response,
        elapsed_ms: int,
    ) -> dict:
        parts = ["curl", "-X", method.upper()]
        for k, v in headers.items():
            parts += ["-H", f"{k}: {v}"]
        if data:
            parts += ["-H", "Content-Type: application/json", "-d", json.dumps(data)]
        if params:
            qs = "&".join(f"{k}={v}" for k, v in params.items())
            url = f"{url}?{qs}"
        parts.append(url)
        curl = " ".join(shlex.quote(p) for p in parts)

        try:
            resp_body = response.json()
        except Exception:
            resp_body = response.text

        return {
            "status": response.status_code,
            "elapsed_ms": elapsed_ms,
            "curl": curl,
            "response": resp_body,
        }

    def get(
        self,
        endpoint_name: str,
        path_params: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        schema_name: Optional[str] = None,
    ) -> requests.Response:
        return self._send_request("get", endpoint_name, None, path_params, params, headers, schema_name)

    def post(
        self,
        endpoint_name: str,
        payload_name: str,
        path_params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        schema_name: Optional[str] = None,
    ) -> requests.Response:
        return self._send_request("post", endpoint_name, payload_name, path_params, None, headers, schema_name)

    def put(
        self,
        endpoint_name: str,
        payload_name: str,
        path_params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        schema_name: Optional[str] = None,
    ) -> requests.Response:
        return self._send_request("put", endpoint_name, payload_name, path_params, None, headers, schema_name)

    def delete(
        self,
        endpoint_name: str,
        path_params: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        schema_name: Optional[str] = None,
    ) -> requests.Response:
        return self._send_request("delete", endpoint_name, None, path_params, params, headers, schema_name)
