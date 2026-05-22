"""Unit tests for core.audit_logger."""
from __future__ import annotations

import json

import pytest


@pytest.fixture
def audit_path(tmp_path, monkeypatch):
    path = tmp_path / "audit_log.json"
    import core.audit_logger as al
    monkeypatch.setattr(al, "_AUDIT_PATH", path)
    return path


class TestAuditLogger:
    def test_log_creates_file(self, audit_path):
        import core.audit_logger as al
        al.log("login", "alice@example.com", "Alice", "logged in")
        assert audit_path.exists()

    def test_log_appends_event(self, audit_path):
        import core.audit_logger as al
        al.log("login", "alice@example.com", "Alice", "logged in")
        events = json.loads(audit_path.read_text())
        assert len(events) == 1
        assert events[0]["type"] == "login"
        assert events[0]["user_email"] == "alice@example.com"
        assert events[0]["user_name"] == "Alice"
        assert events[0]["detail"] == "logged in"

    def test_log_event_has_id_and_timestamp(self, audit_path):
        import core.audit_logger as al
        al.log("config_change", "bob@example.com", "Bob", "updated config")
        events = json.loads(audit_path.read_text())
        ev = events[0]
        assert ev["id"].startswith("aud_")
        assert "timestamp" in ev

    def test_log_stores_ip_and_section(self, audit_path):
        import core.audit_logger as al
        al.log("login", "u@e.com", "U", "login", ip="1.2.3.4", section="auth")
        events = json.loads(audit_path.read_text())
        assert events[0]["ip"] == "1.2.3.4"
        assert events[0]["section"] == "auth"

    def test_multiple_events_accumulate(self, audit_path):
        import core.audit_logger as al
        al.log("login", "a@b.com", "A", "in")
        al.log("logout", "a@b.com", "A", "out")
        events = json.loads(audit_path.read_text())
        assert len(events) == 2

    def test_recent_returns_newest_first(self, audit_path):
        import core.audit_logger as al
        al.log("login", "a@b.com", "A", "first")
        al.log("logout", "a@b.com", "A", "second")
        recent = al.recent(limit=10)
        assert recent[0]["detail"] == "second"
        assert recent[1]["detail"] == "first"

    def test_recent_respects_limit(self, audit_path):
        import core.audit_logger as al
        for i in range(10):
            al.log("login", "u@e.com", "U", f"event-{i}")
        recent = al.recent(limit=3)
        assert len(recent) == 3

    def test_recent_empty_when_no_file(self, audit_path):
        import core.audit_logger as al
        assert al.recent() == []

    def test_max_entries_trim(self, audit_path):
        import core.audit_logger as al
        max_events = 2000  # _MAX_EVENTS constant
        for i in range(max_events + 5):
            al.log("login", "u@e.com", "U", f"event-{i}")
        events = json.loads(audit_path.read_text())
        assert len(events) == max_events

    def test_log_event_types(self, audit_path):
        import core.audit_logger as al
        for etype in ("login", "logout", "config_change"):
            al.log(etype, "u@e.com", "U", f"action: {etype}")
        recent = al.recent()
        types = {e["type"] for e in recent}
        assert types == {"login", "logout", "config_change"}

    def test_recent_handles_corrupt_file_gracefully(self, audit_path):
        audit_path.write_text("this is not json", encoding="utf-8")
        import core.audit_logger as al
        # Should not raise, returns empty list
        result = al.recent()
        assert result == []
