"""
QuarantineManager — rule-based (no AI). Manages quarantine.yaml and run_history.yaml.

Semi-autonomous design
----------------------
FlakyDetectorAgent → propose()      writes to pending_actions (human can review)
human / CI gate    → apply_pending() promotes to quarantined

conftest.py reads quarantined_ids() at collection time and marks tests xfail.

To go fully autonomous: call apply_pending() immediately after propose()
in your pipeline without a human gate.
"""
from __future__ import annotations

import logging
from datetime import date, timedelta
from pathlib import Path

import yaml
from filelock import FileLock

from utils.paths import ROOT as _ROOT_DIR

_log = logging.getLogger("sentinelflux.agents.quarantine_manager")

_QUARANTINE_PATH = _ROOT_DIR / "data" / "quarantine.yaml"
_HISTORY_PATH = _ROOT_DIR / "data" / "run_history.yaml"
_HISTORY_WINDOW_DAYS = 90


class QuarantineManager:
    """
    Reads / writes quarantine.yaml and run_history.yaml.

    quarantine.yaml structure:
      quarantined:       list of active quarantined tests
      pending_actions:   proposed changes awaiting apply_pending()

    run_history.yaml structure:
      tests:
        <test_nodeid>:
          - status: passed|failed
            date: "YYYY-MM-DD"
            duration: 0.45
    """

    def __init__(
        self,
        quarantine_path: Path = _QUARANTINE_PATH,
        history_path: Path = _HISTORY_PATH,
    ):
        self._qpath = quarantine_path
        self._hpath = history_path

    # ── quarantine write side ──────────────────────────────────────────────

    def propose(
        self,
        quarantine_candidates: list[dict],
        unquarantine_candidates: list[dict],
    ) -> int:
        """
        Write candidates to pending_actions. Returns number of new proposals added.
        Call apply_pending() to promote them (after human review or CI gate).
        """
        data = self._load_quarantine()
        pending: list[dict] = data.setdefault("pending_actions", [])
        added = 0

        for c in quarantine_candidates:
            if not self._is_quarantined(data, c["test_id"]) and not self._is_pending(pending, c["test_id"]):
                pending.append({
                    "action": "quarantine",
                    "test_id": c["test_id"],
                    "reason": c["rule"],
                    "fail_rate": c["fail_rate"],
                    "proposed_date": str(date.today()),
                })
                added += 1
                _log.info("Proposed quarantine: %s (%.0f%% fail rate)", c["test_id"], c["fail_rate"] * 100)

        for c in unquarantine_candidates:
            if self._is_quarantined(data, c["test_id"]) and not self._is_pending(pending, c["test_id"]):
                pending.append({
                    "action": "unquarantine",
                    "test_id": c["test_id"],
                    "reason": c["rule"],
                    "consecutive_passes": c["consecutive_passes"],
                    "proposed_date": str(date.today()),
                })
                added += 1
                _log.info("Proposed unquarantine: %s (%d consecutive passes)", c["test_id"], c["consecutive_passes"])

        self._save_quarantine(data)
        return added

    def apply_pending(self) -> dict[str, list[str]]:
        """
        Promote all pending_actions to active quarantine/release.
        Returns summary of applied changes.
        """
        data = self._load_quarantine()
        pending: list[dict] = data.pop("pending_actions", [])
        quarantined: list[dict] = data.setdefault("quarantined", [])
        applied: dict[str, list[str]] = {"quarantined": [], "unquarantined": []}

        for action in pending:
            tid = action["test_id"]
            if action["action"] == "quarantine":
                quarantined.append({
                    "test_id": tid,
                    "reason": action["reason"],
                    "quarantined_date": str(date.today()),
                    "consecutive_passes": 0,
                })
                applied["quarantined"].append(tid)
                _log.info("Quarantined: %s", tid)
            elif action["action"] == "unquarantine":
                quarantined[:] = [q for q in quarantined if q["test_id"] != tid]
                applied["unquarantined"].append(tid)
                _log.info("Unquarantined: %s", tid)

        self._save_quarantine(data)
        return applied

    # ── run history ────────────────────────────────────────────────────────

    def record_run(self, test_id: str, status: str, meta: dict | None = None):
        """Append one run result to run_history.yaml."""
        history = self._load_history()
        entry: dict = {"status": status, "date": str(date.today())}
        if meta:
            entry.update(meta)
        history.setdefault("tests", {}).setdefault(test_id, []).append(entry)
        cutoff = str(date.today() - timedelta(days=_HISTORY_WINDOW_DAYS))
        history["tests"][test_id] = [e for e in history["tests"][test_id] if e.get("date", "") >= cutoff]
        self._save_history(history)

    def record_run_bulk(self, results: list[dict]):
        """Batch-record results. Each item: {test_id, status, meta?}."""
        history = self._load_history()
        tests = history.setdefault("tests", {})
        today = str(date.today())
        for r in results:
            entry: dict = {"status": r["status"], "date": today}
            if "meta" in r:
                entry.update(r["meta"])
            tests.setdefault(r["test_id"], []).append(entry)
        cutoff = str(date.today() - timedelta(days=_HISTORY_WINDOW_DAYS))
        for tid in list(tests.keys()):
            tests[tid] = [e for e in tests[tid] if e.get("date", "") >= cutoff]
            if not tests[tid]:
                del tests[tid]
        self._save_history(history)

    # ── read side ──────────────────────────────────────────────────────────

    def quarantined_ids(self) -> set[str]:
        """Returns set of currently quarantined test node IDs."""
        data = self._load_quarantine()
        return {q["test_id"] for q in data.get("quarantined", [])}

    def pending_count(self) -> int:
        return len(self._load_quarantine().get("pending_actions", []))

    # ── internal ───────────────────────────────────────────────────────────

    def _load_quarantine(self) -> dict:
        if not self._qpath.exists():
            return {}
        with self._qpath.open(encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def _save_quarantine(self, data: dict):
        self._qpath.parent.mkdir(parents=True, exist_ok=True)
        with FileLock(str(self._qpath) + ".lock"):
            with self._qpath.open("w", encoding="utf-8") as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    def _load_history(self) -> dict:
        if not self._hpath.exists():
            return {"tests": {}}
        with self._hpath.open(encoding="utf-8") as f:
            return yaml.safe_load(f) or {"tests": {}}

    def _save_history(self, data: dict):
        self._hpath.parent.mkdir(parents=True, exist_ok=True)
        with FileLock(str(self._hpath) + ".lock"):
            with self._hpath.open("w", encoding="utf-8") as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    @staticmethod
    def _is_quarantined(data: dict, test_id: str) -> bool:
        return any(q["test_id"] == test_id for q in data.get("quarantined", []))

    @staticmethod
    def _is_pending(pending: list[dict], test_id: str) -> bool:
        return any(p["test_id"] == test_id for p in pending)
