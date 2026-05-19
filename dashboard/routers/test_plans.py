"""Test plan CRUD, scope management, TC execution tracking, and run linking."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response
from pydantic import BaseModel

from core.bug_manager import BugManager
from core.run_manager import RunManager
from core.test_plan_manager import TestPlanManager
from dashboard.routers.auth import require_user, user_products
from utils.paths import ROOT as _ROOT

router = APIRouter(tags=["test-plans"])
_tpm = TestPlanManager()
_rm = RunManager()
_bm = BugManager()

_PRODUCTS_DIR = _ROOT / "products"


# ── helpers ───────────────────────────────────────────────────────────────────

def _visible_products(current_user: dict) -> list[str]:
    from dashboard.routers.kb import _list_products
    return user_products(current_user, _list_products())


def _check_product(product: str, current_user: dict) -> None:
    if product not in _visible_products(current_user):
        raise HTTPException(403, "Access denied to this product")


def _get_plan_or_404(plan_id: str) -> dict:
    plan = _tpm.get_plan(plan_id)
    if not plan:
        raise HTTPException(404, "Test plan not found")
    return plan


def _resolve_modules(product: str, domain: str) -> list[str]:
    """Return test file stems for a product+domain combo."""
    base = _PRODUCTS_DIR / product / "tests"
    if not base.exists():
        return []
    domain_dir = (base / domain) if (domain and domain != "all") else base
    if not domain_dir.exists():
        return []
    return sorted(p.stem for p in domain_dir.glob("test_*.py") if p.is_file())


def _tcs_for_module(product: str, domain: str, module: str) -> list[dict]:
    """Parse TC index from the doc corresponding to this test module."""
    from dashboard.routers.docs import _parse_tc_index

    feature = module.removeprefix("test_") if module.startswith("test_") else module
    doc_path = _PRODUCTS_DIR / product / "docs" / "test_cases" / domain / f"{feature}.md"
    if not doc_path.exists():
        return []
    content = doc_path.read_text(encoding="utf-8")
    raw = _parse_tc_index(content)
    return [
        {
            "tc_id": tc["id"],
            "tc_title": tc["title"],
            "automation_status": tc["status"],  # automated | not_automated | not_automatable
        }
        for tc in raw
        if tc.get("id")
    ]


def _sync_tc_statuses(plan_id: str, product: str, scope_items: list[dict]) -> None:
    """Populate/sync test_plan_tc_status from scope + docs."""
    all_tc_ids: list[str] = []
    for item in scope_items:
        domain = item["domain"]
        module = item["module"]
        excluded = set(item.get("excluded_tc_ids") or [])
        tcs = _tcs_for_module(product, domain, module)
        in_scope_tcs = [
            {"tc_id": tc["tc_id"], "tc_title": tc["tc_title"],
             "domain": domain, "module": module,
             "automation_status": tc["automation_status"]}
            for tc in tcs
            if tc["tc_id"] not in excluded
        ]
        if in_scope_tcs:
            _tpm.upsert_tc_statuses(plan_id, in_scope_tcs)
            all_tc_ids.extend(t["tc_id"] for t in in_scope_tcs)
    _tpm.remove_tc_statuses_not_in_scope(plan_id, all_tc_ids)


# ── request models ────────────────────────────────────────────────────────────

class CreatePlanBody(BaseModel):
    name: str
    product: str
    owner: str = ""
    description: str = ""
    schedule_start: str | None = None
    schedule_end: str | None = None
    milestones: list[dict] = []
    risks: list[dict] = []
    exit_criteria: str = ""
    pass_criteria: str = ""


class PatchPlanBody(BaseModel):
    name: str | None = None
    owner: str | None = None
    description: str | None = None
    status: str | None = None
    schedule_start: str | None = None
    schedule_end: str | None = None
    milestones: list[dict] | None = None
    risks: list[dict] | None = None
    exit_criteria: str | None = None
    pass_criteria: str | None = None


class ScopeItem(BaseModel):
    domain: str
    module: str
    excluded_tc_ids: list[str] = []


class SetScopeBody(BaseModel):
    items: list[ScopeItem]


class PatchTCStatusBody(BaseModel):
    exec_status: str
    notes: str = ""


# ── plan CRUD ─────────────────────────────────────────────────────────────────

@router.get("/")
def list_plans(
    product: str | None = None,
    status: str | None = None,
    current_user: dict = Depends(require_user),
):
    visible = _visible_products(current_user)
    plans = _tpm.list_plans(product=product, status=status)
    plans = [p for p in plans if p["product"] in visible]
    for p in plans:
        p["progress"] = _tpm.get_progress(p["id"])
    return {"plans": plans, "total": len(plans)}


@router.post("/")
def create_plan(body: CreatePlanBody, current_user: dict = Depends(require_user)):
    _check_product(body.product, current_user)
    plan = _tpm.create_plan(
        name=body.name,
        product=body.product,
        owner=body.owner or current_user.get("name", ""),
        description=body.description,
        schedule_start=body.schedule_start,
        schedule_end=body.schedule_end,
        milestones=body.milestones,
        risks=body.risks,
        exit_criteria=body.exit_criteria,
        pass_criteria=body.pass_criteria,
    )
    return plan


@router.get("/{plan_id}")
def get_plan(plan_id: str, current_user: dict = Depends(require_user)):
    plan = _get_plan_or_404(plan_id)
    _check_product(plan["product"], current_user)
    plan["progress"] = _tpm.get_progress(plan_id)
    return plan


@router.patch("/{plan_id}")
def patch_plan(plan_id: str, body: PatchPlanBody, current_user: dict = Depends(require_user)):
    plan = _get_plan_or_404(plan_id)
    _check_product(plan["product"], current_user)
    updates: dict[str, Any] = {k: v for k, v in body.model_dump().items() if v is not None}
    updated = _tpm.patch_plan(plan_id, **updates)
    return updated


@router.delete("/{plan_id}")
def delete_plan(plan_id: str, current_user: dict = Depends(require_user)):
    plan = _get_plan_or_404(plan_id)
    _check_product(plan["product"], current_user)
    _tpm.delete_plan(plan_id)
    return {"deleted": plan_id}


# ── scope ─────────────────────────────────────────────────────────────────────

@router.get("/{plan_id}/scope")
def get_scope(plan_id: str, current_user: dict = Depends(require_user)):
    plan = _get_plan_or_404(plan_id)
    _check_product(plan["product"], current_user)
    return {"scope": _tpm.get_scope(plan_id)}


@router.put("/{plan_id}/scope")
def set_scope(plan_id: str, body: SetScopeBody, current_user: dict = Depends(require_user)):
    plan = _get_plan_or_404(plan_id)
    _check_product(plan["product"], current_user)
    items = [item.model_dump() for item in body.items]
    _tpm.set_scope(plan_id, items)
    _sync_tc_statuses(plan_id, plan["product"], items)
    return {"scope": _tpm.get_scope(plan_id)}


@router.get("/{plan_id}/scope/available-modules")
def available_modules(
    plan_id: str,
    domain: str = "all",
    current_user: dict = Depends(require_user),
):
    plan = _get_plan_or_404(plan_id)
    _check_product(plan["product"], current_user)
    modules = _resolve_modules(plan["product"], domain)
    return {"modules": modules, "domain": domain}


@router.get("/{plan_id}/scope/module-tcs")
def module_tcs(
    plan_id: str,
    domain: str,
    module: str,
    current_user: dict = Depends(require_user),
):
    """Return TC list for a specific module (for scope exclusion UI)."""
    plan = _get_plan_or_404(plan_id)
    _check_product(plan["product"], current_user)
    tcs = _tcs_for_module(plan["product"], domain, module)
    return {"tcs": tcs, "total": len(tcs)}


# ── TC execution status ────────────────────────────────────────────────────────

@router.get("/{plan_id}/tc-status")
def get_tc_statuses(
    plan_id: str,
    domain: str | None = None,
    module: str | None = None,
    current_user: dict = Depends(require_user),
):
    plan = _get_plan_or_404(plan_id)
    _check_product(plan["product"], current_user)
    statuses = _tpm.get_tc_statuses(plan_id, domain=domain, module=module)
    return {"tc_statuses": statuses, "total": len(statuses)}


@router.patch("/{plan_id}/tc-status/{tc_id}")
def update_tc_status(
    plan_id: str,
    tc_id: str,
    body: PatchTCStatusBody,
    current_user: dict = Depends(require_user),
):
    plan = _get_plan_or_404(plan_id)
    _check_product(plan["product"], current_user)
    ok = _tpm.update_tc_status(
        plan_id, tc_id,
        exec_status=body.exec_status,
        notes=body.notes,
        updated_by=current_user.get("name", ""),
    )
    if not ok:
        raise HTTPException(404, "TC not found in this plan's scope")
    return _tpm.get_tc_statuses(plan_id)


# ── execution ─────────────────────────────────────────────────────────────────

@router.post("/{plan_id}/execute")
def execute_plan(
    plan_id: str,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(require_user),
):
    """Trigger automated runs for all in-scope modules that have automated TCs."""
    from dashboard.routers.runs import _execute_run, _build_run_config_snapshot

    plan = _get_plan_or_404(plan_id)
    _check_product(plan["product"], current_user)
    product = plan["product"]

    scope = _tpm.get_scope(plan_id)
    if not scope:
        raise HTTPException(400, "No scope defined — add modules to scope first")

    run_ids: list[str] = []
    for item in scope:
        domain = item["domain"]
        module = item["module"]
        snapshot = _build_run_config_snapshot(product, "", "", "")
        run = _rm.create_run(
            product=product,
            domain=domain,
            module=module,
            trigger="plan",
            run_config_snapshot=snapshot,
        )
        _tpm.link_run(plan_id, run["id"])
        background_tasks.add_task(
            _execute_run, run["id"], product, domain, module, "", "", "", ""
        )
        run_ids.append(run["id"])

    return {"triggered": len(run_ids), "run_ids": run_ids}


# ── progress and linked runs ───────────────────────────────────────────────────

@router.get("/{plan_id}/progress")
def get_progress(plan_id: str, current_user: dict = Depends(require_user)):
    plan = _get_plan_or_404(plan_id)
    _check_product(plan["product"], current_user)
    return _tpm.get_progress(plan_id)


@router.get("/{plan_id}/runs")
def get_linked_runs(plan_id: str, current_user: dict = Depends(require_user)):
    plan = _get_plan_or_404(plan_id)
    _check_product(plan["product"], current_user)
    run_ids = _tpm.get_linked_run_ids(plan_id)
    runs = [_rm.get_run(rid) for rid in run_ids]
    ordered = sorted(
        (r for r in runs if r),
        key=lambda r: r.get("triggered_at") or "",
        reverse=True,
    )
    return {"runs": ordered, "total": len(run_ids)}


# ── report ────────────────────────────────────────────────────────────────────

def _to_pdf(html: str) -> bytes | None:
    try:
        from weasyprint import HTML
        return HTML(string=html).write_pdf()
    except Exception:
        return None


def _render_plan_report_html(plan_id: str) -> str:
    from jinja2 import Environment, FileSystemLoader
    plan = _tpm.get_plan(plan_id)
    scope = _tpm.get_scope(plan_id)
    tc_statuses = _tpm.get_tc_statuses(plan_id)
    progress = _tpm.get_progress(plan_id)
    run_ids = _tpm.get_linked_run_ids(plan_id)
    runs = sorted(
        (r for r in (_rm.get_run(rid) for rid in run_ids) if r),
        key=lambda r: r.get("triggered_at") or "",
        reverse=True,
    )
    # group TCs by domain for template rendering
    domains_seen: list[str] = []
    tcs_by_domain: dict[str, list[dict]] = {}
    for tc in tc_statuses:
        d = tc["domain"]
        if d not in tcs_by_domain:
            domains_seen.append(d)
            tcs_by_domain[d] = []
        tcs_by_domain[d].append(tc)

    closed_states = _bm.closed_state_names(plan["product"])
    open_bugs = [
        b for b in _bm.list_bugs(linked_plan_id=plan_id)
        if b.get("state") not in closed_states
    ]

    env = Environment(autoescape=True,
                      loader=FileSystemLoader(str(_ROOT / "dashboard" / "templates")))
    tpl = env.get_template("test_plan_report_pdf.html")
    return tpl.render(
        plan=plan,
        scope=scope,
        progress=progress,
        domains=domains_seen,
        tcs_by_domain=tcs_by_domain,
        runs=runs,
        open_bugs=open_bugs,
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    )


@router.get("/{plan_id}/report")
def plan_report(plan_id: str, format: str = "pdf",
                current_user: dict = Depends(require_user)):
    plan = _get_plan_or_404(plan_id)
    _check_product(plan["product"], current_user)
    html = _render_plan_report_html(plan_id)
    if format == "pdf":
        pdf = _to_pdf(html)
        if pdf is None:
            raise HTTPException(500, detail="WeasyPrint not available")
        filename = f"test_plan_{plan['product']}_{plan_id}.pdf"
        return Response(pdf, media_type="application/pdf",
                        headers={"Content-Disposition": f'attachment; filename="{filename}"'})
    return Response(html, media_type="text/html")
