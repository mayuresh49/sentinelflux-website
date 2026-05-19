"""InsightsManager — CRUD for product_insights rows in SQLite."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from core.db import get_conn

_VALID_STATUSES = {"active", "planned", "punted", "discarded"}
_AGENT_TYPES = {"product_manager", "dev_architect", "qa_architect", "ux_architect"}


class InsightsManager:
    def save_insights(self, agent_type: str, insights: list[dict], run_id: str) -> None:
        run_at = datetime.now(timezone.utc).isoformat()
        conn = get_conn()
        with conn:
            for ins in insights:
                conn.execute(
                    """INSERT INTO product_insights
                       (id, agent_type, title, description, recommendation,
                        category, priority, status, run_id, run_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)""",
                    (
                        str(uuid.uuid4()),
                        agent_type,
                        ins.get("title", ""),
                        ins.get("description", ""),
                        ins.get("recommendation", ""),
                        ins.get("category", "opportunity"),
                        ins.get("priority", "medium"),
                        run_id,
                        run_at,
                    ),
                )

    def list_insights(
        self,
        agent_type: str | None = None,
        status: str | None = None,
    ) -> list[dict]:
        clauses: list[str] = []
        params: list[Any] = []
        if agent_type:
            clauses.append("agent_type = ?")
            params.append(agent_type)
        if status:
            clauses.append("status = ?")
            params.append(status)
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        conn = get_conn()
        rows = conn.execute(
            f"SELECT * FROM product_insights {where} ORDER BY run_at DESC, priority DESC",
            params,
        ).fetchall()
        return [dict(r) for r in rows]

    def update_status(self, insight_id: str, status: str) -> bool:
        if status not in _VALID_STATUSES:
            return False
        updated_at = datetime.now(timezone.utc).isoformat()
        conn = get_conn()
        with conn:
            cur = conn.execute(
                "UPDATE product_insights SET status=?, updated_at=? WHERE id=?",
                (status, updated_at, insight_id),
            )
        return cur.rowcount > 0

    def latest_runs(self) -> dict[str, str | None]:
        conn = get_conn()
        rows = conn.execute(
            "SELECT agent_type, MAX(run_at) as latest FROM product_insights GROUP BY agent_type"
        ).fetchall()
        result: dict[str, str | None] = {at: None for at in _AGENT_TYPES}
        for r in rows:
            result[r["agent_type"]] = r["latest"]
        return result

    def delete_insights_by_agent(self, agent_type: str) -> int:
        conn = get_conn()
        with conn:
            cur = conn.execute(
                "DELETE FROM product_insights WHERE agent_type=?", (agent_type,)
            )
        return cur.rowcount
