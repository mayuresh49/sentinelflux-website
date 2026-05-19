from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from core.db import get_conn
from utils.paths import ROOT

_BUGS_DIR = ROOT / "data" / "bugs"
_CONFIG_PATH = ROOT / "data" / "config.yaml"

_DEFAULT_STATUSES: list[dict] = [
    {"name": "new",         "label": "New",         "color": "sky"},
    {"name": "open",        "label": "Open",        "color": "amber"},
    {"name": "in_progress", "label": "In Progress", "color": "violet"},
    {"name": "resolved",    "label": "Resolved",    "color": "emerald"},
    {"name": "closed",      "label": "Closed",      "color": "slate"},
    {"name": "deferred",    "label": "Deferred",    "color": "yellow"},
    {"name": "wont_fix",    "label": "Won't Fix",   "color": "red"},
]

# Default state transitions: state → set of allowed next states
_DEFAULT_TRANSITIONS: dict[str, set[str]] = {
    "new":         {"open", "deferred", "wont_fix"},
    "open":        {"in_progress", "deferred", "wont_fix"},
    "in_progress": {"resolved", "open"},
    "resolved":    {"closed", "open"},
    "closed":      {"open"},
    "deferred":    {"open"},
    "wont_fix":    set(),
}


def _get_statuses(product: str | None = None) -> list[dict]:
    """Return configured statuses for a product, falling back to defaults."""
    if not product or not _CONFIG_PATH.exists():
        return _DEFAULT_STATUSES
    try:
        cfg = yaml.safe_load(_CONFIG_PATH.read_text(encoding="utf-8")) or {}
        for p in cfg.get("products", []):
            if p["name"] == product:
                raw = p.get("bug_statuses")
                if raw:
                    return raw
    except Exception:
        pass
    return _DEFAULT_STATUSES


def _get_transitions(product: str | None = None) -> dict[str, set[str]]:
    """Return the configured transitions for a product, falling back to defaults."""
    if not product or not _CONFIG_PATH.exists():
        return _DEFAULT_TRANSITIONS
    try:
        cfg = yaml.safe_load(_CONFIG_PATH.read_text(encoding="utf-8")) or {}
        for p in cfg.get("products", []):
            if p["name"] == product:
                raw = p.get("bug_transitions")
                if raw:
                    return {state: set(targets) for state, targets in raw.items()}
    except Exception:
        pass
    return _DEFAULT_TRANSITIONS

