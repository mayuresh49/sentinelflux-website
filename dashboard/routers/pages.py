from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from collections import defaultdict

from core.activity_log import ActivityLog
from core.approval_manager import ApprovalManager
from dashboard.routers.approval_dispatch import derive_feature
from dashboard.routers.kb import _list_products
from dashboard.routers.auth import get_session_user, user_products

router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))

_alog = ActivityLog()
_am = ApprovalManager()


def _require_auth(request: Request) -> dict:
    """Dependency: return session user or redirect to /login."""
    user = get_session_user(request)
    if user is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=307, headers={"Location": f"/login?next={request.url.path}"})
    return user


def _ctx(request: Request, current_user: dict, **kwargs) -> dict:
    all_prods = _list_products()
    visible = user_products(current_user, all_prods)
    return {
        "pending_count": len(_am.pending()),
        "all_products": visible,
        "current_user": current_user,
        **kwargs,
    }


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
async def home(request: Request, product: str | None = None,
               current_user: dict = Depends(_require_auth)):
    from dashboard.routers.agents import _AGENT_REGISTRY
    all_entries = _alog.all()
    visible = user_products(current_user, _list_products())
    if product and product not in visible:
        product = None
    scoped = [e for e in all_entries if e.get("product") == product] if product else all_entries
    pending = _am.pending()
    pending_ids = {p["id"] for p in pending}
    recent = [e for e in reversed(scoped) if e.get("agent") != "human"][:10]
    status_map: dict = {}
    for e in reversed(all_entries):
        name = e.get("agent", "")
        if name and name not in status_map:
            status_map[name] = e
    agent_flow = [
        {
            "name": a["name"],
            "requires_ai": a["requires_ai"],
            "description": a["description"],
            "status": status_map[a["name"]]["status"] if a["name"] in status_map else "never",
        }
        for a in _AGENT_REGISTRY
    ]
    return templates.TemplateResponse(request, "index.html", context=_ctx(
        request, current_user,
        total_activities=len(scoped),
        pending_approvals=len(pending),
        requires_human_count=len(pending),
        agent_count=9,
        recent=recent,
        pending_ids=pending_ids,
        pending_items=pending[:3],
        queued_gaps=_queued_gaps(),
        agent_flow=agent_flow,
    ))


@router.get("/activities", response_class=HTMLResponse)
async def activities(
    request: Request,
    product: str | None = None,
    agent: str | None = None,
    domain: str | None = None,
    requires_human: str | None = None,
    current_user: dict = Depends(_require_auth),
):
    all_entries = _alog.all()
    visible = user_products(current_user, _list_products())
    agents = sorted(set(e.get("agent", "") for e in all_entries if e.get("agent")))
    domains = sorted(set(e.get("domain", "") for e in all_entries if e.get("domain")))
    products = [p for p in sorted(set(e.get("product") or "" for e in all_entries if e.get("product"))) if p in visible]
    if product and product not in visible:
        product = None
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
        request, current_user,
        agents=agents,
        domains=domains,
        products=products,
        entries=list(reversed(entries))[:200],
    ))


@router.get("/approvals", response_class=HTMLResponse)
async def approvals(request: Request, product: str | None = None,
                    current_user: dict = Depends(_require_auth)):
    visible = user_products(current_user, _list_products())
    pending = [p for p in _am.pending() if not p.get("product") or p.get("product") in visible]
    resolved = [r for r in list(reversed(_am.resolved()))[:50] if not r.get("product") or r.get("product") in visible]
    if product and product in visible:
        pending = [p for p in pending if p.get("product") == product]
        resolved = [r for r in resolved if r.get("product") == product]
    return templates.TemplateResponse(request, "approvals.html", context=_ctx(
        request, current_user,
        pending=pending,
        resolved=resolved,
    ))


@router.get("/docs", response_class=HTMLResponse)
async def docs_page(request: Request, product: str | None = None,
                    current_user: dict = Depends(_require_auth)):
    from dashboard.routers.docs import _find_docs
    visible = user_products(current_user, _list_products())
    if product and product not in visible:
        product = None
    all_docs = _find_docs()
    products = [p for p in sorted(set(d["product"] for d in all_docs)) if p in visible]
    domains = sorted(set(d["domain"] for d in all_docs))
    docs = _find_docs(product=product or None)
    docs = [d for d in docs if d["product"] in visible]
    return templates.TemplateResponse(request, "docs.html", context=_ctx(
        request, current_user, docs=docs, products=products, domains=domains,
    ))


@router.get("/scripts", response_class=HTMLResponse)
async def scripts_page(request: Request, product: str | None = None,
                       current_user: dict = Depends(_require_auth)):
    from dashboard.routers.scripts import _find_scripts
    visible = user_products(current_user, _list_products())
    if product and product not in visible:
        product = None
    all_scripts = _find_scripts()
    products = [p for p in sorted(set(s["product"] for s in all_scripts)) if p in visible]
    domains = sorted(set(s["domain"] for s in all_scripts))
    scripts = [s for s in _find_scripts(product=product or None) if s["product"] in visible]
    return templates.TemplateResponse(request, "scripts.html", context=_ctx(
        request, current_user, scripts=scripts, products=products, domains=domains,
    ))


