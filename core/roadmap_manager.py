"""RoadmapManager — CRUD for roadmap_items rows in SQLite."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from core.db import get_conn

_VALID_STATUSES = {"planned", "done"}


class RoadmapManager:
    def create_item(self, source_insight: dict, cto_rationale: str) -> str:
        """Insert roadmap item. Skips silently if source_insight_id already exists. Returns item id."""
        item_id = str(uuid.uuid4())
        promoted_at = datetime.now(timezone.utc).isoformat()
        conn = get_conn()
        with conn:
            conn.execute(
                """INSERT OR IGNORE INTO roadmap_items
                   (id, source_insight_id, agent_type, title, description, recommendation,
                    category, priority, cto_rationale, status, promoted_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'planned', ?)""",
                (
                    item_id,
                    source_insight["id"],
                    source_insight["agent_type"],
                    source_insight["title"],
                    source_insight.get("description", ""),
                    source_insight.get("recommendation", ""),
                    source_insight.get("category", "opportunity"),
                    source_insight.get("priority", "medium"),
                    cto_rationale,
                    promoted_at,
                ),
            )
        # Return the actual id (may differ if row already existed)
        row = conn.execute(
            "SELECT id FROM roadmap_items WHERE source_insight_id=?",
            (source_insight["id"],),
        ).fetchone()
        return row["id"] if row else item_id

    def list_items(self, status: str | None = None) -> list[dict]:
        conn = get_conn()
        where = "WHERE status=?" if status else ""
        params = [status] if status else []
        rows = conn.execute(
            f"SELECT * FROM roadmap_items {where} ORDER BY promoted_at DESC",
            params,
        ).fetchall()
        return [dict(r) for r in rows]

    def update_status(self, item_id: str, status: str) -> bool:
        if status not in _VALID_STATUSES:
            return False
        done_at = datetime.now(timezone.utc).isoformat() if status == "done" else None
        conn = get_conn()
        with conn:
            cur = conn.execute(
                "UPDATE roadmap_items SET status=?, done_at=? WHERE id=?",
                (status, done_at, item_id),
            )
        return cur.rowcount > 0

    def delete_item(self, item_id: str) -> str | None:
        """Delete item, return source_insight_id so caller can restore the source insight."""
        conn = get_conn()
        row = conn.execute(
            "SELECT source_insight_id FROM roadmap_items WHERE id=?", (item_id,)
        ).fetchone()
        if not row:
            return None
        source_id = row["source_insight_id"]
        with conn:
            conn.execute("DELETE FROM roadmap_items WHERE id=?", (item_id,))
        return source_id

    def latest_run_at(self) -> str | None:
        conn = get_conn()
        row = conn.execute(
            "SELECT MAX(promoted_at) as latest FROM roadmap_items"
        ).fetchone()
        return row["latest"] if row else None
