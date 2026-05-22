"""Unit tests for core.bug_manager.BugManager."""
from __future__ import annotations

import sqlite3

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
def bm(db_conn, monkeypatch):
    monkeypatch.setattr("core.bug_manager.get_conn", lambda: db_conn)
    from core.bug_manager import BugManager
    return BugManager()


# ── CRUD ──────────────────────────────────────────────────────────────────────

class TestBugCRUD:
    def test_create_returns_dict_with_id(self, bm):
        bug = bm.create(product="acme", title="Login breaks on Safari")
        assert bug["id"]
        assert bug["product"] == "acme"
        assert bug["title"] == "Login breaks on Safari"
        assert bug["state"] == "new"

    def test_create_auto_assigns_bug_number(self, bm):
        b1 = bm.create(product="acme", title="First")
        b2 = bm.create(product="acme", title="Second")
        assert b1["bug_number"].startswith("BUG-AC-001")
        assert b2["bug_number"].startswith("BUG-AC-002")

    def test_create_per_product_sequence(self, bm):
        b_acme = bm.create(product="acme", title="a")
        b_other = bm.create(product="other", title="b")
        assert b_acme["bug_seq"] == 1
        assert b_other["bug_seq"] == 1  # sequence resets per product

    def test_get_returns_none_for_missing(self, bm):
        assert bm.get("nonexistent-id") is None

    def test_get_returns_bug(self, bm):
        bug = bm.create(product="acme", title="Found")
        fetched = bm.get(bug["id"])
        assert fetched is not None
        assert fetched["title"] == "Found"

    def test_list_bugs_all(self, bm):
        bm.create(product="acme", title="A")
        bm.create(product="acme", title="B")
        assert len(bm.list_bugs()) == 2

    def test_list_bugs_filter_product(self, bm):
        bm.create(product="acme", title="A")
        bm.create(product="other", title="B")
        assert len(bm.list_bugs(product="acme")) == 1
        assert len(bm.list_bugs(product="other")) == 1

    def test_list_bugs_filter_state(self, bm):
        bm.create(product="acme", title="A")
        bm.create(product="acme", title="B")
        assert len(bm.list_bugs(state="new")) == 2
        assert len(bm.list_bugs(state="open")) == 0

    def test_list_bugs_filter_priority(self, bm):
        bm.create(product="acme", title="A", priority="P1")
        bm.create(product="acme", title="B", priority="P2")
        assert len(bm.list_bugs(priority="P1")) == 1

    def test_list_bugs_filter_assignee(self, bm):
        bm.create(product="acme", title="A", assignee="alice")
        bm.create(product="acme", title="B", assignee="bob")
        assert len(bm.list_bugs(assignee="alice")) == 1

    def test_patch_updates_fields(self, bm):
        bug = bm.create(product="acme", title="Original")
        updated = bm.patch(bug["id"], title="Updated Title", priority="P1")
        assert updated["title"] == "Updated Title"
        assert updated["priority"] == "P1"

    def test_patch_tags_as_list(self, bm):
        bug = bm.create(product="acme", title="Tagged")
        updated = bm.patch(bug["id"], tags=["ui", "regression"])
        assert updated["tags"] == ["ui", "regression"]

    def test_patch_ignores_unknown_fields(self, bm):
        bug = bm.create(product="acme", title="T")
        result = bm.patch(bug["id"], nonexistent_field="x")
        assert result["title"] == "T"  # unchanged, no error

    def test_delete_removes_bug(self, bm):
        bug = bm.create(product="acme", title="Delete me")
        assert bm.delete(bug["id"]) is True
        assert bm.get(bug["id"]) is None

    def test_delete_nonexistent_returns_false(self, bm):
        assert bm.delete("no-such-id") is False

    def test_delete_also_removes_comments(self, bm):
        bug = bm.create(product="acme", title="With comments")
        bm.add_comment(bug["id"], author="alice", body="note")
        bm.delete(bug["id"])
        assert bm.list_comments(bug["id"]) == []

    def test_create_with_tags(self, bm):
        bug = bm.create(product="acme", title="T", tags=["smoke", "auth"])
        assert bug["tags"] == ["smoke", "auth"]

    def test_create_stores_all_fields(self, bm):
        bug = bm.create(
            product="acme",
            title="Full",
            description="desc",
            reporter="alice",
            priority="P1",
            severity="critical",
            bug_type="security",
            component="auth",
            environment="staging",
            build_version="1.2.3",
            assignee="bob",
            steps_to_reproduce="click X",
            expected_result="success",
            actual_result="error",
        )
        assert bug["description"] == "desc"
        assert bug["reporter"] == "alice"
        assert bug["severity"] == "critical"
        assert bug["component"] == "auth"


# ── State machine ─────────────────────────────────────────────────────────────

