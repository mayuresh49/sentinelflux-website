"""Test suite run records and schedule configuration."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from filelock import FileLock

from utils.paths import ROOT as _ROOT

# Per-product storage directories
_RUNS_STORE_DIR = _ROOT / "data" / "test_runs"         # data/test_runs/<product>.json
_SCHEDULES_STORE_DIR = _ROOT / "data" / "test_schedules"  # data/test_schedules/<product>.json
_RUNS_DIR = _ROOT / "data" / "runs"                    # report JSON files (unchanged)
_RUN_INDEX_PATH = _ROOT / "data" / "run_product_index.json"

# Legacy flat-file paths — migrated on first access
_LEGACY_RUNS_PATH = _ROOT / "data" / "test_runs.json"
_LEGACY_SCHEDULES_PATH = _ROOT / "data" / "test_schedules.json"

_MAX_RUNS = 200  # per product

_DAY_NAMES = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


class RunManager:
    _migrated = False

    # ── one-time migration from flat files ────────────────────────────────

    def _ensure_migrated(self) -> None:
        if RunManager._migrated:
            return
        RunManager._migrated = True
        self._migrate_legacy_runs()
        self._migrate_legacy_schedules()

    def _migrate_legacy_runs(self) -> None:
        if not _LEGACY_RUNS_PATH.exists():
            return
        try:
            legacy = json.loads(_LEGACY_RUNS_PATH.read_text(encoding="utf-8")).get("runs", [])
        except Exception:
            return
        by_product: dict[str, list] = {}
        for r in legacy:
            by_product.setdefault(r.get("product", "unknown"), []).append(r)
        for product, runs in by_product.items():
            path = _RUNS_STORE_DIR / f"{product}.json"
            existing = self._load(path, "runs")
            seen = {r["id"] for r in existing}
            merged = existing + [r for r in runs if r["id"] not in seen]
            self._save(path, "runs", merged)
            for r in runs:
                self._index_run(r["id"], product)
        _LEGACY_RUNS_PATH.rename(_LEGACY_RUNS_PATH.with_suffix(".json.migrated"))

    def _migrate_legacy_schedules(self) -> None:
        if not _LEGACY_SCHEDULES_PATH.exists():
            return
        try:
            legacy = json.loads(_LEGACY_SCHEDULES_PATH.read_text(encoding="utf-8")).get("schedules", [])
        except Exception:
            return
        by_product: dict[str, list] = {}
        for s in legacy:
            by_product.setdefault(s.get("product", "unknown"), []).append(s)
        for product, schedules in by_product.items():
            path = _SCHEDULES_STORE_DIR / f"{product}.json"
            existing = self._load(path, "schedules")
            seen = {s["id"] for s in existing}
            merged = existing + [s for s in schedules if s["id"] not in seen]
            self._save(path, "schedules", merged)
        _LEGACY_SCHEDULES_PATH.rename(_LEGACY_SCHEDULES_PATH.with_suffix(".json.migrated"))

    # ── run-to-product index (O(1) lookups for patch_run hot path) ────────

    def _index_run(self, run_id: str, product: str) -> None:
        with FileLock(str(_RUN_INDEX_PATH) + ".lock"):
            try:
                index = json.loads(_RUN_INDEX_PATH.read_text(encoding="utf-8")) if _RUN_INDEX_PATH.exists() else {}
            except Exception:
                index = {}
            index[run_id] = product
            _RUN_INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
            _RUN_INDEX_PATH.write_text(json.dumps(index), encoding="utf-8")

    def _deindex_run(self, run_id: str) -> None:
        with FileLock(str(_RUN_INDEX_PATH) + ".lock"):
            try:
                index = json.loads(_RUN_INDEX_PATH.read_text(encoding="utf-8")) if _RUN_INDEX_PATH.exists() else {}
                index.pop(run_id, None)
                _RUN_INDEX_PATH.write_text(json.dumps(index), encoding="utf-8")
            except Exception:
                pass

    def _product_for_run(self, run_id: str) -> str | None:
        try:
            if _RUN_INDEX_PATH.exists():
                index = json.loads(_RUN_INDEX_PATH.read_text(encoding="utf-8"))
                if run_id in index:
                    return index[run_id]
        except Exception:
            pass
        # Fallback: scan all product files (covers pre-index runs)
        if _RUNS_STORE_DIR.exists():
            for f in _RUNS_STORE_DIR.glob("*.json"):
                if any(r["id"] == run_id for r in self._load(f, "runs")):
                    return f.stem
        return None

    # ── runs ──────────────────────────────────────────────────────────────

    def all_runs(self, product: str | None = None) -> list[dict]:
        self._ensure_migrated()
        if product:
            return self._load(_RUNS_STORE_DIR / f"{product}.json", "runs")
        if not _RUNS_STORE_DIR.exists():
            return []
        result: list[dict] = []
        for f in _RUNS_STORE_DIR.glob("*.json"):
            result.extend(self._load(f, "runs"))
        result.sort(key=lambda r: r.get("triggered_at", ""), reverse=True)
        return result

    def get_run(self, run_id: str) -> dict | None:
        self._ensure_migrated()
        product = self._product_for_run(run_id)
        if not product:
            return None
        return next(
            (r for r in self._load(_RUNS_STORE_DIR / f"{product}.json", "runs") if r["id"] == run_id),
            None,
        )

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
        run: dict[str, Any] = {
            "id": run_id,
            "triggered_at": datetime.now(timezone.utc).isoformat(),
            "finished_at": None,
            "product": product,
            "domain": domain,
            "module": module,
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
        path = _RUNS_STORE_DIR / f"{product}.json"
        runs = self._load(path, "runs")
        runs.append(run)
        if len(runs) > _MAX_RUNS:
            runs = runs[-_MAX_RUNS:]
        self._save(path, "runs", runs)
        self._index_run(run_id, product)
        return run

    def delete_run(self, run_id: str) -> bool:
        product = self._product_for_run(run_id)
        if not product:
            return False
        path = _RUNS_STORE_DIR / f"{product}.json"
        runs = self._load(path, "runs")
        new = [r for r in runs if r["id"] != run_id]
        if len(new) == len(runs):
            return False
        self._save(path, "runs", new)
        self._deindex_run(run_id)
        return True

    def patch_run(self, run_id: str, **fields: Any) -> dict | None:
        product = self._product_for_run(run_id)
        if not product:
            return None
        path = _RUNS_STORE_DIR / f"{product}.json"
        runs = self._load(path, "runs")
        for r in runs:
            if r["id"] == run_id:
                r.update(fields)
                self._save(path, "runs", runs)
                return r
        return None

    # ── schedules ─────────────────────────────────────────────────────────

    def all_schedules(self, product: str | None = None) -> list[dict]:
        self._ensure_migrated()
        if product:
            return self._load(_SCHEDULES_STORE_DIR / f"{product}.json", "schedules")
        if not _SCHEDULES_STORE_DIR.exists():
            return []
        result: list[dict] = []
        for f in _SCHEDULES_STORE_DIR.glob("*.json"):
            result.extend(self._load(f, "schedules"))
        return result

    def get_schedule(self, sched_id: str) -> dict | None:
        return next((s for s in self.all_schedules() if s["id"] == sched_id), None)

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
        sched: dict[str, Any] = {
            "id": f"sched_{uuid.uuid4().hex[:8]}",
            "name": name,
            "product": product,
            "domain": domain,
            "module": module,
            "hour": hour,
            "minute": minute,
            "days": days or ["mon", "tue", "wed", "thu", "fri"],
            "enabled": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_run_id": None,
            "last_run_at": None,
            "environment": environment,
            "browser": browser,
            "device": device,
        }
        path = _SCHEDULES_STORE_DIR / f"{product}.json"
        schedules = self._load(path, "schedules")
        schedules.append(sched)
        self._save(path, "schedules", schedules)
        return sched

    def patch_schedule(self, sched_id: str, **fields: Any) -> dict | None:
        sched = self.get_schedule(sched_id)
        if not sched:
            return None
        path = _SCHEDULES_STORE_DIR / f"{sched['product']}.json"
        schedules = self._load(path, "schedules")
        for s in schedules:
            if s["id"] == sched_id:
                s.update(fields)
                self._save(path, "schedules", schedules)
                return s
        return None

    def delete_schedule(self, sched_id: str) -> bool:
        sched = self.get_schedule(sched_id)
        if not sched:
            return False
        path = _SCHEDULES_STORE_DIR / f"{sched['product']}.json"
        schedules = self._load(path, "schedules")
        new = [s for s in schedules if s["id"] != sched_id]
        if len(new) == len(schedules):
            return False
        self._save(path, "schedules", new)
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
