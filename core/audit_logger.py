"""Append-only audit log for auth events and configuration changes."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from utils.paths import ROOT as _ROOT

_AUDIT_PATH = _ROOT / "data" / "audit_log.json"
_MAX_EVENTS = 2000


def _load() -> list[dict]:
    if _AUDIT_PATH.exists():
        try:
            return json.loads(_AUDIT_PATH.read_text(encoding="utf-8")) or []
        except Exception:
            return []
    return []


def _save(events: list[dict]) -> None:
    _AUDIT_PATH.write_text(json.dumps(events, indent=2, ensure_ascii=False), encoding="utf-8")


def log(
    event_type: str,
    user_email: str,
    user_name: str,
    detail: str,
    *,
    ip: str = "",
    section: str = "",
) -> None:
    """Append one audit event. event_type: 'login' | 'logout' | 'config_change'."""
    events = _load()
    events.append({
        "id": f"aud_{uuid.uuid4().hex[:8]}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "type": event_type,
        "user_email": user_email,
        "user_name": user_name,
        "section": section,
        "detail": detail,
        "ip": ip,
    })
    if len(events) > _MAX_EVENTS:
        events = events[-_MAX_EVENTS:]
    _save(events)


def recent(limit: int = 200) -> list[dict]:
    """Return the most recent events, newest first."""
    return list(reversed(_load()))[:limit]
