"""
ActivityLog — append-only event store for all agent and pipeline runs.

Written by SentinelOrchestrator (and individual agents if needed).
Read by the FastAPI dashboard backend.

File: data/activity_log.json
Trims to MAX_ENTRIES on each write to prevent unbounded growth.
"""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from filelock import FileLock

from utils.paths import ROOT as _ROOT_DIR

_log = logging.getLogger("sentinelflux.activity_log")
_LOG_PATH = _ROOT_DIR / "data" / "activity_log.json"

MAX_ENTRIES = 1000


class ActivityLog:
    def __init__(self, path: Path = _LOG_PATH):
        self._path = path

    def append(
        self,
        *,
        event_type: str,
        agent: str,
        domain: str,
        status: str,
        summary: str,
        product: str | None = None,
        output: dict[str, Any] | None = None,
        requires_human: bool = False,
        approval_id: str | None = None,
    ) -> str:
        """Append one event. Returns the new entry ID."""
        entry = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "agent": agent,
            "product": product,
            "domain": domain,
            "status": status,
            "summary": summary,
            "output": output or {},
            "requires_human": requires_human,
            "approval_id": approval_id,
        }
        data = self._load()
        data["entries"].append(entry)
        if len(data["entries"]) > MAX_ENTRIES:
            data["entries"] = data["entries"][-MAX_ENTRIES:]
        self._save(data)
        return entry["id"]

    def all(self) -> list[dict]:
        return self._load()["entries"]

    def get(self, entry_id: str) -> dict | None:
        for e in self._load()["entries"]:
            if e["id"] == entry_id:
                return e
        return None

    def recent(self, n: int = 50) -> list[dict]:
        return self._load()["entries"][-n:]

    def filter(
        self,
        *,
        agent: str | None = None,
        domain: str | None = None,
        product: str | None = None,
        requires_human: bool | None = None,
        event_type: str | None = None,
    ) -> list[dict]:
        entries = self.all()
        if agent:
            entries = [e for e in entries if e.get("agent") == agent]
        if domain:
            entries = [e for e in entries if e.get("domain") == domain]
        if product:
            entries = [e for e in entries if e.get("product") == product]
        if requires_human is not None:
            entries = [e for e in entries if e.get("requires_human") == requires_human]
        if event_type:
            entries = [e for e in entries if e.get("event_type") == event_type]
        return entries

    def _load(self) -> dict:
        if not self._path.exists():
            return {"entries": []}
        with self._path.open(encoding="utf-8") as f:
            return json.load(f)

    def _save(self, data: dict):
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with FileLock(str(self._path) + ".lock"):
            with self._path.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
