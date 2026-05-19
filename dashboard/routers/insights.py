"""Product insights + strategic roadmap API — master-admin-only routes."""
from __future__ import annotations

import logging
import uuid
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel

from core.insights_manager import InsightsManager
from core.roadmap_manager import RoadmapManager
from dashboard.routers.auth import require_user

_log = logging.getLogger(__name__)

router = APIRouter(prefix="/insights", tags=["insights"])
_im = InsightsManager()
_rm = RoadmapManager()

_AGENT_TYPES = {"product_manager", "dev_architect", "qa_architect", "ux_architect"}
_agent_cls_cache: dict[str, Any] = {}

# In-memory run state per agent (and cto)
_run_state: dict[str, dict] = {
    a: {"state": "idle", "error": None}
    for a in (*_AGENT_TYPES, "cto")
}


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
    _run_state[agent_type] = {"state": "running", "error": None}
    try:
        from ai.agents.base_agent import AgentContext
        from core.ai_factory import create_ai_client_from_dashboard
        client = create_ai_client_from_dashboard()
        if not client:
            _run_state[agent_type] = {"state": "error", "error": "No AI provider configured — check Settings"}
            return
        cls = _agent_classes().get(agent_type)
        if not cls:
            _run_state[agent_type] = {"state": "error", "error": "Unknown agent type"}
            return
        ctx = AgentContext(domain="product")
        agent = cls(ai_client=client, context=ctx)
        result = agent.run()
        err = result.get("error")
        if err:
            _run_state[agent_type] = {"state": "error", "error": err}
            return
        insights = result.get("insights", [])
        if insights:
            _im.save_insights(agent_type, insights, str(uuid.uuid4()))
            _run_state[agent_type] = {"state": "done", "error": None}
        else:
            _run_state[agent_type] = {"state": "error", "error": "LLM returned no parseable insights — check model or prompt"}
    except Exception as exc:
        _log.exception("insights agent %s failed", agent_type)
        _run_state[agent_type] = {"state": "error", "error": str(exc)}


def _run_cto_task() -> None:
    _run_state["cto"] = {"state": "running", "error": None}
    try:
        from ai.agents.base_agent import AgentContext
        from ai.agents.cto_agent import CTOAgent
        from core.ai_factory import create_ai_client_from_dashboard
        client = create_ai_client_from_dashboard()
        if not client:
            _run_state["cto"] = {"state": "error", "error": "No AI provider configured — check Settings"}
            return
        ctx = AgentContext(domain="product")
        result = CTOAgent(ai_client=client, context=ctx).run()
        err = result.get("error")
        if err:
            _run_state["cto"] = {"state": "error", "error": err}
            return
        items = result.get("items", [])
        if not items:
            _run_state["cto"] = {"state": "error", "error": "No items selected — run the 4 expert agents first"}
            return
        for item in items:
            _rm.create_item(item["insight"], item["rationale"])
            _im.update_status(item["insight"]["id"], "planned")
        _run_state["cto"] = {"state": "done", "error": None}
    except Exception as exc:
        _log.exception("CTO agent failed")
        _run_state["cto"] = {"state": "error", "error": str(exc)}


# ── insight endpoints ──────────────────────────────────────────────────────────

@router.get("/")
def list_insights(
    agent_type: str | None = None,
    status: str | None = None,
    _: dict = Depends(_require_master_admin),
):
    return {"insights": _im.list_insights(agent_type, status)}


@router.get("/runs")
def latest_runs(_: dict = Depends(_require_master_admin)):
    return {
        "runs": _im.latest_runs(),
        "state": dict(_run_state),
        "cto_run_at": _rm.latest_run_at(),
    }


@router.post("/run/{agent_type}")
def trigger_run(
    agent_type: str,
    background_tasks: BackgroundTasks,
    _: dict = Depends(_require_master_admin),
):
    if agent_type not in _AGENT_TYPES:
        raise HTTPException(status_code=404, detail="Unknown agent type")
    if _run_state.get(agent_type, {}).get("state") == "running":
        return {"status": "already_running", "agent_type": agent_type}
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


# ── roadmap endpoints ──────────────────────────────────────────────────────────

@router.get("/roadmap")
def list_roadmap(
    status: str | None = None,
    _: dict = Depends(_require_master_admin),
):
    return {"items": _rm.list_items(status)}


@router.post("/roadmap/run")
def trigger_cto_run(
    background_tasks: BackgroundTasks,
    _: dict = Depends(_require_master_admin),
):
    if _run_state.get("cto", {}).get("state") == "running":
        return {"status": "already_running"}
    background_tasks.add_task(_run_cto_task)
    return {"status": "queued"}


@router.patch("/roadmap/{item_id}")
def update_roadmap_status(
    item_id: str,
    body: _StatusUpdate,
    _: dict = Depends(_require_master_admin),
):
    ok = _rm.update_status(item_id, body.status)
    if not ok:
        raise HTTPException(status_code=400, detail="Invalid status or item not found")
    return {"ok": True}


@router.delete("/roadmap/{item_id}")
def remove_roadmap_item(
    item_id: str,
    _: dict = Depends(_require_master_admin),
):
    source_id = _rm.delete_item(item_id)
    if source_id is None:
        raise HTTPException(status_code=404, detail="Item not found")
    _im.update_status(source_id, "active")
    return {"ok": True}
