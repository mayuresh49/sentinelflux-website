"""Unit tests for core.insights_manager.InsightsManager and core.roadmap_manager.RoadmapManager."""
from __future__ import annotations

import sqlite3
import uuid

import pytest

from core.db import apply_schema


@pytest.fixture
def db_conn():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    apply_schema(conn)
    return conn


@pytest.fixture
def db(db_conn, monkeypatch):
    monkeypatch.setattr("core.insights_manager.get_conn", lambda: db_conn)
    monkeypatch.setattr("core.roadmap_manager.get_conn", lambda: db_conn)
    return db_conn


# ── InsightsManager ───────────────────────────────────────────────────────────

class TestInsightsManager:
    def _im(self):
        from core.insights_manager import InsightsManager
        return InsightsManager()

    def test_save_and_list_insights(self, db):
        im = self._im()
        im.save_insights("qa_architect", [
            {"title": "Flaky login test", "description": "high failure rate", "recommendation": "stabilise fixture"},
        ], run_id="run-1")
        rows = im.list_insights()
        assert len(rows) == 1
        assert rows[0]["title"] == "Flaky login test"
        assert rows[0]["status"] == "active"

    def test_save_replaces_active_insights_for_agent(self, db):
        im = self._im()
        im.save_insights("qa_architect", [{"title": "Old"}], run_id="r1")
        im.save_insights("qa_architect", [{"title": "New"}], run_id="r2")
        rows = im.list_insights(agent_type="qa_architect")
        assert len(rows) == 1
        assert rows[0]["title"] == "New"

    def test_save_preserves_other_statuses(self, db):
        im = self._im()
        im.save_insights("qa_architect", [{"title": "Planned insight"}], run_id="r1")
        rows = im.list_insights(agent_type="qa_architect")
        im.update_status(rows[0]["id"], "planned")
        im.save_insights("qa_architect", [{"title": "Fresh active"}], run_id="r2")
        all_rows = im.list_insights(agent_type="qa_architect")
        statuses = {r["status"] for r in all_rows}
        assert "planned" in statuses
        assert "active" in statuses

    def test_list_insights_filter_agent_type(self, db):
        im = self._im()
        im.save_insights("qa_architect", [{"title": "QA"}], run_id="r1")
        im.save_insights("product_manager", [{"title": "PM"}], run_id="r2")
        qa = im.list_insights(agent_type="qa_architect")
        pm = im.list_insights(agent_type="product_manager")
        assert len(qa) == 1
        assert len(pm) == 1
        assert qa[0]["title"] == "QA"

    def test_list_insights_filter_status(self, db):
        im = self._im()
        im.save_insights("qa_architect", [{"title": "A"}, {"title": "B"}], run_id="r1")
        rows = im.list_insights(agent_type="qa_architect")
        im.update_status(rows[0]["id"], "planned")
        active = im.list_insights(status="active")
        planned = im.list_insights(status="planned")
        assert len(active) == 1
        assert len(planned) == 1

    def test_update_status_valid(self, db):
        im = self._im()
        im.save_insights("qa_architect", [{"title": "T"}], run_id="r1")
        row = im.list_insights()[0]
        result = im.update_status(row["id"], "punted")
        assert result is True
        updated = im.list_insights()[0]
        assert updated["status"] == "punted"

    def test_update_status_invalid(self, db):
        im = self._im()
        result = im.update_status("any-id", "bad_status")
        assert result is False

    def test_update_status_nonexistent(self, db):
        im = self._im()
        result = im.update_status("no-such-id", "planned")
        assert result is False

    def test_latest_runs_returns_all_agent_types(self, db):
        im = self._im()
        runs = im.latest_runs()
        assert "qa_architect" in runs
        assert "product_manager" in runs
        assert "dev_architect" in runs
        assert "ux_architect" in runs

    def test_latest_runs_populated(self, db):
        im = self._im()
        im.save_insights("qa_architect", [{"title": "T"}], run_id="r1")
        runs = im.latest_runs()
        assert runs["qa_architect"] is not None
        assert runs["product_manager"] is None

    def test_delete_insights_by_agent(self, db):
        im = self._im()
        im.save_insights("qa_architect", [{"title": "A"}, {"title": "B"}], run_id="r1")
        deleted = im.delete_insights_by_agent("qa_architect")
        assert deleted == 2
        assert im.list_insights(agent_type="qa_architect") == []

    def test_delete_insights_leaves_other_agents(self, db):
        im = self._im()
        im.save_insights("qa_architect", [{"title": "QA"}], run_id="r1")
        im.save_insights("product_manager", [{"title": "PM"}], run_id="r2")
        im.delete_insights_by_agent("qa_architect")
        assert len(im.list_insights(agent_type="product_manager")) == 1

    def test_save_defaults(self, db):
        im = self._im()
        im.save_insights("dev_architect", [{}], run_id="r1")
        row = im.list_insights()[0]
        assert row["category"] == "opportunity"
        assert row["priority"] == "medium"
        assert row["title"] == ""


