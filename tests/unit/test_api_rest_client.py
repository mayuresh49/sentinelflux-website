"""Unit tests for api.rest_client.RestClient — pure helpers only (no network calls)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from api.rest_client import RestClient


class FakeResponse:
    """Minimal requests.Response stand-in."""
    def __init__(self, status_code=200, body=None, content_type="application/json"):
        self.status_code = status_code
        self._body = body or {"ok": True}
        self.headers = {"Content-Type": content_type}
        self.text = json.dumps(self._body)

    def json(self):
        return self._body


# ── URL building ──────────────────────────────────────────────────────────────

class TestBuildUrl:
    def test_strips_trailing_slash_from_base(self):
        rc = RestClient(base_url="https://api.example.com/")
        assert rc._build_url("/health") == "https://api.example.com/health"

    def test_strips_leading_slash_from_path(self):
        rc = RestClient(base_url="https://api.example.com")
        assert rc._build_url("/v1/users") == "https://api.example.com/v1/users"

    def test_no_double_slash(self):
        rc = RestClient(base_url="https://api.example.com/")
        url = rc._build_url("/resource")
        assert "//" not in url.replace("://", "")

    def test_path_without_leading_slash(self):
        rc = RestClient(base_url="https://api.example.com")
        assert rc._build_url("v1/users") == "https://api.example.com/v1/users"


# ── Path formatting ───────────────────────────────────────────────────────────

class TestFormatPath:
    def test_no_params_returns_path_unchanged(self):
        rc = RestClient(base_url="http://example.com")
        assert rc._format_path("/users", None) == "/users"

    def test_substitutes_path_params(self):
        rc = RestClient(base_url="http://example.com")
        result = rc._format_path("/users/{user_id}/posts/{post_id}", {"user_id": 42, "post_id": 7})
        assert result == "/users/42/posts/7"

    def test_empty_params_dict_is_fine(self):
        rc = RestClient(base_url="http://example.com")
        result = rc._format_path("/items", {})
        assert result == "/items"


# ── Log entry building ────────────────────────────────────────────────────────

class TestBuildLogEntry:
    def test_entry_has_required_keys(self):
        resp = FakeResponse(status_code=200, body={"id": 1})
        entry = RestClient._build_log_entry("get", "http://example.com/api", None, None, {}, resp, 42)
        assert entry["status"] == 200
        assert entry["elapsed_ms"] == 42
        assert "curl" in entry
        assert "response" in entry

    def test_curl_includes_method(self):
        resp = FakeResponse()
        entry = RestClient._build_log_entry("post", "http://example.com/api", {"key": "val"}, None, {}, resp, 10)
        assert "POST" in entry["curl"]

    def test_curl_includes_headers(self):
        resp = FakeResponse()
        entry = RestClient._build_log_entry(
            "get", "http://example.com/api", None, None,
            {"Authorization": "Bearer token"}, resp, 5
        )
        assert "Authorization" in entry["curl"]

    def test_curl_includes_payload(self):
        resp = FakeResponse()
        entry = RestClient._build_log_entry(
            "post", "http://example.com/api", {"name": "test"}, None, {}, resp, 10
        )
        assert "name" in entry["curl"] or "test" in entry["curl"]

    def test_response_json_is_parsed(self):
        resp = FakeResponse(body={"users": [1, 2, 3]})
        entry = RestClient._build_log_entry("get", "http://example.com", None, None, {}, resp, 0)
        assert entry["response"] == {"users": [1, 2, 3]}

    def test_response_fallback_to_text_on_json_error(self):
        class BadResponse:
            status_code = 500
            headers = {"Content-Type": "text/plain"}
            text = "internal server error"
            def json(self):
                raise ValueError("not json")

        entry = RestClient._build_log_entry("get", "http://example.com", None, None, {}, BadResponse(), 0)
        assert entry["response"] == "internal server error"

    def test_params_appended_to_url_in_curl(self):
        resp = FakeResponse()
        entry = RestClient._build_log_entry(
            "get", "http://example.com/api", None, {"page": 1, "limit": 20}, {}, resp, 0
        )
        assert "page=1" in entry["curl"] or "page" in entry["curl"]


# ── Request log ───────────────────────────────────────────────────────────────

class TestRequestLog:
    def test_clear_log_empties_list(self, tmp_path):
        rc = RestClient(base_url="http://example.com", data_dir=tmp_path)
        rc._request_log.append({"status": 200, "elapsed_ms": 1, "curl": "", "response": {}})
        rc.clear_log()
        assert rc._request_log == []

    def test_log_starts_empty(self):
        rc = RestClient(base_url="http://example.com")
        assert rc._request_log == []

    def test_multiple_clear_calls_are_safe(self):
        rc = RestClient(base_url="http://example.com")
        rc.clear_log()
        rc.clear_log()
        assert rc._request_log == []


# ── JSON loading ──────────────────────────────────────────────────────────────

class TestLoadJson:
    def test_load_existing_file(self, tmp_path):
        data = {"key": "value", "count": 42}
        (tmp_path / "test.json").write_text(json.dumps(data))
        rc = RestClient(base_url="http://example.com", data_dir=tmp_path)
        result = rc._load_json("test.json")
        assert result == data

    def test_load_missing_file_raises(self, tmp_path):
        rc = RestClient(base_url="http://example.com", data_dir=tmp_path)
        with pytest.raises(FileNotFoundError):
            rc._load_json("nonexistent.json")

    def test_load_json_with_nested_structure(self, tmp_path):
        data = {"endpoints": [{"path": "/users", "method": "GET"}]}
        (tmp_path / "endpoints.json").write_text(json.dumps(data))
        rc = RestClient(base_url="http://example.com", data_dir=tmp_path)
        result = rc._load_json("endpoints.json")
        assert result["endpoints"][0]["path"] == "/users"


# ── Schema validation ─────────────────────────────────────────────────────────

class TestSchemaValidation:
    def test_validate_schema_passes(self, tmp_path):
        schema = {
            "type": "object",
            "properties": {"id": {"type": "integer"}},
            "required": ["id"],
        }
        schema_dir = tmp_path / "schemas" / "rest_schemas"
        schema_dir.mkdir(parents=True)
        (schema_dir / "user.json").write_text(json.dumps(schema))
        rc = RestClient(base_url="http://example.com", data_dir=tmp_path)
        resp = FakeResponse(body={"id": 1})
        rc._validate_schema(resp, "user")  # Should not raise

    def test_validate_schema_fails_on_mismatch(self, tmp_path):
        schema = {
            "type": "object",
            "properties": {"id": {"type": "integer"}},
            "required": ["id"],
        }
        schema_dir = tmp_path / "schemas" / "rest_schemas"
        schema_dir.mkdir(parents=True)
        (schema_dir / "user.json").write_text(json.dumps(schema))
        rc = RestClient(base_url="http://example.com", data_dir=tmp_path)
        resp = FakeResponse(body={"name": "alice"})  # missing 'id'
        with pytest.raises(AssertionError, match="Schema validation failed"):
            rc._validate_schema(resp, "user")

    def test_validate_schema_rejects_non_json_content_type(self, tmp_path):
        schema = {"type": "object"}
        schema_dir = tmp_path / "schemas" / "rest_schemas"
        schema_dir.mkdir(parents=True)
        (schema_dir / "thing.json").write_text(json.dumps(schema))
        rc = RestClient(base_url="http://example.com", data_dir=tmp_path)
        resp = FakeResponse(content_type="text/html")
        with pytest.raises(AssertionError, match="Expected JSON response"):
            rc._validate_schema(resp, "thing")