@router.get("/assignments", response_class=HTMLResponse)
async def assignments_page(request: Request, current_user: dict = Depends(_require_auth)):
    from dashboard.routers.config_router import _load_config, _load_assignments, _all_tests
    cfg = _load_config()
    visible = user_products(current_user, _list_products())
    filter_product = request.query_params.get("product", "")
    if filter_product and filter_product not in visible:
        filter_product = ""
    assignments = _load_assignments()
    all_tests = [t for t in _all_tests() if t["product"] in visible]
    tests = [t for t in all_tests if t["product"] == filter_product] if filter_product else all_tests
    products = sorted(set(t["product"] for t in all_tests))
    return templates.TemplateResponse(request, "assignments.html", context=_ctx(
        request, current_user,
        cfg=cfg,
        labels=cfg.get("labels", []),
        priorities=cfg.get("priorities", []),
        custom_fields=cfg.get("custom_fields", []),
        users=cfg.get("users", []),
        tests=tests,
        assignments=assignments,
        products=products,
        search="",
        filter_product=filter_product,
        filter_labels=[],
        filter_priority="",
        filter_owner="",
        filter_jira_exists="",
    ))


@router.get("/agents", response_class=HTMLResponse)
async def agents_page(request: Request, current_user: dict = Depends(_require_auth)):
    import yaml
    from dashboard.routers.agents import _AGENT_REGISTRY
    from dashboard.agent_meta import AGENT_META
    from utils.paths import ROOT as _ROOT
    config_path = _ROOT / "ai" / "context" / "agent_config.yaml"
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
    return templates.TemplateResponse(request, "agents.html", context=_ctx(
        request, current_user, agents=agents_data,
    ))


@router.get("/quality", response_class=HTMLResponse)
async def quality_page(request: Request, product: str | None = None,
                       current_user: dict = Depends(_require_auth)):
    from dashboard.routers.quality import compute_metrics, _all_test_functions
    from dashboard.routers.partials import _quarantine_groups
    visible = user_products(current_user, _list_products())
    if product and product not in visible:
        product = None
    metrics = compute_metrics(product)
    return templates.TemplateResponse(request, "quality.html", context=_ctx(
        request, current_user,
        metrics=metrics,
        filter_product=product or "",
        quarantine_groups=_quarantine_groups(product),
        all_tests=_all_test_functions(),
    ))


@router.get("/runs", response_class=HTMLResponse)
async def runs_page(
    request: Request,
    product: str | None = None,
    domain: str | None = None,
    status: str | None = None,
    current_user: dict = Depends(_require_auth),
):
    from core.run_manager import RunManager
    rm = RunManager()
    visible = user_products(current_user, _list_products())
    if product and product not in visible:
        product = None
    runs = list(reversed(rm.all_runs()))
    if product:
        runs = [r for r in runs if r.get("product") == product]
    if domain:
        runs = [r for r in runs if r.get("domain") == domain]
    if status:
        runs = [r for r in runs if r.get("status") == status]
    schedules = rm.all_schedules()
    any_running = any(r.get("status") in ("running", "queued") for r in rm.all_runs())
    return templates.TemplateResponse(request, "runs.html", context=_ctx(
        request, current_user,
        runs=runs[:100],
        schedules=schedules,
        any_running=any_running,
        filter_product=product or "",
        filter_domain=domain or "",
        filter_status=status or "",
    ))


@router.get("/kb", response_class=HTMLResponse)
async def kb_page(request: Request, product: str | None = None,
                  current_user: dict = Depends(_require_auth)):
    from dashboard.routers.kb import _list_products, _kb_files, _load_increments_log, _INCREMENTS_DIR, _TEXT_SUFFIXES
    from dashboard.routers.pipeline import _load_jobs
    all_prods = _list_products()
    visible = user_products(current_user, all_prods)
    if product and product not in visible:
        product = None
    kb_files = {p: _kb_files(p) for p in visible}
    selected_product = product if product and product in visible else (visible[0] if visible else "")
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
        request, current_user,
        products=visible,
        kb_files=kb_files,
        increments=increments,
        recent_jobs=recent_jobs,
        queued_gaps=_queued_gaps(),
        selected_product=selected_product,
    ))


@router.get("/admin/users", response_class=HTMLResponse)
async def admin_users_page(request: Request, current_user: dict = Depends(_require_auth)):
    if not current_user.get("admin"):
        raise HTTPException(status_code=403, headers={"Location": "/"})
    from dashboard.routers.config_router import _load_config
    cfg = _load_config()
    return templates.TemplateResponse(request, "admin_users.html", context=_ctx(
        request, current_user,
        users=cfg.get("users", []),
        all_products=[p["name"] for p in cfg.get("products", []) if p.get("active", True)],
    ))


@router.get("/profile/password", response_class=HTMLResponse)
async def change_password_page(request: Request, current_user: dict = Depends(_require_auth)):
    return templates.TemplateResponse(request, "change_password.html", context=_ctx(
        request, current_user, saved=False, error="",
    ))


@router.post("/profile/password", response_class=HTMLResponse)
async def change_password_submit(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    current_user: dict = Depends(_require_auth),
):
    import bcrypt as _bcrypt
    from dashboard.routers.config_router import _load_config, _save_config
    cfg = _load_config()
    user_entry = next((u for u in cfg.get("users", []) if u["email"] == current_user["email"]), None)
    ctx = _ctx(request, current_user, saved=False, error="")
    if not user_entry:
        ctx["error"] = "User account not found."
        return templates.TemplateResponse(request, "change_password.html", context=ctx)
    stored_hash = user_entry.get("password_hash", "")
    if not stored_hash or not _bcrypt.checkpw(current_password.encode(), stored_hash.encode()):
        ctx["error"] = "Current password is incorrect."
        return templates.TemplateResponse(request, "change_password.html", context=ctx)
    if len(new_password.strip()) < 8:
        ctx["error"] = "New password must be at least 8 characters."
        return templates.TemplateResponse(request, "change_password.html", context=ctx)
    user_entry["password_hash"] = _bcrypt.hashpw(new_password.strip().encode(), _bcrypt.gensalt()).decode()
    _save_config(cfg)
    ctx["saved"] = True
    return templates.TemplateResponse(request, "change_password.html", context=ctx)
