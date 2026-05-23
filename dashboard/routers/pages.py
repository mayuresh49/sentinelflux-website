from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from core.activity_log import ActivityLog
from core.approval_manager import ApprovalManager
from dashboard.routers.approval_dispatch import derive_feature
from dashboard.routers.auth import get_session_user, user_products
from dashboard.routers.kb import _list_products

router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))

_alog = ActivityLog()
_am = ApprovalManager()


def _require_auth(request: Request) -> dict:
    """Dependency: return session user or redirect to /login."""
    user = get_session_user(request)
    if user is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=303, headers={"Location": f"/login?next={request.url.path}"})
    return user


def _module_access(flag: str, current_user: dict) -> bool:
    try:
        from dashboard.routers.config._helpers import _load_config
        cfg = _load_config()
        if current_user.get("admin"):
            return True
        user_prods = set(current_user.get("products", []))
        return any(p.get(flag) and p["name"] in user_prods for p in cfg.get("products", []))
    except Exception:
        return bool(current_user.get("admin"))


def _vapt_access(current_user: dict) -> bool:
    try:
        from dashboard.routers.config._helpers import _load_config
        cfg = _load_config()
        if current_user.get("admin"):
            return True
        user_prods = set(current_user.get("products", []))
        return any(p.get("vapt_enabled") and p["name"] in user_prods for p in cfg.get("products", []))
    except Exception:
        return bool(current_user.get("admin"))


