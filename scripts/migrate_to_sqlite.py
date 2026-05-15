#!/usr/bin/env python3
"""One-shot migration: JSON/YAML flat files → SQLite.

Run once after deploying the SQLite-based managers:
    python scripts/migrate_to_sqlite.py

Safe to re-run (uses INSERT OR IGNORE for all records).
After verifying the migration, old files can be archived or deleted.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import yaml  # noqa: E402

from core.db import get_conn, init_db  # noqa: E402
from utils.paths import ROOT  # noqa: E402

_DATA = ROOT / "data"


def migrate_activity_log() -> int:
    path = _DATA / "activity_log.json"
    if not path.exists():
        print("  activity_log.json not found — skipping")
        return 0
    data = json.loads(path.read_text(encoding="utf-8"))
    entries = data.get("entries", [])
    conn = get_conn()
    count = 0
    for e in entries:
        try:
            conn.execute(
                """INSERT OR IGNORE INTO activity_log
                   (id, timestamp, event_type, agent, product, domain, status,
                    summary, output, requires_human, approval_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    e["id"], e["timestamp"], e["event_type"], e["agent"],
                    e.get("product"), e["domain"], e["status"], e["summary"],
                    json.dumps(e.get("output", {})),
                    1 if e.get("requires_human") else 0,
                    e.get("approval_id"),
                ),
            )
            count += 1
        except Exception as exc:
            print(f"  WARNING: skipped activity entry {e.get('id')}: {exc}")
    conn.commit()
    return count


def migrate_approvals() -> int:
    path = _DATA / "pending_approvals.yaml"
    if not path.exists():
        print("  pending_approvals.yaml not found — skipping")
        return 0
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    conn = get_conn()
    count = 0
    for item in data.get("pending", []):
        try:
            conn.execute(
                """INSERT OR IGNORE INTO approvals
                   (id, type, product, domain, title, proposed_date, details, status)
                   VALUES (?, ?, ?, ?, ?, ?, ?, 'pending')""",
                (
                    item["id"], item["type"], item.get("product"), item["domain"],
                    item["title"], item["proposed_date"],
                    json.dumps(item.get("details", {})),
                ),
            )
            count += 1
        except Exception as exc:
            print(f"  WARNING: skipped pending approval {item.get('id')}: {exc}")
    for item in data.get("resolved", []):
        try:
            conn.execute(
                """INSERT OR IGNORE INTO approvals
                   (id, type, product, domain, title, proposed_date, details,
                    status, decision, resolved_date, resolved_by, notes)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    item["id"], item["type"], item.get("product"), item["domain"],
                    item["title"], item["proposed_date"],
                    json.dumps(item.get("details", {})),
                    item.get("decision", "approved"),
                    item.get("decision", "approved"),
                    item.get("resolved_date"), item.get("resolved_by", "human"),
                    item.get("notes", ""),
                ),
            )
            count += 1
        except Exception as exc:
            print(f"  WARNING: skipped resolved approval {item.get('id')}: {exc}")
    conn.commit()
    return count


def migrate_runs() -> int:
    store_dir = _DATA / "test_runs"
    if not store_dir.exists():
        print("  data/test_runs/ not found — skipping")
        return 0
    conn = get_conn()
    count = 0
    for f in store_dir.glob("*.json"):
        try:
            runs = json.loads(f.read_text(encoding="utf-8")).get("runs", [])
        except Exception as exc:
            print(f"  WARNING: could not parse {f.name}: {exc}")
            continue
        for r in runs:
            try:
                conn.execute(
                    """INSERT OR IGNORE INTO test_runs
                       (id, triggered_at, finished_at, product, domain, module,
                        trigger, schedule_id, status, total, passed, failed,
                        skipped, errors, duration, report_path, analyzed,
                        failure_categories, failures, run_config_snapshot)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        r["id"], r["triggered_at"], r.get("finished_at"),
                        r["product"], r["domain"], r.get("module", ""),
                        r.get("trigger", "manual"), r.get("schedule_id"),
                        r.get("status", "queued"),
                        r.get("total", 0), r.get("passed", 0), r.get("failed", 0),
                        r.get("skipped", 0), r.get("errors", 0), r.get("duration", 0.0),
                        r.get("report_path", ""),
                        1 if r.get("analyzed") else 0,
                        json.dumps(r.get("failure_categories", {})),
                        json.dumps(r.get("failures", [])),
                        json.dumps(r.get("run_config_snapshot", {})),
                    ),
                )
                count += 1
            except Exception as exc:
                print(f"  WARNING: skipped run {r.get('id')}: {exc}")
    conn.commit()
    return count