class TestBugTransitions:
    def test_valid_transition_new_to_open(self, bm):
        bug = bm.create(product="acme", title="T")
        updated = bm.transition(bug["id"], "open", changed_by="alice")
        assert updated["state"] == "open"

    def test_transition_records_history(self, bm):
        bug = bm.create(product="acme", title="T")
        bm.transition(bug["id"], "open", changed_by="alice", comment="starting work")
        history = bm.get_history(bug["id"])
        assert len(history) == 1
        assert history[0]["from_state"] == "new"
        assert history[0]["to_state"] == "open"
        assert history[0]["changed_by"] == "alice"
        assert history[0]["comment"] == "starting work"

    def test_invalid_transition_raises(self, bm):
        bug = bm.create(product="acme", title="T")
        with pytest.raises(ValueError, match="Cannot transition"):
            bm.transition(bug["id"], "resolved", changed_by="alice")

    def test_transition_nonexistent_bug_raises(self, bm):
        with pytest.raises(ValueError, match="not found"):
            bm.transition("no-such-id", "open", changed_by="alice")

    def test_transition_sets_resolved_at(self, bm):
        bug = bm.create(product="acme", title="T")
        bm.transition(bug["id"], "open", changed_by="alice")
        bm.transition(bug["id"], "in_progress", changed_by="alice")
        resolved = bm.transition(bug["id"], "resolved", changed_by="alice")
        assert resolved["resolved_at"] is not None

    def test_transition_sets_closed_at(self, bm):
        bug = bm.create(product="acme", title="T")
        bm.transition(bug["id"], "open", changed_by="alice")
        bm.transition(bug["id"], "in_progress", changed_by="alice")
        bm.transition(bug["id"], "resolved", changed_by="alice")
        closed = bm.transition(bug["id"], "closed", changed_by="alice")
        assert closed["closed_at"] is not None

    def test_allowed_transitions_from_new(self, bm):
        bug = bm.create(product="acme", title="T")
        allowed = bm.allowed_transitions(bug["id"])
        assert "open" in allowed
        assert "deferred" in allowed
        assert "wont_fix" in allowed

    def test_allowed_transitions_empty_for_nonexistent(self, bm):
        assert bm.allowed_transitions("no-such-id") == []

    def test_full_lifecycle(self, bm):
        bug = bm.create(product="acme", title="Flow")
        bm.transition(bug["id"], "open", changed_by="a")
        bm.transition(bug["id"], "in_progress", changed_by="a")
        bm.transition(bug["id"], "resolved", changed_by="a")
        bm.transition(bug["id"], "closed", changed_by="a")
        history = bm.get_history(bug["id"])
        assert len(history) == 4


# ── Comments ──────────────────────────────────────────────────────────────────

class TestBugComments:
    def test_add_and_list_comments(self, bm):
        bug = bm.create(product="acme", title="T")
        comment = bm.add_comment(bug["id"], author="alice", body="looks like a UI bug")
        comments = bm.list_comments(bug["id"])
        assert len(comments) == 1
        assert comments[0]["id"] == comment["id"]
        assert comments[0]["author"] == "alice"
        assert comments[0]["body"] == "looks like a UI bug"

    def test_multiple_comments_ordered(self, bm):
        bug = bm.create(product="acme", title="T")
        bm.add_comment(bug["id"], author="alice", body="first")
        bm.add_comment(bug["id"], author="bob", body="second")
        comments = bm.list_comments(bug["id"])
        assert len(comments) == 2
        assert comments[0]["body"] == "first"
        assert comments[1]["body"] == "second"

    def test_list_comments_empty(self, bm):
        bug = bm.create(product="acme", title="T")
        assert bm.list_comments(bug["id"]) == []

    def test_comments_isolated_per_bug(self, bm):
        b1 = bm.create(product="acme", title="Bug 1")
        b2 = bm.create(product="acme", title="Bug 2")
        bm.add_comment(b1["id"], author="a", body="for b1")
        assert bm.list_comments(b2["id"]) == []


# ── Artifacts ─────────────────────────────────────────────────────────────────

class TestBugArtifacts:
    def test_add_and_list_artifact(self, bm):
        bug = bm.create(product="acme", title="T")
        art = bm.add_artifact(
            bug_id=bug["id"],
            filename="log.txt",
            artifact_type="document",
            mime_type="text/plain",
            size_bytes=1024,
            storage_path="data/bugs/acme/log.txt",
            uploaded_by="alice",
        )
        arts = bm.list_artifacts(bug["id"])
        assert len(arts) == 1
        assert arts[0]["filename"] == "log.txt"
        assert arts[0]["uploaded_by"] == "alice"

    def test_get_artifact(self, bm):
        bug = bm.create(product="acme", title="T")
        art = bm.add_artifact(
            bug_id=bug["id"], filename="screen.png", artifact_type="screenshot",
            mime_type="image/png", size_bytes=512, storage_path="data/bugs/acme/screen.png",
        )
        fetched = bm.get_artifact(art["id"])
        assert fetched is not None
        assert fetched["filename"] == "screen.png"

    def test_get_artifact_missing(self, bm):
        assert bm.get_artifact("no-such-id") is None

    def test_delete_artifact(self, bm):
        bug = bm.create(product="acme", title="T")
        art = bm.add_artifact(
            bug_id=bug["id"], filename="f.txt", artifact_type="document",
            mime_type="text/plain", size_bytes=100, storage_path="no/real/path.txt",
        )
        result = bm.delete_artifact(art["id"])
        assert result is True
        assert bm.get_artifact(art["id"]) is None

    def test_delete_artifact_nonexistent(self, bm):
        assert bm.delete_artifact("no-such-id") is False


# ── Stats ─────────────────────────────────────────────────────────────────────

class TestBugStats:
    def test_counts_by_state_empty(self, bm):
        assert bm.counts_by_state() == {}

    def test_counts_by_state_multiple(self, bm):
        bm.create(product="acme", title="A")
        bm.create(product="acme", title="B")
        bm.create(product="acme", title="C")
        counts = bm.counts_by_state()
        assert counts.get("new", 0) == 3

    def test_counts_by_state_with_product_filter(self, bm):
        bm.create(product="acme", title="A")
        bm.create(product="other", title="B")
        counts = bm.counts_by_state(product="acme")
        assert sum(counts.values()) == 1

    def test_product_statuses_defaults(self, bm):
        statuses = bm.get_product_statuses("acme")
        names = [s["name"] for s in statuses]
        assert "new" in names
        assert "open" in names
        assert "resolved" in names
        assert "closed" in names

    def test_closed_state_names(self, bm):
        closed = bm.closed_state_names("acme")
        assert "resolved" in closed
        assert "closed" in closed
        assert "new" not in closed
