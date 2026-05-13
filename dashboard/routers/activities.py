from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from utils.activity_log import ActivityLog

router = APIRouter(prefix="/activities", tags=["activities"])
_alog = ActivityLog()


@router.get("/")
def list_activities(
    limit: int = Query(50, ge=1, le=500),
    agent: str | None = None,
    domain: str | None = None,
    product: str | None = None,
    requires_human: bool | None = None,
    event_type: str | None = None,
):
    entries = _alog.filter(
        agent=agent,
        domain=domain,
        product=product,
        requires_human=requires_human,
        event_type=event_type,
    )
    return {"entries": list(reversed(entries))[-limit:], "total": len(entries)}


@router.get("/{entry_id}")
def get_activity(entry_id: str):
    entry = _alog.get(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Activity not found")
    return entry