def migrate_schedules() -> int:
    store_dir = _DATA / "test_schedules"
    if not store_dir.exists():
        print("  data/test_schedules/ not found — skipping")
        return 0
    conn = get_conn()
    count = 0
    for f in store_dir.glob("*.json"):
        try:
            schedules = json.loads(f.read_text(encoding="utf-8")).get("schedules", [])
        except Exception as exc:
            print(f"  WARNING: could not parse {f.name}: {exc}")
            continue
        for s in schedules:
            try:
                conn.execute(
                    """INSERT OR IGNORE INTO test_schedules
                       (id, name, product, domain, module, hour, minute, days,
                        enabled, created_at, last_run_id, last_run_at,
                        environment, browser, device)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        s["id"], s["name"], s["product"], s["domain"],
                        s.get("module", ""),
                        s.get("hour", 2), s.get("minute", 0),
                        json.dumps(s.get("days", ["mon","tue","wed","thu","fri"])),
                        1 if s.get("enabled", True) else 0,
                        s.get("created_at", ""),
                        s.get("last_run_id"), s.get("last_run_at"),
                        s.get("environment", ""), s.get("browser", ""), s.get("device", ""),
                    ),
                )
                count += 1
            except Exception as exc:
                print(f"  WARNING: skipped schedule {s.get('id')}: {exc}")
    conn.commit()
    return count


def migrate_quarantine() -> int:
    path = _DATA / "quarantine.yaml"
    if not path.exists():
        print("  quarantine.yaml not found — skipping")
        return 0
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    conn = get_conn()
    count = 0
    for q in data.get("quarantined", []):
        try:
            conn.execute(
                """INSERT OR IGNORE INTO quarantine
                   (test_id, reason, quarantined_date, consecutive_passes)
                   VALUES (?, ?, ?, ?)""",
                (
                    q["test_id"], q.get("reason", ""),
                    q.get("quarantined_date", ""),
                    q.get("consecutive_passes", 0),
                ),
            )
            count += 1
        except Exception as exc:
            print(f"  WARNING: skipped quarantine {q.get('test_id')}: {exc}")
    for p in data.get("pending_actions", []):
        try:
            conn.execute(
                """INSERT OR IGNORE INTO quarantine_pending
                   (action, test_id, reason, fail_rate, consecutive_passes, proposed_date)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    p["action"], p["test_id"], p.get("reason", ""),
                    p.get("fail_rate"), p.get("consecutive_passes"),
                    p.get("proposed_date", ""),
                ),
            )
            count += 1
        except Exception as exc:
            print(f"  WARNING: skipped pending quarantine {p.get('test_id')}: {exc}")
    conn.commit()
    return count


def migrate_run_history() -> int:
    path = _DATA / "run_history.yaml"
    if not path.exists():
        print("  run_history.yaml not found — skipping")
        return 0
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    conn = get_conn()
    count = 0
    rows = []
    for test_id, runs in data.get("tests", {}).items():
        for r in runs:
            rows.append((test_id, r.get("status", ""), r.get("date", ""), r.get("duration")))
    try:
        conn.executemany(
            "INSERT INTO run_history (test_id, status, date, duration) VALUES (?, ?, ?, ?)",
            rows,
        )
        count = len(rows)
    except Exception as exc:
        print(f"  WARNING: run_history partial failure: {exc}")
    conn.commit()
    return count


def main() -> None:
    print("SentinelFlux → SQLite migration")
    print("=" * 40)
    init_db()
    steps = [
        ("Activity log", migrate_activity_log),
        ("Approvals", migrate_approvals),
        ("Test runs", migrate_runs),
        ("Test schedules", migrate_schedules),
        ("Quarantine", migrate_quarantine),
        ("Run history", migrate_run_history),
    ]
    for label, fn in steps:
        print(f"\n{label}...")
        n = fn()
        print(f"  Migrated {n} records")

    print("\nDone. Verify with: sqlite3 data/sentinelflux.db '.tables'")
    print("Old files are untouched — archive or delete them manually once verified.")


if __name__ == "__main__":
    main()
