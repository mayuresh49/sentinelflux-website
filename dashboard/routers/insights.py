"""Product insights API — master-admin-only routes."""
from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel

from core.insights_manager import InsightsManager
from dashboard.routers.auth import require_user

router = APIRouter(prefix="/insights", tags=["insights"])
_im = InsightsManager()

_AGENT_TYPES = {"product_manager", "dev_architect", "qa_architect", "ux_architect"}
_agent_cls_cache: dict[str, Any] = {}


def _require_master_admin(current_user: dict = Depends(require_user)) -> dict:
    if not current_user.get("master_admin"):
        raise HTTPException(status_code=403, detail="Master admin access required")
    return current_user


def _agent_classes() -> dict[str, Any]:
    if not _agent_cls_cache:
        from ai.agents.product_review_agents import (
            DevArchitectAgent,
            ProductManagerAgent,
            QAArchitectAgent,
            UXArchitectAgent,
        )
        _agent_cls_cache.update({
            "product_manager": ProductManagerAgent,
            "dev_architect": DevArchitectAgent,
            "qa_architect": QAArchitectAgent,
            "ux_architect": UXArchitectAgent,
        })
    return _agent_cls_cache


def _run_agent_task(agent_type: str) -> None:
    from ai.agents.base_agent import AgentContext
    from core.ai_factory import create_ai_client_from_dashboard
    client = create_ai_client_from_dashboard()
    cls = _agent_classes().get(agent_type)
    if not cls:
        return
    ctx = AgentContext(domain="product")
    agent = cls(ai_client=client, context=ctx)
    result = agent.run()
    insights = result.get("insights", [])
    if insights:
        _im.save_insights(agent_type, insights, str(uuid.uuid4()))


@router.get("/")
def list_insights(
    agent_type: str | None = None,
    status: str | None = None,
    _: dict = Depends(_require_master_admin),
):
    return {"insights": _im.list_insights(agent_type, status)}


@router.get("/runs")
def latest_runs(_: dict = Depends(_require_master_admin)):
    return {"runs": _im.latest_runs()}


@router.post("/run/{agent_type}")
def trigger_run(
    agent_type: str,
    background_tasks: BackgroundTasks,
    _: dict = Depends(_require_master_admin),
):
    if agent_type not in _AGENT_TYPES:
        raise HTTPException(status_code=404, detail="Unknown agent type")
    background_tasks.add_task(_run_agent_task, agent_type)
    return {"status": "queued", "agent_type": agent_type}


class _StatusUpdate(BaseModel):
    status: str


@router.patch("/{insight_id}")
def update_status(
    insight_id: str,
    body: _StatusUpdate,
    _: dict = Depends(_require_master_admin),
):
    ok = _im.update_status(insight_id, body.status)
    if not ok:
        raise HTTPException(status_code=400, detail="Invalid status or insight not found")
    return {"ok": True}


@router.delete("/agent/{agent_type}")
def clear_agent_insights(
    agent_type: str,
    _: dict = Depends(_require_master_admin),
):
    deleted = _im.delete_insights_by_agent(agent_type)
    return {"deleted": deleted}
