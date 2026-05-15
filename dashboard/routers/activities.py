from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from core.activity_log import ActivityLog
from dashboard.routers.auth import require_user, user_products

router = APIRouter(prefix="/activities", tags=["activities"])
_alog = ActivityLog()


def _visible_products(current_user: dict) -> list[str]:
    from dashboard.routers.kb import _list_products
    return user_products(current_user, _list_products())


@router.get("/")
def list_activities(
    limit: int = Query(50, ge=1, le=500),
    agent: str | None = None,
    domain: str | None = None,
    product: str | None = None,
    requires_human: bool | None = None,
    event_type: str | None = None,
    current_user: dict = Depends(require_user),
):
    visible = _visible_products(current_user)
    if product and product not in visible:
        return {"entries": [], "total": 0}
    entries = _alog.filter(
        agent=agent,
        domain=domain,
        product=product,
        requires_human=requires_human,
        event_type=event_type,
    )
    if not current_user.get("admin"):
        entries = [e for e in entries if e.get("product") in visible]
    entries = list(reversed(entries))
    return {"entries": entries[-limit:], "total": len(entries)}


@router.get("/{entry_id}")
def get_activity(entry_id: str, current_user: dict = Depends(require_user)):
    visible = _visible_products(current_user)
    entry = _alog.get(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Activity not found")
    if not current_user.get("admin") and entry.get("product") not in visible:
        raise HTTPException(status_code=403, detail="Access denied")
    return entry
