"""Unit tests for core framework utilities."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from core.activity_log import ActivityLog
from core.approval_manager import ApprovalManager
from core.run_manager import RunManager

# ── ActivityLog ───────────────────────────────────────────────────────────────

class TestActivityLog:
    def test_append_and_all(self, tmp_path):
        log = ActivityLog(path=tmp_path / "activity_log.json")
        log.append(event_type="test_run", agent="pytest", domain="api",
                   status="success", summary="ok")
        entries = log.all()
        assert len(entries) == 1
        assert entries[0]["event_type"] == "test_run"
        assert entries[0]["agent"] == "pytest"

    def test_append_returns_id(self, tmp_path):
        log = ActivityLog(path=tmp_path / "activity_log.json")
        eid = log.append(event_type="pipeline_run", agent="pipeline", domain="web",
                         status="pending", summary="started")
        assert isinstance(eid, str) and len(eid) == 36  # UUID

    def test_filter_by_agent(self, tmp_path):
        log = ActivityLog(path=tmp_path / "activity_log.json")
        log.append(event_type="e", agent="alpha", domain="api", status="s", summary="s")
        log.append(event_type="e", agent="beta", domain="api", status="s", summary="s")
        result = log.filter(agent="alpha")
        assert len(result) == 1 and result[0]["agent"] == "alpha"

    def test_filter_by_product(self, tmp_path):
        log = ActivityLog(path=tmp_path / "activity_log.json")
        log.append(event_type="e", agent="a", domain="d", status="s", summary="s", product="orangehrm")
        log.append(event_type="e", agent="a", domain="d", status="s", summary="s", product="other")
        assert len(log.filter(product="orangehrm")) == 1

    def test_max_entries_trim(self, tmp_path):
        from core.activity_log import MAX_ENTRIES
        log = ActivityLog(path=tmp_path / "activity_log.json")
        for i in range(MAX_ENTRIES + 5):
            log.append(event_type="e", agent="a", domain="d", status="s", summary=str(i))
        assert len(log.all()) == MAX_ENTRIES

    def test_empty_path_returns_empty(self, tmp_path):
        log = ActivityLog(path=tmp_path / "nonexistent.json")
        assert log.all() == []

    def test_get_by_id(self, tmp_path):
        log = ActivityLog(path=tmp_path / "activity_log.json")
        eid = log.append(event_type="e", agent="a", domain="d", status="s", summary="s")
        entry = log.get(eid)
        assert entry is not None and entry["id"] == eid

    def test_requires_human_filter(self, tmp_path):
        log = ActivityLog(path=tmp_path / "activity_log.json")
        log.append(event_type="e", agent="a", domain="d", status="s", summary="s", requires_human=True)
        log.append(event_type="e", agent="a", domain="d", status="s", summary="s", requires_human=False)
        assert len(log.filter(requires_human=True)) == 1
        assert len(log.filter(requires_human=False)) == 1


# ── ApprovalManager ───────────────────────────────────────────────────────────

class TestApprovalManager:
    def test_submit_and_pending(self, tmp_path):
        am = ApprovalManager(path=tmp_path / "approvals.yaml")
        aid = am.submit(approval_type="quarantine", title="flaky test", domain="api")
        pending = am.pending()
        assert len(pending) == 1
        assert pending[0]["id"] == aid

    def test_resolve_approve(self, tmp_path):
        am = ApprovalManager(path=tmp_path / "approvals.yaml")
        aid = am.submit(approval_type="quarantine", title="t", domain="api")
        result = am.resolve(aid, decision="approved")
        assert result is True
        assert len(am.pending()) == 0
        resolved = am.resolved()
        assert len(resolved) == 1
        assert resolved[0]["decision"] == "approved"

    def test_resolve_not_found(self, tmp_path):
        am = ApprovalManager(path=tmp_path / "approvals.yaml")
        assert am.resolve("nonexistent-id", decision="approved") is False

    def test_pending_type_filter(self, tmp_path):
        am = ApprovalManager(path=tmp_path / "approvals.yaml")
        am.submit(approval_type="quarantine", title="q", domain="api")
        am.submit(approval_type="coverage_gap", title="c", domain="web")
        assert len(am.pending(approval_type="quarantine")) == 1
        assert len(am.pending(approval_type="coverage_gap")) == 1
        assert len(am.pending()) == 2

    def test_get(self, tmp_path):
        am = ApprovalManager(path=tmp_path / "approvals.yaml")
        aid = am.submit(approval_type="quarantine", title="t", domain="api", product="acme")
        item = am.get(aid)
        assert item is not None and item["product"] == "acme"

    def test_empty_path_returns_empty(self, tmp_path):
        am = ApprovalManager(path=tmp_path / "no_approvals.yaml")
        assert am.pending() == []
        assert am.resolved() == []


# ── RunManager ────────────────────────────────────────────────────────────────

class TestRunManager:
    def test_create_and_get_run(self, tmp_path):
        rm = RunManager(db_path=tmp_path / "test.db")
        run = rm.create_run(product="acme", domain="api")
        assert run["status"] == "queued"
        assert run["product"] == "acme"
        fetched = rm.get_run(run["id"])
        assert fetched is not None and fetched["id"] == run["id"]

    def test_patch_run(self, tmp_path):
        rm = RunManager(db_path=tmp_path / "test.db")
        run = rm.create_run(product="acme", domain="web")
        updated = rm.patch_run(run["id"], status="completed", passed=10)
        assert updated["status"] == "completed"
        assert updated["passed"] == 10

    def test_create_and_delete_schedule(self, tmp_path):
        rm = RunManager(db_path=tmp_path / "test.db")
        sched = rm.create_schedule("nightly", "acme", "api", hour=2, minute=0, days=["mon"])
        assert len(rm.all_schedules()) == 1
        rm.delete_schedule(sched["id"])
        assert len(rm.all_schedules()) == 0

    def test_max_runs_cap(self, tmp_path):
        from core.run_manager import _MAX_RUNS
        rm = RunManager(db_path=tmp_path / "test.db")
        for _ in range(_MAX_RUNS + 3):
            rm.create_run(product="p", domain="api")
        assert len(rm.all_runs()) == _MAX_RUNS


# ── RunManager.is_due ─────────────────────────────────────────────────────────

class TestRunManagerIsDue:
    def _now(self, weekday: int, hour: int, minute: int) -> datetime:
        """Build a UTC datetime with specific weekday/hour/minute."""
        # 2026-05-11 is a Monday (weekday=0), so offset from there
        base_monday = datetime(2026, 5, 11, tzinfo=timezone.utc)
        from datetime import timedelta
        return base_monday.replace(hour=hour, minute=minute) + timedelta(days=weekday)

    def _sched(self, days, hour=2, minute=0, enabled=True, last_run_at=None):
        return {"enabled": enabled, "days": days, "hour": hour, "minute": minute, "last_run_at": last_run_at}

    def test_due_when_conditions_match(self):
        now = self._now(weekday=0, hour=2, minute=0)  # Monday 02:00
        assert RunManager.is_due(self._sched(["mon"], hour=2, minute=0), now)

    def test_not_due_wrong_day(self):
        now = self._now(weekday=1, hour=2, minute=0)  # Tuesday
        assert not RunManager.is_due(self._sched(["mon"]), now)

    def test_not_due_wrong_hour(self):
        now = self._now(weekday=0, hour=3, minute=0)  # Monday 03:00
        assert not RunManager.is_due(self._sched(["mon"], hour=2), now)

    def test_not_due_already_ran_today(self):
        now = self._now(weekday=0, hour=2, minute=0)
        last = now.isoformat()
        assert not RunManager.is_due(self._sched(["mon"], last_run_at=last), now)

    def test_not_due_when_disabled(self):
        now = self._now(weekday=0, hour=2, minute=0)
        assert not RunManager.is_due(self._sched(["mon"], enabled=False), now)

    def test_due_ran_yesterday(self):
        from datetime import timedelta
        now = self._now(weekday=0, hour=2, minute=0)
        yesterday = (now - timedelta(days=1)).isoformat()
        assert RunManager.is_due(self._sched(["mon"], last_run_at=yesterday), now)