def _ctx(request: Request, current_user: dict, **kwargs) -> dict:
    all_prods = _list_products()
    visible = user_products(current_user, all_prods)
    return {
        "pending_count": len(_am.pending()),
        "all_products": visible,
        "current_user": current_user,
        "vapt_access": _vapt_access(current_user),
        "perf_access": _module_access("perf_enabled", current_user),
        "a11y_access": _module_access("a11y_enabled", current_user),
        "contract_access": _module_access("contract_enabled", current_user),
        "visual_access": _module_access("visual_enabled", current_user),
        "bugs_access": _module_access("bugs_enabled", current_user),
        "master_admin": current_user.get("master_admin", False),
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
    from dashboard.routers.agents import _PUBLIC_REGISTRY
    all_entries = _alog.all()
    visible = user_products(current_user, _list_products())
    if product and product not in visible:
        product = None
    visible_entries = [e for e in all_entries if e.get("product") in visible]
    scoped = [e for e in visible_entries if e.get("product") == product] if product else visible_entries
    pending = _am.pending()
    pending_ids = {p["id"] for p in pending}
    recent = [e for e in reversed(scoped) if e.get("agent") != "human"][:10]
    status_map: dict = {}
    for e in reversed(visible_entries):
        name = e.get("agent", "")
        if name and name not in status_map:
            status_map[name] = e
    agent_flow = [
        {
            "name": a["name"],
            "requires_ai": a["requires_ai"],
            "description": a["description"],
            "status": status_map[a["name"]]["status"] if a["name"] in status_map else "idle",
        }
        for a in _PUBLIC_REGISTRY
    ]
    return templates.TemplateResponse(request, "index.html", context=_ctx(
        request, current_user,
        total_activities=len(scoped),
        pending_approvals=len(pending),
        requires_human_count=len(pending),
        agent_count=len(_PUBLIC_REGISTRY),
        recent=recent,
        pending_ids=pending_ids,
        pending_items=pending[:3],
        queued_gaps=_queued_gaps(),
        agent_flow=agent_flow,
    ))


_PAGE_SIZE = 50

@router.get("/activities", response_class=HTMLResponse)
async def activities(
    request: Request,
    product: str | None = None,
    agent: str | None = None,
    domain: str | None = None,
    requires_human: str | None = None,
    page: int = 1,
    current_user: dict = Depends(_require_auth),
):
    visible = user_products(current_user, _list_products())
    if product and product not in visible:
        product = None
    rh: bool | None = None
    if requires_human == "true":
        rh = True
    elif requires_human == "false":
        rh = False
    all_filtered = list(reversed(_alog.filter(
        agent=agent or None,
        domain=domain or None,
        product=product or None,
        requires_human=rh,
    )))
    if not current_user.get("admin"):
        all_filtered = [e for e in all_filtered if e.get("product") in visible]
    agents = sorted(set(e.get("agent", "") for e in all_filtered if e.get("agent")))
    domains = sorted(set(e.get("domain", "") for e in all_filtered if e.get("domain")))
    products = sorted(set(e.get("product") or "" for e in all_filtered if e.get("product")))
    total = len(all_filtered)
    total_pages = max(1, (total + _PAGE_SIZE - 1) // _PAGE_SIZE)
    page = max(1, min(page, total_pages))
    return templates.TemplateResponse(request, "activities.html", context=_ctx(
        request, current_user,
        agents=agents,
        domains=domains,
        products=products,
        entries=all_filtered[(page - 1) * _PAGE_SIZE: page * _PAGE_SIZE],
        page=page,
        total_pages=total_pages,
        total=total,
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
    from dashboard.routers.docs import _find_docs, _parse_tc_index
    from utils.paths import ROOT as _froot
    visible = user_products(current_user, _list_products())
    if product and product not in visible:
        product = None
    all_docs = _find_docs()
    products = sorted(p for p in set(d["product"] for d in all_docs) if p in visible)
    domains = sorted(set(d["domain"] for d in all_docs))
    docs = [d for d in _find_docs() if d["product"] in visible]
    modules = []
    for d in docs:
        path = _froot / "products" / d["product"] / "docs" / "test_cases" / d["domain"] / f"{d['feature']}.md"
        tcs: list[dict] = []
        if path.exists():
            try:
                tcs = _parse_tc_index(path.read_text(encoding="utf-8"))
            except Exception:
                pass
        modules.append({**d, "test_cases": tcs})
    features = sorted(set(m["feature"] for m in modules if m["test_cases"]))
    test_types = sorted(set(
        tc["test_type"] for m in modules for tc in m["test_cases"] if tc.get("test_type")
    ))
    return templates.TemplateResponse(request, "docs.html", context=_ctx(
        request, current_user,
        modules=modules,
        products=products,
        domains=domains,
        features=features,
        test_types=test_types,
        filter_product=product or "",
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
    features = sorted(set(s["feature"] for s in scripts))
    test_types = sorted(set(tt for s in scripts for tt in s.get("test_types", [])))
    return templates.TemplateResponse(request, "scripts.html", context=_ctx(
        request, current_user, scripts=scripts, products=products, domains=domains,
        features=features, test_types=test_types,
    ))


@router.get("/assignments", response_class=HTMLResponse)
async def assignments_page(request: Request, current_user: dict = Depends(_require_auth)):
    from dashboard.routers.config_router import _all_tests, _load_assignments, _load_config
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
    import json
    import yaml

    from dashboard.agent_meta import AGENT_META
    from dashboard.routers.agents import _PUBLIC_REGISTRY as _AGENT_REGISTRY
    from utils.paths import ROOT as _ROOT

    config_path = _ROOT / "ai" / "context" / "agent_config.yaml"
    agent_config: dict = {}
    if config_path.exists():
        data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        agent_config = data.get("agents", {})

    # Determine whether AI and KB are configured
    chat_cfg_path = _ROOT / "dashboard" / "chat_config.json"
    has_ai = False
    if chat_cfg_path.exists():
        try:
            cc = json.loads(chat_cfg_path.read_text(encoding="utf-8"))
            provider = cc.get("provider", "")
            api_key = cc.get("api_key", "")
            # ollama and similar local providers don't need an API key
            has_ai = bool(provider and (api_key or provider == "ollama"))
        except Exception:
            pass

    has_kb = bool(list((_ROOT / "ai" / "knowledge_base").rglob("*.yaml")))
    from core.db import get_conn as _get_conn
    has_history = _get_conn().execute("SELECT COUNT(*) FROM run_history").fetchone()[0] > 0
    has_baseline = (_ROOT / "data" / "baseline_report.json").exists()

    # Agents that need KB
    _kb_agents = {"doc_gen", "script_gen", "coverage_gap"}

    def _health(agent: dict, last_run: dict | None) -> str:
        name = agent["name"]
        if agent.get("requires_ai") and not has_ai:
            return "needs_config"
        if name in _kb_agents and not has_kb:
            return "needs_config"
        if name == "flaky_detector" and not has_history:
            return "no_data"
        if name == "regression_guard" and not has_baseline:
            return "no_baseline"
        if last_run:
            return "degraded" if last_run.get("status") == "error" else "healthy"
        return "ready"

    status_map: dict = {}
    for e in reversed(_alog.all()):
        name = e.get("agent", "")
        if name and name not in status_map:
            status_map[name] = e

    agents_data = []
    for a in _AGENT_REGISTRY:
        last = status_map.get(a["name"])
        agents_data.append({
            **a,
            "last_run": last,
            "meta": AGENT_META.get(a["name"], {}),
            "config": agent_config.get(a["name"], {}),
            "health": _health(a, last),
        })

    health_counts = Counter(a["health"] for a in agents_data)
    return templates.TemplateResponse(request, "agents.html", context=_ctx(
        request, current_user, agents=agents_data, health_counts=health_counts,
    ))


@router.get("/quality", response_class=HTMLResponse)
async def quality_page(request: Request, product: str | None = None,
                       current_user: dict = Depends(_require_auth)):
    from dashboard.routers.partials import _quarantine_groups
    from dashboard.routers.quality import _all_test_functions, compute_metrics
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
    highlight: str | None = None,
    page: int = 1,
    current_user: dict = Depends(_require_auth),
):
    from core.run_manager import RunManager
    rm = RunManager()
    visible = user_products(current_user, _list_products())
    if product and product not in visible:
        product = None
    runs = [r for r in rm.all_runs() if r.get("product") in visible]
    if product:
        runs = [r for r in runs if r.get("product") == product]
    if domain:
        runs = [r for r in runs if r.get("domain") == domain]
    if status:
        runs = [r for r in runs if r.get("status") == status]
    # If a specific run is highlighted, jump to the page it lives on
    if highlight:
        ids = [r["id"] for r in runs]
        if highlight in ids:
            page = ids.index(highlight) // _PAGE_SIZE + 1
    schedules = [s for s in rm.all_schedules() if s.get("product") in visible]
    total = len(runs)
    total_pages = max(1, (total + _PAGE_SIZE - 1) // _PAGE_SIZE)
    page = max(1, min(page, total_pages))
    page_runs = runs[(page - 1) * _PAGE_SIZE: page * _PAGE_SIZE]
    any_running = any(r.get("status") in ("running", "queued") for r in page_runs)
    return templates.TemplateResponse(request, "runs.html", context=_ctx(
        request, current_user,
        runs=page_runs,
        schedules=schedules,
        any_running=any_running,
        filter_product=product or "",
        filter_domain=domain or "",
        filter_status=status or "",
        highlight=highlight or "",
        page=page,
        total_pages=total_pages,
        total=total,
    ))


@router.get("/failures", response_class=HTMLResponse)
async def failures_page(
    request: Request,
    run_id: str | None = None,
    domain: str | None = None,
    category: str | None = None,
    page: int = 1,
    current_user: dict = Depends(_require_auth),
):
    from core.run_manager import RunManager
    rm = RunManager()
    visible = user_products(current_user, _list_products())

    _cat_map = {
        "assertion": "Product Bug",
        "env":       "Env Issue",
        "infra":     "Env Issue",
        "locator":   "Script/Data",
        "flaky":     "Script/Data",
        "unanalyzed":"Unanalyzed",
        "unknown":   "Unanalyzed",
    }
    _cat_styles = {
        "Product Bug":  ("bg-red-50 text-red-700 border-red-200",    "bg-red-500"),
        "Env Issue":    ("bg-amber-50 text-amber-700 border-amber-200", "bg-amber-500"),
        "Script/Data":  ("bg-orange-50 text-orange-700 border-orange-200", "bg-orange-400"),
        "Unanalyzed":   ("bg-slate-50 text-slate-500 border-slate-200", "bg-slate-400"),
    }

    all_runs = [r for r in rm.all_runs() if r.get("product") in visible]
    all_failures = []
    for run in all_runs:
        if run.get("status") not in ("completed", "failed"):
            continue
        if run_id and run["id"] != run_id:
            continue
        if domain and run.get("domain") != domain:
            continue
        for f in run.get("failures", []):
            raw_cat = f.get("category") or f.get("classification", "unknown")
            mapped = _cat_map.get(raw_cat, "Unanalyzed")
            all_failures.append({
                **f,
                "mapped_category": mapped,
                "run_id":      run["id"],
                "product":     run["product"],
                "domain":      run["domain"],
                "module":      run.get("module", ""),
                "triggered_at": run["triggered_at"],
                "analyzed":    run.get("analyzed", False),
            })

    counts = Counter(f["mapped_category"] for f in all_failures)
    failures = [f for f in all_failures if not category or f["mapped_category"] == category]
    total_failures = len(failures)
    total_pages = max(1, (total_failures + _PAGE_SIZE - 1) // _PAGE_SIZE)
    page = max(1, min(page, total_pages))

    return templates.TemplateResponse(request, "failures.html", context=_ctx(
        request, current_user,
        failures=failures[(page - 1) * _PAGE_SIZE: page * _PAGE_SIZE],
        counts=counts,
        total_failures=total_failures,
        cat_styles=_cat_styles,
        filter_run_id=run_id or "",
        filter_domain=domain or "",
        filter_category=category or "",
        page=page,
        total_pages=total_pages,
    ))


@router.get("/kb", response_class=HTMLResponse)
async def kb_page(request: Request, product: str | None = None,
                  current_user: dict = Depends(_require_auth)):
    from dashboard.routers.kb import (
        _INCREMENTS_DIR,
        _TEXT_SUFFIXES,
        _kb_files,
        _list_products,
        _load_increments_log,
    )
    from dashboard.routers.pipeline import _load_jobs
    all_prods = _list_products()
    visible = user_products(current_user, all_prods)
    if product and product not in visible:
        product = None
    kb_files = {p: _kb_files(p) for p in visible}
    selected_product = product if product and product in visible else ""
    log = _load_increments_log()
    import yaml as _yaml
    increments: list[dict] = []
    if _INCREMENTS_DIR.exists():
        for f in sorted(_INCREMENTS_DIR.iterdir()):
            if f.suffix not in _TEXT_SUFFIXES or f.name == ".gitkeep":
                continue
            try:
                inc_product = str((_yaml.safe_load(f.read_text(encoding="utf-8")) or {}).get("product", "")).strip()
            except Exception:
                inc_product = ""
            if selected_product and inc_product != selected_product:
                continue
            increments.append({"filename": f.name, "processed": f.name in log, "log": log.get(f.name)})
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
async def admin_users_page(request: Request, audit_page: int = 1,
                           current_user: dict = Depends(_require_auth)):
    if not current_user.get("admin"):
        return RedirectResponse("/", status_code=302)
    from dashboard.routers.config_router import _load_config
    from core.audit_logger import recent as _audit_recent
    cfg = _load_config()
    all_events = _audit_recent(500)
    total_audit = len(all_events)
    audit_total_pages = max(1, (total_audit + _PAGE_SIZE - 1) // _PAGE_SIZE)
    audit_page = max(1, min(audit_page, audit_total_pages))
    return templates.TemplateResponse(request, "admin_users.html", context=_ctx(
        request, current_user,
        users=cfg.get("users", []),
        all_products=[p["name"] for p in cfg.get("products", []) if p.get("active", True)],
        audit_events=all_events[(audit_page - 1) * _PAGE_SIZE: audit_page * _PAGE_SIZE],
        audit_page=audit_page,
        audit_total_pages=audit_total_pages,
        total_audit=total_audit,
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


@router.get("/vapt", response_class=HTMLResponse)
async def vapt_page(request: Request, product: str | None = None,
                    current_user: dict = Depends(_require_auth)):
    if not _vapt_access(current_user):
        return RedirectResponse("/", status_code=302)
    from dashboard.routers.vapt import _vapt_products
    vapt_prods = _vapt_products(current_user)
    return templates.TemplateResponse(request, "vapt.html", context=_ctx(
        request, current_user,
        vapt_products=vapt_prods,
        vapt_access=True,
    ))


@router.get("/perf", response_class=HTMLResponse)
async def perf_page(request: Request, current_user: dict = Depends(_require_auth)):
    if not _module_access("perf_enabled", current_user):
        return RedirectResponse("/", status_code=302)
    from dashboard.routers.perf import _perf_products
    return templates.TemplateResponse(request, "perf.html", context=_ctx(
        request, current_user, perf_products=_perf_products(current_user),
    ))


@router.get("/a11y", response_class=HTMLResponse)
async def a11y_page(request: Request, current_user: dict = Depends(_require_auth)):
    if not _module_access("a11y_enabled", current_user):
        return RedirectResponse("/", status_code=302)
    from dashboard.routers.a11y import _a11y_products
    return templates.TemplateResponse(request, "a11y.html", context=_ctx(
        request, current_user, a11y_products=_a11y_products(current_user),
    ))


@router.get("/contract", response_class=HTMLResponse)
async def contract_page(request: Request, current_user: dict = Depends(_require_auth)):
    if not _module_access("contract_enabled", current_user):
        return RedirectResponse("/", status_code=302)
    from dashboard.routers.contract import _contract_products
    return templates.TemplateResponse(request, "contract.html", context=_ctx(
        request, current_user, contract_products=_contract_products(current_user),
    ))


@router.get("/visual", response_class=HTMLResponse)
async def visual_page(request: Request, current_user: dict = Depends(_require_auth)):
    if not _module_access("visual_enabled", current_user):
        return RedirectResponse("/", status_code=302)
    from dashboard.routers.visual import _visual_products
    return templates.TemplateResponse(request, "visual.html", context=_ctx(
        request, current_user, visual_products=_visual_products(current_user),
    ))


@router.get("/test-plans", response_class=HTMLResponse)
async def test_plans_page(request: Request, product: str | None = None,
                          current_user: dict = Depends(_require_auth)):
    visible = user_products(current_user, _list_products())
    if product and product not in visible:
        product = None
    return templates.TemplateResponse(request, "test_plans.html", context=_ctx(
        request, current_user,
        filter_product=product or "",
    ))


@router.get("/bugs", response_class=HTMLResponse)
async def bugs_page(request: Request, product: str | None = None,
                    current_user: dict = Depends(_require_auth)):
    if not _module_access("bugs_enabled", current_user):
        return RedirectResponse("/", status_code=302)
    visible = user_products(current_user, _list_products())
    if product and product not in visible:
        product = None
    from dashboard.routers.config._helpers import _load_config
    from core.bug_manager import _get_statuses
    import json as _json
    cfg = _load_config()
    users = cfg.get("users", [])
    priorities = cfg.get("priorities", [])
    bug_statuses = _get_statuses(product)
    return templates.TemplateResponse(request, "bugs.html", context=_ctx(
        request, current_user,
        filter_product=product or "",
        config_users=users,
        config_priorities=priorities,
        bug_statuses=bug_statuses,
        bug_statuses_json=_json.dumps(bug_statuses),
    ))


@router.get("/insights", response_class=HTMLResponse)
async def insights_page(request: Request, current_user: dict = Depends(_require_auth)):
    if not current_user.get("master_admin"):
        return RedirectResponse("/", status_code=302)
    return templates.TemplateResponse(request, "insights.html", context=_ctx(
        request, current_user,
    ))
