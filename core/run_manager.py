"""Test suite run records and schedule configuration."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from filelock import FileLock
from utils.paths import ROOT as _ROOT

_RUNS_PATH = _ROOT / "data" / "test_runs.json"
_SCHEDULES_PATH = _ROOT / "data" / "test_schedules.json"
_RUNS_DIR = _ROOT / "data" / "runs"
_MAX_RUNS = 200

_DAY_NAMES = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


class RunManager:
    # ── runs ──────────────────────────────────────────────────────────────

    def all_runs(self) -> list[dict]:
        return self._load(_RUNS_PATH, "runs")

    def get_run(self, run_id: str) -> dict | None:
        return next((r for r in self.all_runs() if r["id"] == run_id), None)

    def create_run(
        self,
        product: str,
        domain: str,
        trigger: str = "manual",
        schedule_id: str | None = None,
        run_config_snapshot: dict | None = None,
    ) -> dict:
        run_id = f"run_{uuid.uuid4().hex[:8]}"
        report_path = str((_RUNS_DIR / f"{run_id}_report.json").relative_to(_ROOT))
        run: dict[str, Any] = {
            "id": run_id,
            "triggered_at": datetime.now(timezone.utc).isoformat(),
            "finished_at": None,
            "product": product,
            "domain": domain,
            "trigger": trigger,
            "schedule_id": schedule_id,
            "status": "queued",
            "total": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": 0,
            "duration": 0.0,
            "report_path": report_path,
            "analyzed": False,
            "failure_categories": {},
            "failures": [],
            "run_config_snapshot": run_config_snapshot or {},
        }
        runs = self.all_runs()
        runs.append(run)
        if len(runs) > _MAX_RUNS:
            runs = runs[-_MAX_RUNS:]
        self._save(_RUNS_PATH, "runs", runs)
        return run

    def patch_run(self, run_id: str, **fields: Any) -> dict | None:
        runs = self.all_runs()
        for r in runs:
            if r["id"] == run_id:
                r.update(fields)
                self._save(_RUNS_PATH, "runs", runs)
                return r
        return None

    # ── schedules ─────────────────────────────────────────────────────────

    def all_schedules(self) -> list[dict]:
        return self._load(_SCHEDULES_PATH, "schedules")

    def get_schedule(self, sched_id: str) -> dict | None:
        return next((s for s in self.all_schedules() if s["id"] == sched_id), None)

    def create_schedule(
        self,
        name: str,
        product: str,
        domain: str,
        hour: int,
        minute: int,
        days: list[str],
        environment: str = "",
        browser: str = "",
        device: str = "",
    ) -> dict:
        sched: dict[str, Any] = {
            "id": f"sched_{uuid.uuid4().hex[:8]}",
            "name": name,
            "product": product,
            "domain": domain,
            "hour": hour,
            "minute": minute,
            "days": days,
            "enabled": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_run_id": None,
            "last_run_at": None,
            "environment": environment,
            "browser": browser,
            "device": device,
        }
        schedules = self.all_schedules()
        schedules.append(sched)
        self._save(_SCHEDULES_PATH, "schedules", schedules)
        return sched

    def patch_schedule(self, sched_id: str, **fields: Any) -> dict | None:
        schedules = self.all_schedules()
        for s in schedules:
            if s["id"] == sched_id:
                s.update(fields)
                self._save(_SCHEDULES_PATH, "schedules", schedules)
                return s
        return None

    def delete_schedule(self, sched_id: str) -> bool:
        schedules = self.all_schedules()
        new = [s for s in schedules if s["id"] != sched_id]
        if len(new) == len(schedules):
            return False
        self._save(_SCHEDULES_PATH, "schedules", new)
        return True

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

    # ── helpers ───────────────────────────────────────────────────────────

    @staticmethod
    def _load(path: Path, key: str) -> list[dict[str, Any]]:
        if not path.exists():
            return []
        try:
            return json.loads(path.read_text(encoding="utf-8")).get(key, [])
        except Exception:
            return []

    @staticmethod
    def _save(path: Path, key: str, items: list) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with FileLock(str(path) + ".lock"):
            path.write_text(json.dumps({key: items}, indent=2), encoding="utf-8")