_SEVERITY_VALUES = {"blocker", "critical", "major", "minor", "trivial"}
_TYPE_VALUES = {"functional", "performance", "security", "ui", "regression", "data"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _row(r) -> dict:
    d = dict(r)
    for key in ("tags",):
        if isinstance(d.get(key), str):
            try:
                d[key] = json.loads(d[key])
            except Exception:
                d[key] = []
    return d


class BugManager:
    def _conn(self):
        return get_conn()

    # ── Bug CRUD ──────────────────────────────────────────────────────────────

    def create(
        self,
        product: str,
        title: str,
        description: str = "",
        reporter: str = "",
        priority: str = "P2",
        severity: str = "major",
        bug_type: str = "functional",
        component: str = "",
        environment: str = "",
        build_version: str = "",
        assignee: str = "",
        steps_to_reproduce: str = "",
        expected_result: str = "",
        actual_result: str = "",
        tags: list[str] | None = None,
        linked_tc_id: str = "",
        linked_run_id: str = "",
        linked_plan_id: str = "",
    ) -> dict:
        bug_id = str(uuid.uuid4())
        now = _now()
        conn = self._conn()
        conn.execute(
            """INSERT INTO bugs
               (id, product, title, description, priority, severity, state, bug_type,
                component, environment, build_version, reporter, assignee,
                steps_to_reproduce, expected_result, actual_result,
                tags, linked_tc_id, linked_run_id, linked_plan_id,
                created_at, updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                bug_id, product, title, description, priority, severity, "new", bug_type,
                component, environment, build_version, reporter, assignee,
                steps_to_reproduce, expected_result, actual_result,
                json.dumps(tags or []), linked_tc_id, linked_run_id, linked_plan_id,
                now, now,
            ),
        )
        conn.commit()
        return self.get(bug_id)  # type: ignore[return-value]

    def get(self, bug_id: str) -> dict | None:
        row = self._conn().execute("SELECT * FROM bugs WHERE id = ?", (bug_id,)).fetchone()
        return _row(row) if row else None

    def list_bugs(
        self,
        product: str | None = None,
        state: str | None = None,
        priority: str | None = None,
        assignee: str | None = None,
        component: str | None = None,
        linked_run_id: str | None = None,
        linked_tc_id: str | None = None,
    ) -> list[dict]:
        clauses, params = [], []
        if product:
            clauses.append("product = ?"); params.append(product)
        if state:
            clauses.append("state = ?"); params.append(state)
        if priority:
            clauses.append("priority = ?"); params.append(priority)
        if assignee:
            clauses.append("assignee = ?"); params.append(assignee)
        if component:
            clauses.append("component = ?"); params.append(component)
        if linked_run_id:
            clauses.append("linked_run_id = ?"); params.append(linked_run_id)
        if linked_tc_id:
            clauses.append("linked_tc_id = ?"); params.append(linked_tc_id)
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        rows = self._conn().execute(
            f"SELECT * FROM bugs {where} ORDER BY created_at DESC", params
        ).fetchall()
        return [_row(r) for r in rows]

    def patch(self, bug_id: str, **fields: Any) -> dict | None:
        allowed = {
            "title", "description", "priority", "severity", "bug_type", "component",
            "environment", "build_version", "assignee", "steps_to_reproduce",
            "expected_result", "actual_result", "root_cause", "fix_notes",
            "tags", "linked_tc_id", "linked_run_id", "linked_plan_id",
        }
        updates = {k: v for k, v in fields.items() if k in allowed}
        if not updates:
            return self.get(bug_id)
        if "tags" in updates and isinstance(updates["tags"], list):
            updates["tags"] = json.dumps(updates["tags"])
        updates["updated_at"] = _now()
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        vals = list(updates.values()) + [bug_id]
        self._conn().execute(f"UPDATE bugs SET {set_clause} WHERE id = ?", vals)
        self._conn().commit()
        return self.get(bug_id)

    def delete(self, bug_id: str) -> bool:
        bug = self.get(bug_id)
        if not bug:
            return False
        # Remove artifact files from disk
        for art in self.list_artifacts(bug_id):
            p = ROOT / art["storage_path"]
            if p.exists():
                p.unlink(missing_ok=True)
        bug_dir = _BUGS_DIR / bug["product"] / bug_id
        if bug_dir.exists():
            import shutil
            shutil.rmtree(bug_dir, ignore_errors=True)
        conn = self._conn()
        conn.execute("DELETE FROM bug_artifacts WHERE bug_id = ?", (bug_id,))
        conn.execute("DELETE FROM bug_comments WHERE bug_id = ?", (bug_id,))
        conn.execute("DELETE FROM bug_state_history WHERE bug_id = ?", (bug_id,))
        conn.execute("DELETE FROM bugs WHERE id = ?", (bug_id,))
        conn.commit()
        return True

    # ── State machine ─────────────────────────────────────────────────────────

    def transition(
        self, bug_id: str, to_state: str, changed_by: str, comment: str = ""
    ) -> dict:
        bug = self.get(bug_id)
        if not bug:
            raise ValueError(f"Bug {bug_id} not found")
        from_state = bug["state"]
        allowed = _get_transitions(bug.get("product")).get(from_state, set())
        if to_state not in allowed:
            raise ValueError(
                f"Cannot transition from '{from_state}' to '{to_state}'. "
                f"Allowed: {sorted(allowed) or 'none'}"
            )
        now = _now()
        updates: dict[str, Any] = {"state": to_state, "updated_at": now}
        if to_state == "resolved":
            updates["resolved_at"] = now
        elif to_state == "closed":
            updates["closed_at"] = now
        elif to_state == "open" and from_state in ("resolved", "closed"):
            updates["resolved_at"] = None
            updates["closed_at"] = None

        set_clause = ", ".join(f"{k} = ?" for k in updates)
        vals = list(updates.values()) + [bug_id]
        conn = self._conn()
        conn.execute(f"UPDATE bugs SET {set_clause} WHERE id = ?", vals)
        conn.execute(
            """INSERT INTO bug_state_history
               (bug_id, from_state, to_state, changed_by, changed_at, comment)
               VALUES (?,?,?,?,?,?)""",
            (bug_id, from_state, to_state, changed_by, now, comment),
        )
        conn.commit()
        return self.get(bug_id)  # type: ignore[return-value]

    def get_history(self, bug_id: str) -> list[dict]:
        rows = self._conn().execute(
            "SELECT * FROM bug_state_history WHERE bug_id = ? ORDER BY changed_at",
            (bug_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def allowed_transitions(self, bug_id: str) -> list[str]:
        bug = self.get(bug_id)
        if not bug:
            return []
        return sorted(_get_transitions(bug.get("product")).get(bug["state"], set()))

    def get_product_statuses(self, product: str) -> list[dict]:
        return _get_statuses(product)

    # ── Comments ──────────────────────────────────────────────────────────────

    def add_comment(self, bug_id: str, author: str, body: str) -> dict:
        cid = str(uuid.uuid4())
        now = _now()
        self._conn().execute(
            "INSERT INTO bug_comments (id, bug_id, author, body, created_at, updated_at) VALUES (?,?,?,?,?,?)",
            (cid, bug_id, author, body, now, now),
        )
        self._conn().commit()
        return {"id": cid, "bug_id": bug_id, "author": author, "body": body,
                "created_at": now, "updated_at": now}

    def list_comments(self, bug_id: str) -> list[dict]:
        rows = self._conn().execute(
            "SELECT * FROM bug_comments WHERE bug_id = ? ORDER BY created_at",
            (bug_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    # ── Artifacts ─────────────────────────────────────────────────────────────

    def artifact_storage_path(self, product: str, bug_id: str, artifact_id: str, filename: str) -> Path:
        d = _BUGS_DIR / product / bug_id / "artifacts"
        d.mkdir(parents=True, exist_ok=True)
        return d / f"{artifact_id}_{filename}"

    def add_artifact(
        self,
        bug_id: str,
        filename: str,
        artifact_type: str,
        mime_type: str,
        size_bytes: int,
        storage_path: str,
        uploaded_by: str = "",
    ) -> dict:
        aid = str(uuid.uuid4())
        now = _now()
        self._conn().execute(
            """INSERT INTO bug_artifacts
               (id, bug_id, filename, artifact_type, mime_type, size_bytes, storage_path, uploaded_at, uploaded_by)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (aid, bug_id, filename, artifact_type, mime_type, size_bytes, storage_path, now, uploaded_by),
        )
        self._conn().commit()
        return {"id": aid, "bug_id": bug_id, "filename": filename,
                "artifact_type": artifact_type, "mime_type": mime_type,
                "size_bytes": size_bytes, "storage_path": storage_path,
                "uploaded_at": now, "uploaded_by": uploaded_by}

    def list_artifacts(self, bug_id: str) -> list[dict]:
        rows = self._conn().execute(
            "SELECT * FROM bug_artifacts WHERE bug_id = ? ORDER BY uploaded_at",
            (bug_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_artifact(self, artifact_id: str) -> dict | None:
        row = self._conn().execute(
            "SELECT * FROM bug_artifacts WHERE id = ?", (artifact_id,)
        ).fetchone()
        return dict(row) if row else None

    def delete_artifact(self, artifact_id: str) -> bool:
        art = self.get_artifact(artifact_id)
        if not art:
            return False
        p = ROOT / art["storage_path"]
        p.unlink(missing_ok=True)
        self._conn().execute("DELETE FROM bug_artifacts WHERE id = ?", (artifact_id,))
        self._conn().commit()
        return True

    # ── Stats ─────────────────────────────────────────────────────────────────

    def counts_by_state(self, product: str | None = None) -> dict[str, int]:
        where = "WHERE product = ?" if product else ""
        rows = self._conn().execute(
            f"SELECT state, COUNT(*) FROM bugs {where} GROUP BY state",
            (product,) if product else (),
        ).fetchall()
        return {r[0]: r[1] for r in rows}
