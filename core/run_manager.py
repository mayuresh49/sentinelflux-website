"""Test suite run records and schedule configuration."""
from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.db import apply_schema, get_conn
from utils.paths import ROOT as _ROOT

_RUNS_DIR = _ROOT / "data" / "runs"
_MAX_RUNS = 200  # per product
_DAY_NAMES = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]

_RUN_JSON = {"failure_categories", "failures", "run_config_snapshot"}
_SCHEDULE_JSON = {"days"}


class RunManager:
    def __init__(self, db_path: Path | None = None):
        # When db_path is given (e.g. in tests), use an isolated SQLite DB.
        if db_path is not None:
            db_path.parent.mkdir(parents=True, exist_ok=True)
            self._isolated_conn: sqlite3.Connection | None = sqlite3.connect(str(db_path))
            self._isolated_conn.row_factory = sqlite3.Row
            self._isolated_conn.execute("PRAGMA journal_mode=WAL")
            apply_schema(self._isolated_conn)
        else:
            self._isolated_conn = None

    def _conn(self) -> sqlite3.Connection:
        return self._isolated_conn if self._isolated_conn is not None else get_conn()

    # ── runs ──────────────────────────────────────────────────────────────

    def all_runs(self, product: str | None = None) -> list[dict]:
        if product:
            rows = self._conn().execute(
                "SELECT * FROM test_runs WHERE product = ? ORDER BY triggered_at DESC",
                (product,),
            ).fetchall()
        else:
            rows = self._conn().execute(
                "SELECT * FROM test_runs ORDER BY triggered_at DESC"
            ).fetchall()
        return [_run_row(r) for r in rows]

    def get_run(self, run_id: str) -> dict | None:
        row = self._conn().execute(
            "SELECT * FROM test_runs WHERE id = ?", (run_id,)
        ).fetchone()
        return _run_row(row) if row else None

    def create_run(
        self,
        product: str,
        domain: str,
        module: str = "",
        trigger: str = "manual",
        schedule_id: str | None = None,
        run_config_snapshot: dict | None = None,
    ) -> dict:
        run_id = f"run_{uuid.uuid4().hex[:8]}"
        _abs = _RUNS_DIR / f"{run_id}_report.json"
        try:
            report_path = str(_abs.relative_to(_ROOT))
        except ValueError:
            report_path = str(_abs)

        conn = self._conn()
        conn.execute(
            """INSERT INTO test_runs
               (id, triggered_at, finished_at, product, domain, module, trigger,
                schedule_id, status, total, passed, failed, skipped, errors,
                duration, report_path, analyzed, failure_categories, failures,
                run_config_snapshot)
               VALUES (?, ?, NULL, ?, ?, ?, ?, ?, 'queued',
                       0, 0, 0, 0, 0, 0.0, ?, 0, '{}', '[]', ?)""",
            (
                run_id,
                datetime.now(timezone.utc).isoformat(),
                product, domain, module, trigger, schedule_id,
                report_path,
                json.dumps(run_config_snapshot or {}),
            ),
        )
        conn.execute(
            "DELETE FROM test_runs WHERE product = ? AND id NOT IN "
            "(SELECT id FROM test_runs WHERE product = ? ORDER BY triggered_at DESC LIMIT ?)",
            (product, product, _MAX_RUNS),
        )
        conn.commit()
        return self.get_run(run_id)  # type: ignore[return-value]

    def delete_run(self, run_id: str) -> bool:
        conn = self._conn()
        cur = conn.execute("DELETE FROM test_runs WHERE id = ?", (run_id,))
        conn.commit()
        return cur.rowcount > 0

    def patch_run(self, run_id: str, **fields: Any) -> dict | None:
        if not fields:
            return self.get_run(run_id)
        serialised = {
            k: (json.dumps(v) if k in _RUN_JSON else v)
            for k, v in fields.items()
        }
        set_clause = ", ".join(f"{k} = ?" for k in serialised)
        params = list(serialised.values()) + [run_id]
        conn = self._conn()
        conn.execute(f"UPDATE test_runs SET {set_clause} WHERE id = ?", params)
        conn.commit()
        return self.get_run(run_id)

    # ── schedules ─────────────────────────────────────────────────────────

    def all_schedules(self, product: str | None = None) -> list[dict]:
        if product:
            rows = self._conn().execute(
                "SELECT * FROM test_schedules WHERE product = ?", (product,)
            ).fetchall()
        else:
            rows = self._conn().execute("SELECT * FROM test_schedules").fetchall()
        return [_sched_row(r) for r in rows]

    def get_schedule(self, sched_id: str) -> dict | None:
        row = self._conn().execute(
            "SELECT * FROM test_schedules WHERE id = ?", (sched_id,)
        ).fetchone()
        return _sched_row(row) if row else None

    def create_schedule(
        self,
        name: str,
        product: str,
        domain: str,
        module: str = "",
        hour: int = 2,
        minute: int = 0,
        days: list[str] | None = None,
        environment: str = "",
        browser: str = "",
        device: str = "",
    ) -> dict:
        sched_id = f"sched_{uuid.uuid4().hex[:8]}"
        conn = self._conn()
        conn.execute(
            """INSERT INTO test_schedules
               (id, name, product, domain, module, hour, minute, days, enabled,
                created_at, last_run_id, last_run_at, environment, browser, device)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, NULL, NULL, ?, ?, ?)""",
            (
                sched_id, name, product, domain, module, hour, minute,
                json.dumps(days or ["mon", "tue", "wed", "thu", "fri"]),
                datetime.now(timezone.utc).isoformat(),
                environment, browser, device,
            ),
        )
        conn.commit()
        return self.get_schedule(sched_id)  # type: ignore[return-value]

    def patch_schedule(self, sched_id: str, **fields: Any) -> dict | None:
        if not fields:
            return self.get_schedule(sched_id)
        serialised = {
            k: (json.dumps(v) if k in _SCHEDULE_JSON else v)
            for k, v in fields.items()
        }
        if "enabled" in serialised:
            serialised["enabled"] = 1 if serialised["enabled"] else 0
        set_clause = ", ".join(f"{k} = ?" for k in serialised)
        params = list(serialised.values()) + [sched_id]
        conn = self._conn()
        conn.execute(f"UPDATE test_schedules SET {set_clause} WHERE id = ?", params)
        conn.commit()
        return self.get_schedule(sched_id)

    def delete_schedule(self, sched_id: str) -> bool:
        conn = self._conn()
        cur = conn.execute("DELETE FROM test_schedules WHERE id = ?", (sched_id,))
        conn.commit()
        return cur.rowcount > 0

    # ── schedule firing check ─────────────────────────────────────────────

    @staticmethod
    def is_due(schedule: dict, now: datetime | None = None) -> bool:
        if not schedule.get("enabled"):
            return False
        now = now or datetime.now(timezone.utc)
        today_name = _DAY_NAMES[now.weekday()]
        if today_name not in schedule.get("days", []):
            return False
        if now.hour != schedule.get("hour", 0) or now.minute != schedule.get("minute", 0):
            return False
        last_run = schedule.get("last_run_at")
        if last_run:
            last_dt = datetime.fromisoformat(last_run)
            if last_dt.date() == now.date():
                return False
        return True


# ── row helpers ───────────────────────────────────────────────────────────────

def _run_row(r) -> dict:
    d = dict(r)
    for col in _RUN_JSON:
        try:
            d[col] = json.loads(d[col])
        except (json.JSONDecodeError, TypeError, KeyError):
            d[col] = {} if col != "failures" else []
    d["analyzed"] = bool(d.get("analyzed"))
    return d


def _sched_row(r) -> dict:
    d = dict(r)
    try:
        d["days"] = json.loads(d["days"])
    except (json.JSONDecodeError, TypeError):
        d["days"] = []
    d["enabled"] = bool(d.get("enabled"))
    return d
