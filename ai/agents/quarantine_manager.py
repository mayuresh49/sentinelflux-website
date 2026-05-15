"""
QuarantineManager — manages test quarantine via SQLite.

Semi-autonomous design
----------------------
FlakyDetectorAgent → propose()      writes to quarantine_pending (human can review)
human / CI gate    → apply_pending() promotes to quarantined

conftest.py reads quarantined_ids() at collection time and marks tests xfail.

To go fully autonomous: call apply_pending() immediately after propose()
in your pipeline without a human gate.
"""
from __future__ import annotations

import logging
from datetime import date, timedelta
from pathlib import Path

from core.db import get_conn

_log = logging.getLogger("sentinelflux.agents.quarantine_manager")
_HISTORY_WINDOW_DAYS = 90


class QuarantineManager:
    def __init__(
        self,
        quarantine_path: Path | None = None,
        history_path: Path | None = None,
    ):
        pass  # paths kept for API compat; storage is now SQLite

    # ── quarantine write side ──────────────────────────────────────────────

    def propose(
        self,
        quarantine_candidates: list[dict],
        unquarantine_candidates: list[dict],
    ) -> int:
        """Write candidates to quarantine_pending. Returns number added."""
        added = 0
        conn = get_conn()
        quarantined = {r[0] for r in conn.execute("SELECT test_id FROM quarantine").fetchall()}
        pending = {r[0] for r in conn.execute("SELECT test_id FROM quarantine_pending").fetchall()}

        for c in quarantine_candidates:
            tid = c["test_id"]
            if tid not in quarantined and tid not in pending:
                conn.execute(
                    """INSERT INTO quarantine_pending
                       (action, test_id, reason, fail_rate, proposed_date)
                       VALUES ('quarantine', ?, ?, ?, ?)""",
                    (tid, c["rule"], c["fail_rate"], str(date.today())),
                )
                added += 1
                _log.info("Proposed quarantine: %s (%.0f%% fail rate)", tid, c["fail_rate"] * 100)

        for c in unquarantine_candidates:
            tid = c["test_id"]
            if tid in quarantined and tid not in pending:
                conn.execute(
                    """INSERT INTO quarantine_pending
                       (action, test_id, reason, consecutive_passes, proposed_date)
                       VALUES ('unquarantine', ?, ?, ?, ?)""",
                    (tid, c["rule"], c["consecutive_passes"], str(date.today())),
                )
                added += 1
                _log.info("Proposed unquarantine: %s (%d consecutive passes)", tid, c["consecutive_passes"])

        conn.commit()
        return added

    def apply_pending(self) -> dict[str, list[str]]:
        """Promote all quarantine_pending to active quarantine/release."""
        applied: dict[str, list[str]] = {"quarantined": [], "unquarantined": []}
        conn = get_conn()
        rows = conn.execute("SELECT * FROM quarantine_pending").fetchall()

        for row in rows:
            tid = row["test_id"]
            if row["action"] == "quarantine":
                conn.execute(
                    """INSERT OR REPLACE INTO quarantine
                       (test_id, reason, quarantined_date, consecutive_passes)
                       VALUES (?, ?, ?, 0)""",
                    (tid, row["reason"], str(date.today())),
                )
                applied["quarantined"].append(tid)
                _log.info("Quarantined: %s", tid)
            elif row["action"] == "unquarantine":
                conn.execute("DELETE FROM quarantine WHERE test_id = ?", (tid,))
                applied["unquarantined"].append(tid)
                _log.info("Unquarantined: %s", tid)

        conn.execute("DELETE FROM quarantine_pending")
        conn.commit()
        return applied

    # ── run history ────────────────────────────────────────────────────────

    def record_run(self, test_id: str, status: str, meta: dict | None = None):
        """Append one run result to run_history."""
        conn = get_conn()
        today = str(date.today())
        duration = (meta or {}).get("duration")
        conn.execute(
            "INSERT INTO run_history (test_id, status, date, duration) VALUES (?, ?, ?, ?)",
            (test_id, status, today, duration),
        )
        cutoff = str(date.today() - timedelta(days=_HISTORY_WINDOW_DAYS))
        conn.execute(
            "DELETE FROM run_history WHERE test_id = ? AND date < ?", (test_id, cutoff)
        )
        conn.commit()

    def record_run_bulk(self, results: list[dict]):
        """Batch-record results. Each item: {test_id, status, meta?}."""
        conn = get_conn()
        today = str(date.today())
        conn.executemany(
            "INSERT INTO run_history (test_id, status, date, duration) VALUES (?, ?, ?, ?)",
            [
                (r["test_id"], r["status"], today, r.get("meta", {}).get("duration"))
                for r in results
            ],
        )
        cutoff = str(date.today() - timedelta(days=_HISTORY_WINDOW_DAYS))
        conn.execute("DELETE FROM run_history WHERE date < ?", (cutoff,))
        conn.commit()

    # ── read side ──────────────────────────────────────────────────────────

    def quarantined_ids(self) -> set[str]:
        rows = get_conn().execute("SELECT test_id FROM quarantine").fetchall()
        return {r[0] for r in rows}

    def pending_count(self) -> int:
        return get_conn().execute(
            "SELECT COUNT(*) FROM quarantine_pending"
        ).fetchone()[0]
