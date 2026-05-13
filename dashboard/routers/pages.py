from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from collections import defaultdict

from utils.activity_log import ActivityLog
from utils.approval_manager import ApprovalManager
from dashboard.routers.approval_dispatch import derive_feature
from dashboard.routers.kb import _list_products

router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))

_alog = ActivityLog()
_am = ApprovalManager()


def _ctx(**kwargs) -> dict:
    return {"pending_count": len(_am.pending()), "all_products": _list_products(), **kwargs}


def _queued_gaps() -> list[dict]:
    """Return coverage gaps queued for generation, grouped by product+domain."""
    entries = [
        e for e in _alog.filter(event_type="approval_action", agent="human")
        if e.get("status") == "pending"
    ]
    by_context: dict[tuple, set] = defaultdict(set)
    for e in entries:
        for test_name in e.get("output", {}).get("gaps", []):
            feature = derive_feature(test_name)
            if feature:
                by_context[(e.get("product"), e.get("domain"))].add(feature)
    return [
        {"product": p, "domain": d, "features": sorted(feats)}
        for (p, d), feats in by_context.items()
    ]


@router.get("/", response_class=HTMLResponse)
async def home(request: Request, product: str | None = None):
    all_entries = _alog.all()
    scoped = [e for e in all_entries if e.get("product") == product] if product else all_entries
    pending = _am.pending()
    return templates.TemplateResponse(request, "index.html", context=_ctx(
        total_activities=len(scoped),
        pending_approvals=len(pending),
        requires_human_count=sum(1 for e in scoped if e.get("requires_human")),
        agent_count=9,
        recent=list(reversed(scoped))[:10],
        pending_items=pending[:3],
        queued_gaps=_queued_gaps(),
    ))


@router.get("/activities", response_class=HTMLResponse)
async def activities(
    request: Request,
    product: str | None = None,
    agent: str | None = None,
    domain: str | None = None,
    requires_human: str | None = None,
):
    all_entries = _alog.all()
    agents = sorted(set(e.get("agent", "") for e in all_entries if e.get("agent")))
    domains = sorted(set(e.get("domain", "") for e in all_entries if e.get("domain")))
    products = sorted(set(e.get("product") or "" for e in all_entries if e.get("product")))
    rh: bool | None = None
    if requires_human == "true":
        rh = True
    elif requires_human == "false":
        rh = False
    entries = _alog.filter(
        agent=agent or None,
        domain=domain or None,
        product=product or None,
        requires_human=rh,
    )
    return templates.TemplateResponse(request, "activities.html", context=_ctx(
        agents=agents,
        domains=domains,
        products=products,
        entries=list(reversed(entries))[:200],
    ))


@router.get("/approvals", response_class=HTMLResponse)
async def approvals(request: Request, product: str | None = None):
    pending = _am.pending()
    resolved = list(reversed(_am.resolved()))[:50]
    if product:
        pending = [p for p in pending if p.get("product") == product]
        resolved = [r for r in resolved if r.get("product") == product]
    return templates.TemplateResponse(request, "approvals.html", context=_ctx(
        pending=pending,
        resolved=resolved,
    ))


@router.get("/docs", response_class=HTMLResponse)
async def docs_page(request: Request, product: str | None = None):
    from dashboard.routers.docs import _find_docs
    all_docs = _find_docs()
    products = sorted(set(d["product"] for d in all_docs))
    domains = sorted(set(d["domain"] for d in all_docs))
    docs = _find_docs(product=product or None)
    return templates.TemplateResponse(request, "docs.html", context=_ctx(
        docs=docs, products=products, domains=domains,
    ))


@router.get("/scripts", response_class=HTMLResponse)
async def scripts_page(request: Request, product: str | None = None):
    from dashboard.routers.scripts import _find_scripts
    all_scripts = _find_scripts()
    products = sorted(set(s["product"] for s in all_scripts))
    domains = sorted(set(s["domain"] for s in all_scripts))
    scripts = _find_scripts(product=product or None)
    return templates.TemplateResponse(request, "scripts.html", context=_ctx(
        scripts=scripts, products=products, domains=domains,
    ))


@router.get("/agents", response_class=HTMLResponse)
async def agents_page(request: Request):
    import yaml
    from dashboard.routers.agents import _AGENT_REGISTRY
    from dashboard.agent_meta import AGENT_META
    config_path = Path(__file__).resolve().parent.parent.parent / "framework_knowledge" / "agent_config.yaml"
    agent_config: dict = {}
    if config_path.exists():
        data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        agent_config = data.get("agents", {})
    status_map: dict = {}
    for e in reversed(_alog.all()):
        name = e.get("agent", "")
        if name and name not in status_map:
            status_map[name] = e
    agents_data = [
        {**a, "last_run": status_map.get(a["name"]), "meta": AGENT_META.get(a["name"], {}), "config": agent_config.get(a["name"], {})}
        for a in _AGENT_REGISTRY
    ]
    return templates.TemplateResponse(request, "agents.html", context=_ctx(agents=agents_data))


@router.get("/quality", response_class=HTMLResponse)
async def quality_page(request: Request, product: str | None = None):
    from dashboard.routers.quality import compute_metrics, _all_test_functions
    from dashboard.routers.partials import _quarantine_groups
    metrics = compute_metrics(product)
    return templates.TemplateResponse(request, "quality.html", context=_ctx(
        metrics=metrics,
        filter_product=product or "",
        quarantine_groups=_quarantine_groups(product),
        all_tests=_all_test_functions(),
    ))


@router.get("/kb", response_class=HTMLResponse)
async def kb_page(request: Request, product: str | None = None):
    from dashboard.routers.kb import _list_products, _kb_files, _load_increments_log, _INCREMENTS_DIR, _TEXT_SUFFIXES
    from dashboard.routers.pipeline import _load_jobs
    products = _list_products()
    kb_files = {p: _kb_files(p) for p in products}
    selected_product = product if product and product in products else (products[0] if products else "")
    log = _load_increments_log()
    increment_files: list[str] = []
    if _INCREMENTS_DIR.exists():
        increment_files = sorted(
            f.name for f in _INCREMENTS_DIR.iterdir()
            if f.suffix in _TEXT_SUFFIXES and f.name != ".gitkeep"
        )
    increments = [{"filename": fn, "processed": fn in log, "log": log.get(fn)} for fn in increment_files]
    recent_jobs = list(reversed(_load_jobs()))[:20]
    return templates.TemplateResponse(request, "kb.html", context=_ctx(
        products=products,
        kb_files=kb_files,
        increments=increments,
        recent_jobs=recent_jobs,
        queued_gaps=_queued_gaps(),
        selected_product=selected_product,
    ))
