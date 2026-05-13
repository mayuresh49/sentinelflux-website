from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from utils.activity_log import ActivityLog
from utils.approval_manager import ApprovalManager

router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))

_alog = ActivityLog()
_am = ApprovalManager()


def _ctx(**kwargs) -> dict:
    return {"pending_count": len(_am.pending()), **kwargs}


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    all_entries = _alog.all()
    pending = _am.pending()
    return templates.TemplateResponse(request, "index.html", context=_ctx(
        total_activities=len(all_entries),
        pending_approvals=len(pending),
        requires_human_count=sum(1 for e in all_entries if e.get("requires_human")),
        agent_count=9,
        recent=list(reversed(all_entries))[:10],
        pending_items=pending[:3],
    ))


@router.get("/activities", response_class=HTMLResponse)
async def activities(request: Request):
    all_entries = _alog.all()
    agents = sorted(set(e.get("agent", "") for e in all_entries if e.get("agent")))
    domains = sorted(set(e.get("domain", "") for e in all_entries if e.get("domain")))
    products = sorted(set(e.get("product") or "" for e in all_entries if e.get("product")))
    return templates.TemplateResponse(request, "activities.html", context=_ctx(
        agents=agents,
        domains=domains,
        products=products,
        entries=list(reversed(all_entries))[:200],
    ))


@router.get("/approvals", response_class=HTMLResponse)
async def approvals(request: Request):
    return templates.TemplateResponse(request, "approvals.html", context=_ctx(
        pending=_am.pending(),
        resolved=list(reversed(_am.resolved()))[:50],
    ))


@router.get("/docs", response_class=HTMLResponse)
async def docs_page(request: Request):
    from dashboard.routers.docs import _find_docs
    all_docs = _find_docs()
    products = sorted(set(d["product"] for d in all_docs))
    domains = sorted(set(d["domain"] for d in all_docs))
    return templates.TemplateResponse(request, "docs.html", context=_ctx(
        docs=all_docs, products=products, domains=domains,
    ))


@router.get("/scripts", response_class=HTMLResponse)
async def scripts_page(request: Request):
    from dashboard.routers.scripts import _find_scripts
    all_scripts = _find_scripts()
    products = sorted(set(s["product"] for s in all_scripts))
    domains = sorted(set(s["domain"] for s in all_scripts))
    return templates.TemplateResponse(request, "scripts.html", context=_ctx(
        scripts=all_scripts, products=products, domains=domains,
    ))


@router.get("/agents", response_class=HTMLResponse)
async def agents_page(request: Request):
    from dashboard.routers.agents import _AGENT_REGISTRY
    status_map: dict = {}
    for e in reversed(_alog.all()):
        name = e.get("agent", "")
        if name and name not in status_map:
            status_map[name] = e
    agents_data = [{**a, "last_run": status_map.get(a["name"])} for a in _AGENT_REGISTRY]
    return templates.TemplateResponse(request, "agents.html", context=_ctx(agents=agents_data))
