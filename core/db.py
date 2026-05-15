"""SQLite connection management and schema for SentinelFlux.

WAL mode: concurrent reads + serialized writes. Safe for single-machine,
multi-thread use (FastAPI + uvicorn thread pool). Each thread gets its own
connection via threading.local().

To upgrade to PostgreSQL later: replace get_conn() and the _DDL list.
The manager classes (activity_log, approval_manager, run_manager,
quarantine_manager) use only standard SQL that works on both.
"""
from __future__ import annotations

import sqlite3
import threading
from pathlib import Path

from utils.paths import ROOT as _ROOT_DIR

_DB_PATH = _ROOT_DIR / "data" / "sentinelflux.db"
_local = threading.local()
_init_lock = threading.Lock()
_initialized = False

_DDL = [
    """CREATE TABLE IF NOT EXISTS activity_log (
        id TEXT PRIMARY KEY,
        timestamp TEXT NOT NULL,
        event_type TEXT NOT NULL,
        agent TEXT NOT NULL,
        product TEXT,
        domain TEXT NOT NULL,
        status TEXT NOT NULL,
        summary TEXT NOT NULL,
        output TEXT NOT NULL DEFAULT '{}',
        requires_human INTEGER NOT NULL DEFAULT 0,
        approval_id TEXT
    )""",
    "CREATE INDEX IF NOT EXISTS idx_alog_timestamp ON activity_log(timestamp)",
    """CREATE TABLE IF NOT EXISTS approvals (
        id TEXT PRIMARY KEY,
        type TEXT NOT NULL,
        product TEXT,
        domain TEXT NOT NULL,
        title TEXT NOT NULL,
        proposed_date TEXT NOT NULL,
        details TEXT NOT NULL DEFAULT '{}',
        status TEXT NOT NULL DEFAULT 'pending',
        decision TEXT,
        resolved_date TEXT,
        resolved_by TEXT,
        notes TEXT
    )""",
    """CREATE TABLE IF NOT EXISTS test_runs (
        id TEXT PRIMARY KEY,
        triggered_at TEXT NOT NULL,
        finished_at TEXT,
        product TEXT NOT NULL,
        domain TEXT NOT NULL,
        module TEXT NOT NULL DEFAULT '',
        trigger TEXT NOT NULL DEFAULT 'manual',
        schedule_id TEXT,
        status TEXT NOT NULL DEFAULT 'queued',
        total INTEGER NOT NULL DEFAULT 0,
        passed INTEGER NOT NULL DEFAULT 0,
        failed INTEGER NOT NULL DEFAULT 0,
        skipped INTEGER NOT NULL DEFAULT 0,
        errors INTEGER NOT NULL DEFAULT 0,
        duration REAL NOT NULL DEFAULT 0.0,
        report_path TEXT NOT NULL DEFAULT '',
        analyzed INTEGER NOT NULL DEFAULT 0,
        failure_categories TEXT NOT NULL DEFAULT '{}',
        failures TEXT NOT NULL DEFAULT '[]',
        run_config_snapshot TEXT NOT NULL DEFAULT '{}'
    )""",
    "CREATE INDEX IF NOT EXISTS idx_runs_product ON test_runs(product, triggered_at)",
    """CREATE TABLE IF NOT EXISTS test_schedules (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        product TEXT NOT NULL,
        domain TEXT NOT NULL,
        module TEXT NOT NULL DEFAULT '',
        hour INTEGER NOT NULL DEFAULT 2,
        minute INTEGER NOT NULL DEFAULT 0,
        days TEXT NOT NULL DEFAULT '["mon","tue","wed","thu","fri"]',
        enabled INTEGER NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL,
        last_run_id TEXT,
        last_run_at TEXT,
        environment TEXT NOT NULL DEFAULT '',
        browser TEXT NOT NULL DEFAULT '',
        device TEXT NOT NULL DEFAULT ''
    )""",
    """CREATE TABLE IF NOT EXISTS quarantine (
        test_id TEXT PRIMARY KEY,
        domain TEXT,
        product TEXT,
        reason TEXT NOT NULL DEFAULT '',
        quarantined_date TEXT NOT NULL,
        consecutive_passes INTEGER NOT NULL DEFAULT 0
    )""",
    """CREATE TABLE IF NOT EXISTS quarantine_pending (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action TEXT NOT NULL,
        test_id TEXT NOT NULL,
        reason TEXT NOT NULL DEFAULT '',
        fail_rate REAL,
        consecutive_passes INTEGER,
        proposed_date TEXT NOT NULL,
        domain TEXT,
        product TEXT
    )""",
    """CREATE TABLE IF NOT EXISTS run_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        test_id TEXT NOT NULL,
        status TEXT NOT NULL,
        date TEXT NOT NULL,
        duration REAL,
        domain TEXT,
        product TEXT
    )""",
    "CREATE INDEX IF NOT EXISTS idx_history_test_id ON run_history(test_id)",
    "CREATE INDEX IF NOT EXISTS idx_history_date ON run_history(date)",
]


def get_conn() -> sqlite3.Connection:
    """Return thread-local SQLite connection, initialising schema on first use."""
    global _initialized
    conn = getattr(_local, "conn", None)
    if conn is None:
        _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(_DB_PATH))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        _local.conn = conn
    if not _initialized:
        with _init_lock:
            if not _initialized:
                _apply_schema(conn)
                _initialized = True
    return conn


def init_db() -> None:
    """Explicit schema init — call at app startup to warm the connection."""
    get_conn()


def apply_schema(conn: sqlite3.Connection) -> None:
    """Apply DDL to any connection — used by managers with custom DB paths (e.g. tests)."""
    for stmt in _DDL:
        conn.execute(stmt)
    conn.commit()


# Internal alias used by get_conn
_apply_schema = apply_schema
