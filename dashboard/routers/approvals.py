from __future__ import annotations

from fastapi import APIRouter, Body, HTTPException

from core.approval_manager import ApprovalManager

router = APIRouter(prefix="/approvals", tags=["approvals"])
_am = ApprovalManager()


@router.get("/")
def list_pending(approval_type: str | None = None):
    items = _am.pending(approval_type)
    return {"pending": items, "total": len(items)}


@router.get("/resolved")
def list_resolved(limit: int = 100):
    items = _am.resolved(limit)
    return {"resolved": items, "total": len(items)}


@router.get("/{approval_id}")
def get_approval(approval_id: str):
    item = _am.get(approval_id)
    if not item:
        raise HTTPException(status_code=404, detail="Approval not found")
    return item


@router.post("/{approval_id}/approve")
def approve(approval_id: str, notes: str = Body("", embed=True)):
    ok = _am.resolve(approval_id, decision="approved", notes=notes)
    if not ok:
        raise HTTPException(status_code=404, detail="Approval not found")
    return {"status": "approved", "id": approval_id}


@router.post("/{approval_id}/reject")
def reject(approval_id: str, notes: str = Body("", embed=True)):
    ok = _am.resolve(approval_id, decision="rejected", notes=notes)
    if not ok:
        raise HTTPException(status_code=404, detail="Approval not found")
    return {"status": "rejected", "id": approval_id}
