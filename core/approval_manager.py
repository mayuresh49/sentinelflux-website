"""ApprovalManager — unified human-in-the-loop gate for all agent proposals."""
from __future__ import annotations

import json
import logging
import sqlite3
import uuid
from datetime import date
from pathlib import Path
from typing import Any

from core.db import apply_schema, get_conn

_log = logging.getLogger("sentinelflux.approval_manager")

APPROVAL_TYPES = frozenset({
    "quarantine",
    "unquarantine",
    "locator_heal",
    "script_review",
    "coverage_gap",
    "regression_review",
})


class ApprovalManager:
    def __init__(self, path: Path | None = None):
        # When path is given (e.g. in tests), use an isolated SQLite DB in the same dir.
        if path is not None:
            db_path = path.parent / "sentinelflux.db"
            db_path.parent.mkdir(parents=True, exist_ok=True)
            self._isolated_conn: sqlite3.Connection | None = sqlite3.connect(str(db_path))
            self._isolated_conn.row_factory = sqlite3.Row
            self._isolated_conn.execute("PRAGMA journal_mode=WAL")
            apply_schema(self._isolated_conn)
        else:
            self._isolated_conn = None

    def _conn(self) -> sqlite3.Connection:
        return self._isolated_conn if self._isolated_conn is not None else get_conn()

    def submit(
        self,
        *,
        approval_type: str,
        title: str,
        domain: str,
        product: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> str:
        approval_id = str(uuid.uuid4())
        conn = self._conn()
        conn.execute(
            """INSERT INTO approvals
               (id, type, product, domain, title, proposed_date, details, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, 'pending')""",
            (approval_id, approval_type, product, domain, title,
             str(date.today()), json.dumps(details or {})),
        )
        conn.commit()
        _log.info("Approval submitted: %s [%s]", title, approval_id[:8])
        return approval_id

    def resolve(
        self,
        approval_id: str,
        *,
        decision: str,
        resolved_by: str = "human",
        notes: str = "",
    ) -> bool:
        conn = self._conn()
        row = conn.execute(
            "SELECT id FROM approvals WHERE id = ? AND status = 'pending'",
            (approval_id,),
        ).fetchone()
        if not row:
            return False
        conn.execute(
            """UPDATE approvals
               SET status = ?, decision = ?, resolved_date = ?, resolved_by = ?, notes = ?
               WHERE id = ?""",
            (decision, decision, str(date.today()), resolved_by, notes, approval_id),
        )
        conn.commit()
        _log.info("Approval %s [%s]", decision, approval_id[:8])
        return True

    def pending(self, approval_type: str | None = None) -> list[dict]:
        if approval_type:
            rows = self._conn().execute(
                "SELECT * FROM approvals WHERE status = 'pending' AND type = ?",
                (approval_type,),
            ).fetchall()
        else:
            rows = self._conn().execute(
                "SELECT * FROM approvals WHERE status = 'pending'"
            ).fetchall()
        return [_row(r) for r in rows]

    def resolved(self, limit: int = 100) -> list[dict]:
        rows = self._conn().execute(
            "SELECT * FROM approvals WHERE status != 'pending' "
            "ORDER BY resolved_date DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [_row(r) for r in rows]

    def get(self, approval_id: str) -> dict | None:
        row = self._conn().execute(
            "SELECT * FROM approvals WHERE id = ?", (approval_id,)
        ).fetchone()
        return _row(row) if row else None


def _row(r) -> dict:
    d = dict(r)
    try:
        d["details"] = json.loads(d["details"])
    except (json.JSONDecodeError, TypeError):
        d["details"] = {}
    return d
