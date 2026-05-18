"""CRUD for test plans, scope, TC execution status, and run links."""
from __future__ import annotations

import json
import sqlite3
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.db import apply_schema, get_conn

_PLAN_JSON = {"milestones", "risks"}
_SCOPE_JSON = {"excluded_tc_ids"}


class TestPlanManager:
    def __init__(self, db_path: Path | None = None):
        if db_path is not None:
            db_path.parent.mkdir(parents=True, exist_ok=True)
            self._isolated_conn: sqlite3.Connection | None = sqlite3.connect(str(db_path))
            self._isolated_conn.row_factory = sqlite3.Row
            self._isolated_conn.execute("PRAGMA journal_mode=WAL")
            self._isolated_conn.execute("PRAGMA foreign_keys=ON")
            apply_schema(self._isolated_conn)
        else:
            self._isolated_conn = None

    def _conn(self) -> sqlite3.Connection:
        return self._isolated_conn if self._isolated_conn is not None else get_conn()

    # ── plans ─────────────────────────────────────────────────────────────

    def create_plan(
        self,
        name: str,
        product: str,
        owner: str = "",
        description: str = "",
        schedule_start: str | None = None,
        schedule_end: str | None = None,
        milestones: list | None = None,
        risks: list | None = None,
        exit_criteria: str = "",
        pass_criteria: str = "",
    ) -> dict:
        plan_id = f"plan_{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc).isoformat()
        conn = self._conn()
        conn.execute(
            """INSERT INTO test_plans
               (id, name, product, description, owner, status, schedule_start,
                schedule_end, milestones, risks, exit_criteria, pass_criteria,
                created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, 'draft', ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                plan_id, name, product, description, owner,
                schedule_start, schedule_end,
                json.dumps(milestones or []),
                json.dumps(risks or []),
                exit_criteria, pass_criteria, now, now,
            ),
        )
        conn.commit()
        return self.get_plan(plan_id)  # type: ignore[return-value]

    def get_plan(self, plan_id: str) -> dict | None:
        row = self._conn().execute(
            "SELECT * FROM test_plans WHERE id = ?", (plan_id,)
        ).fetchone()
        return _plan_row(row) if row else None

    def list_plans(self, product: str | None = None, status: str | None = None) -> list[dict]:
        clauses, params = [], []
        if product:
            clauses.append("product = ?")
            params.append(product)
        if status:
            clauses.append("status = ?")
            params.append(status)
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        rows = self._conn().execute(
            f"SELECT * FROM test_plans {where} ORDER BY created_at DESC", params
        ).fetchall()
        return [_plan_row(r) for r in rows]

    def patch_plan(self, plan_id: str, **fields: Any) -> dict | None:
        if not fields:
            return self.get_plan(plan_id)
        fields["updated_at"] = datetime.now(timezone.utc).isoformat()
        serialised = {
            k: (json.dumps(v) if k in _PLAN_JSON else v)
            for k, v in fields.items()
        }
        set_clause = ", ".join(f"{k} = ?" for k in serialised)
        params = list(serialised.values()) + [plan_id]
        conn = self._conn()
        conn.execute(f"UPDATE test_plans SET {set_clause} WHERE id = ?", params)
        conn.commit()
        return self.get_plan(plan_id)

    def delete_plan(self, plan_id: str) -> bool:
        conn = self._conn()
        cur = conn.execute("DELETE FROM test_plans WHERE id = ?", (plan_id,))
        conn.commit()
        return cur.rowcount > 0

    # ── scope ─────────────────────────────────────────────────────────────

    def set_scope(self, plan_id: str, items: list[dict]) -> None:
        """Replace all scope rows for this plan."""
        conn = self._conn()
        conn.execute("DELETE FROM test_plan_scope WHERE plan_id = ?", (plan_id,))
        for item in items:
            conn.execute(
                """INSERT INTO test_plan_scope (plan_id, domain, module, excluded_tc_ids)
                   VALUES (?, ?, ?, ?)""",
                (
                    plan_id,
                    item["domain"],
                    item["module"],
                    json.dumps(item.get("excluded_tc_ids") or []),
                ),
            )
        conn.commit()

    def get_scope(self, plan_id: str) -> list[dict]:
        rows = self._conn().execute(
            "SELECT * FROM test_plan_scope WHERE plan_id = ? ORDER BY domain, module",
            (plan_id,),
        ).fetchall()
        return [_scope_row(r) for r in rows]

    # ── TC execution status ────────────────────────────────────────────────

    def upsert_tc_statuses(self, plan_id: str, tcs: list[dict]) -> None:
        """Upsert TC rows; preserves existing exec_status/notes on conflict."""
        conn = self._conn()
        for tc in tcs:
            conn.execute(
                """INSERT INTO test_plan_tc_status
                   (plan_id, tc_id, tc_title, domain, module, automation_status,
                    exec_status, notes, updated_at, updated_by)
                   VALUES (?, ?, ?, ?, ?, ?, 'not_run', '', NULL, '')
                   ON CONFLICT(plan_id, tc_id) DO UPDATE
                   SET tc_title = excluded.tc_title,
                       domain = excluded.domain,
                       module = excluded.module,
                       automation_status = excluded.automation_status""",
                (
                    plan_id,
                    tc["tc_id"],
                    tc.get("tc_title", ""),
                    tc["domain"],
                    tc["module"],
                    tc.get("automation_status", "automated"),
                ),
            )
        conn.commit()

    def remove_tc_statuses_not_in_scope(self, plan_id: str, keep_tc_ids: list[str]) -> None:
        """Delete TC status rows that are no longer in scope."""
        if not keep_tc_ids:
            self._conn().execute(
                "DELETE FROM test_plan_tc_status WHERE plan_id = ?", (plan_id,)
            )
        else:
            placeholders = ",".join("?" * len(keep_tc_ids))
            self._conn().execute(
                f"DELETE FROM test_plan_tc_status WHERE plan_id = ? AND tc_id NOT IN ({placeholders})",
                [plan_id] + keep_tc_ids,
            )
        self._conn().commit()

    def update_tc_status(
        self,
        plan_id: str,
        tc_id: str,
        exec_status: str,
        notes: str = "",
        updated_by: str = "",
    ) -> bool:
        conn = self._conn()
        cur = conn.execute(
            """UPDATE test_plan_tc_status
               SET exec_status = ?, notes = ?, updated_at = ?, updated_by = ?
               WHERE plan_id = ? AND tc_id = ?""",
            (
                exec_status, notes,
                datetime.now(timezone.utc).isoformat(),
                updated_by, plan_id, tc_id,
            ),
        )
        conn.commit()
        return cur.rowcount > 0

    def get_tc_statuses(
        self,
        plan_id: str,
        domain: str | None = None,
        module: str | None = None,
    ) -> list[dict]:
        clauses = ["plan_id = ?"]
        params: list[Any] = [plan_id]
        if domain:
            clauses.append("domain = ?")
            params.append(domain)
        if module:
            clauses.append("module = ?")
            params.append(module)
        where = " AND ".join(clauses)
        rows = self._conn().execute(
            f"SELECT * FROM test_plan_tc_status WHERE {where} ORDER BY domain, module, tc_id",
            params,
        ).fetchall()
        return [dict(r) for r in rows]

    # ── run links ──────────────────────────────────────────────────────────

    def link_run(self, plan_id: str, run_id: str) -> None:
        conn = self._conn()
        conn.execute(
            "INSERT OR IGNORE INTO test_plan_run_links (plan_id, run_id, triggered_at) VALUES (?, ?, ?)",
            (plan_id, run_id, datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()

    def get_linked_run_ids(self, plan_id: str) -> list[str]:
        rows = self._conn().execute(
            "SELECT run_id FROM test_plan_run_links WHERE plan_id = ? ORDER BY triggered_at DESC",
            (plan_id,),
        ).fetchall()
        return [r["run_id"] for r in rows]

    # ── progress ──────────────────────────────────────────────────────────

    def get_progress(self, plan_id: str) -> dict:
        rows = self.get_tc_statuses(plan_id)
        total = len(rows)
        counts = Counter(r["exec_status"] for r in rows)
        auto_rows = [r for r in rows if r["automation_status"] == "automated"]
        return {
            "total": total,
            "not_run": counts.get("not_run", 0),
            "pass": counts.get("pass", 0),
            "fail": counts.get("fail", 0),
            "blocked": counts.get("blocked", 0),
            "pass_rate": round(counts.get("pass", 0) / total * 100) if total else 0,
            "auto_total": len(auto_rows),
            "auto_pass": sum(1 for r in auto_rows if r["exec_status"] == "pass"),
            "auto_fail": sum(1 for r in auto_rows if r["exec_status"] == "fail"),
        }


# ── row helpers ───────────────────────────────────────────────────────────────

def _plan_row(r) -> dict:
    d = dict(r)
    for col in _PLAN_JSON:
        try:
            d[col] = json.loads(d[col])
        except (json.JSONDecodeError, TypeError, KeyError):
            d[col] = []
    return d


def _scope_row(r) -> dict:
    d = dict(r)
    try:
        d["excluded_tc_ids"] = json.loads(d["excluded_tc_ids"])
    except (json.JSONDecodeError, TypeError):
        d["excluded_tc_ids"] = []
    return d