# ── RoadmapManager ────────────────────────────────────────────────────────────

class TestRoadmapManager:
    def _rm(self):
        from core.roadmap_manager import RoadmapManager
        return RoadmapManager()

    def _insight(self, title="Test insight"):
        return {
            "id": str(uuid.uuid4()),
            "agent_type": "qa_architect",
            "title": title,
            "description": "desc",
            "recommendation": "fix it",
            "category": "opportunity",
            "priority": "high",
        }

    def test_create_item(self, db):
        rm = self._rm()
        ins = self._insight("Login issue")
        item_id = rm.create_item(ins, cto_rationale="critical path")
        assert isinstance(item_id, str)
        items = rm.list_items()
        assert len(items) == 1
        assert items[0]["title"] == "Login issue"
        assert items[0]["cto_rationale"] == "critical path"
        assert items[0]["status"] == "planned"

    def test_create_item_duplicate_insight_is_idempotent(self, db):
        rm = self._rm()
        ins = self._insight()
        id1 = rm.create_item(ins, cto_rationale="first")
        id2 = rm.create_item(ins, cto_rationale="second")
        assert id1 == id2
        assert len(rm.list_items()) == 1

    def test_list_items_filter_status(self, db):
        rm = self._rm()
        ins1 = self._insight("A")
        ins2 = self._insight("B")
        id1 = rm.create_item(ins1, cto_rationale="r")
        rm.create_item(ins2, cto_rationale="r")
        rm.update_status(id1, "done")
        planned = rm.list_items(status="planned")
        done = rm.list_items(status="done")
        assert len(planned) == 1
        assert len(done) == 1

    def test_update_status_to_done(self, db):
        rm = self._rm()
        ins = self._insight()
        item_id = rm.create_item(ins, cto_rationale="r")
        result = rm.update_status(item_id, "done")
        assert result is True
        items = rm.list_items(status="done")
        assert len(items) == 1
        assert items[0]["done_at"] is not None

    def test_update_status_invalid(self, db):
        rm = self._rm()
        assert rm.update_status("any-id", "invalid_status") is False

    def test_update_status_nonexistent(self, db):
        rm = self._rm()
        result = rm.update_status("no-such-id", "done")
        assert result is False

    def test_delete_item_returns_source_insight_id(self, db):
        rm = self._rm()
        ins = self._insight()
        item_id = rm.create_item(ins, cto_rationale="r")
        source_id = rm.delete_item(item_id)
        assert source_id == ins["id"]
        assert rm.list_items() == []

    def test_delete_item_nonexistent(self, db):
        rm = self._rm()
        assert rm.delete_item("no-such-id") is None

    def test_latest_run_at_none_when_empty(self, db):
        rm = self._rm()
        assert rm.latest_run_at() is None

    def test_latest_run_at_populated(self, db):
        rm = self._rm()
        rm.create_item(self._insight(), cto_rationale="r")
        ts = rm.latest_run_at()
        assert ts is not None

    def test_list_items_ordered_by_promoted_at_desc(self, db):
        rm = self._rm()
        ins1 = self._insight("First")
        ins2 = self._insight("Second")
        rm.create_item(ins1, cto_rationale="r")
        rm.create_item(ins2, cto_rationale="r")
        items = rm.list_items()
        # Most recently created appears first
        assert items[0]["title"] == "Second"
