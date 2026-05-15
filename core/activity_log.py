"""ActivityLog — append-only event store for all agent and pipeline runs."""
from __future__ import annotations

import json
import logging
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.db import apply_schema, get_conn

_log = logging.getLogger("sentinelflux.activity_log")
MAX_ENTRIES = 1000


class ActivityLog:
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

    def append(
        self,
        *,
        event_type: str,
        agent: str,
        domain: str,
        status: str,
        summary: str,
        product: str | None = None,
        output: dict[str, Any] | None = None,
        requires_human: bool = False,
        approval_id: str | None = None,
    ) -> str:
        entry_id = str(uuid.uuid4())
        conn = self._conn()
        conn.execute(
            """INSERT INTO activity_log
               (id, timestamp, event_type, agent, product, domain, status, summary,
                output, requires_human, approval_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                entry_id,
                datetime.now(timezone.utc).isoformat(),
                event_type, agent, product, domain, status, summary,
                json.dumps(output or {}),
                1 if requires_human else 0,
                approval_id,
            ),
        )
        conn.execute(
            "DELETE FROM activity_log WHERE id NOT IN "
            "(SELECT id FROM activity_log ORDER BY timestamp DESC LIMIT ?)",
            (MAX_ENTRIES,),
        )
        conn.commit()
        return entry_id

    def all(self) -> list[dict]:
        rows = self._conn().execute(
            "SELECT * FROM activity_log ORDER BY timestamp ASC"
        ).fetchall()
        return [_row(r) for r in rows]

    def get(self, entry_id: str) -> dict | None:
        row = self._conn().execute(
            "SELECT * FROM activity_log WHERE id = ?", (entry_id,)
        ).fetchone()
        return _row(row) if row else None

    def recent(self, n: int = 50) -> list[dict]:
        rows = self._conn().execute(
            "SELECT * FROM activity_log ORDER BY timestamp DESC LIMIT ?", (n,)
        ).fetchall()
        return [_row(r) for r in reversed(rows)]

    def filter(
        self,
        *,
        agent: str | None = None,
        domain: str | None = None,
        product: str | None = None,
        requires_human: bool | None = None,
        event_type: str | None = None,
    ) -> list[dict]:
        clauses: list[str] = []
        params: list[Any] = []
        if agent:
            clauses.append("agent = ?"); params.append(agent)
        if domain:
            clauses.append("domain = ?"); params.append(domain)
        if product:
            clauses.append("product = ?"); params.append(product)
        if requires_human is not None:
            clauses.append("requires_human = ?"); params.append(1 if requires_human else 0)
        if event_type:
            clauses.append("event_type = ?"); params.append(event_type)
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        rows = self._conn().execute(
            f"SELECT * FROM activity_log {where} ORDER BY timestamp ASC", params
        ).fetchall()
        return [_row(r) for r in rows]


def _row(r) -> dict:
    d = dict(r)
    try:
        d["output"] = json.loads(d["output"])
    except (json.JSONDecodeError, TypeError):
        d["output"] = {}
    d["requires_human"] = bool(d["requires_human"])
    return d
