from __future__ import annotations

from pathlib import Path
from typing import List, Optional

import yaml
from fastapi import APIRouter, Form, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["config"])
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))

_FK_DIR = Path(__file__).resolve().parent.parent.parent / "framework_knowledge"
_CONFIG_PATH = _FK_DIR / "config.yaml"
_ASSIGNMENTS_PATH = _FK_DIR / "test_assignments.yaml"
_EXAMPLES_DIR = _FK_DIR.parent / "examples"


# ---------- data helpers ----------

def _load_config() -> dict:
    if _CONFIG_PATH.exists():
        return yaml.safe_load(_CONFIG_PATH.read_text(encoding="utf-8")) or {}
    return {"labels": [], "priorities": [], "custom_fields": [], "test_type_distribution": {"sanity": 30, "regression": 70}}


def _save_config(cfg: dict) -> None:
    _CONFIG_PATH.write_text(yaml.dump(cfg, default_flow_style=False, allow_unicode=True), encoding="utf-8")


def _load_assignments() -> dict:
    if _ASSIGNMENTS_PATH.exists():
        data = yaml.safe_load(_ASSIGNMENTS_PATH.read_text(encoding="utf-8")) or {}
        return data.get("assignments", {})
    return {}


def _save_assignments(assignments: dict) -> None:
    _ASSIGNMENTS_PATH.write_text(
        "# Maps test function name -> label/priority/custom field assignments\n"
        "# Managed via dashboard Config > Test Assignments\n"
        + yaml.dump({"assignments": assignments}, default_flow_style=False, allow_unicode=True),
        encoding="utf-8",
    )


def _all_tests() -> list[dict]:
    import re
    results = []
    for py in _EXAMPLES_DIR.rglob("test_*.py"):
        parts = py.relative_to(_EXAMPLES_DIR).parts
        if len(parts) < 4 or parts[1] != "tests":
            continue
        p, d = parts[0], parts[2]
        try:
            for fn in re.findall(r"^def (test_\w+)", py.read_text(encoding="utf-8"), re.MULTILINE):
                results.append({"name": fn, "product": p, "domain": d})
        except OSError:
            pass
    return sorted(results, key=lambda x: (x["product"], x["domain"], x["name"]))


def assignments_summary_by_feature() -> dict:
    """Return {product/domain/feature: {labels, priorities, assigned, total}} for dashboard overlays."""
    import re
    assignments = _load_assignments()
    cfg = _load_config()
    label_colors = {l["name"]: l["color"] for l in cfg.get("labels", [])}
    priority_colors = {p["name"]: p["color"] for p in cfg.get("priorities", [])}
    result = {}
    for py in _EXAMPLES_DIR.rglob("test_*.py"):
        parts = py.relative_to(_EXAMPLES_DIR).parts
        if len(parts) < 4 or parts[1] != "tests":
            continue
        product, domain = parts[0], parts[2]
        feature = py.stem[5:]  # strip "test_" prefix
        try:
            fns = re.findall(r"^def (test_\w+)", py.read_text(encoding="utf-8"), re.MULTILINE)
        except OSError:
            continue
        labels: dict[str, str] = {}
        priorities: dict[str, str] = {}
        assigned = 0
        for fn in fns:
            asgn = assignments.get(fn, {})
            if asgn:
                assigned += 1
                for lbl in asgn.get("labels", []):
                    labels[lbl] = label_colors.get(lbl, "slate")
                if asgn.get("priority"):
                    p = asgn["priority"]
                    priorities[p] = priority_colors.get(p, "slate")
        result[f"{product}/{domain}/{feature}"] = {
            "labels": [{"name": k, "color": v} for k, v in labels.items()],
            "priorities": [{"name": k, "color": v} for k, v in priorities.items()],
            "assigned": assigned,
            "total": len(fns),
        }
    return result


def get_test_type_for_index(index: int, total: int, cfg: dict | None = None) -> str:
    """Assign sanity/regression by position in an importance-ordered list.

    Callers MUST sort tests by importance before calling (critical happy-paths first,
    edge cases last). The first `sanity_pct`% of that ordered list becomes sanity;
    the rest become regression.
    """
    if cfg is None:
        cfg = _load_config()
    dist = cfg.get("test_type_distribution", {})
    sanity_pct = dist.get("sanity", 30)
    sanity_count = max(1, round(total * sanity_pct / 100))
    return "sanity" if index < sanity_count else "regression"


def get_generation_type_instruction(cfg: dict | None = None) -> str:
    """Return the prompt rule block for script gen re: sanity/regression markers.

    The AI assigns markers based on business importance, not sequential position.
    The percentage is a target distribution, not a strict slice.
    """
    if cfg is None:
        cfg = _load_config()
    dist = cfg.get("test_type_distribution", {})
    sanity_pct = dist.get("sanity", 30)
    regression_pct = dist.get("regression", 70)
    return (
        f"- Test type markers: add @pytest.mark.sanity OR @pytest.mark.regression to every test function (in addition to the domain marker). "
        f"Judge by business importance: mark core happy-paths and business-critical flows as @pytest.mark.sanity (~{sanity_pct}% of tests). "
        f"Mark edge cases, error paths, and boundary checks as @pytest.mark.regression (~{regression_pct}% of tests). "
        f"Importance — not sequential position — determines the label. "
        f"Every generated test must have exactly one of these two markers."
    )


# ---------- page route ----------

def _config_page_ctx(request: Request, cfg: dict, product: str = "") -> dict:
    from dashboard.routers.kb import _list_products
    return {
        "request": request,
        "pending_count": 0,
        "all_products": _list_products(),
        "cfg": cfg,
        "filter_product": product,
    }


@router.get("/config", response_class=HTMLResponse)
async def config_page(request: Request, product: Optional[str] = None):
    cfg = _load_config()
    assignments = _load_assignments()
    tests = _all_tests()
    from dashboard.routers.kb import _list_products
    from utils.approval_manager import ApprovalManager
    _am = ApprovalManager()
    return templates.TemplateResponse(request, "config.html", context={
        "pending_count": len(_am.pending()),
        "all_products": _list_products(),
        "cfg": cfg,
        "labels": cfg.get("labels", []),
        "priorities": cfg.get("priorities", []),
        "custom_fields": cfg.get("custom_fields", []),
        "filter_product": product or "",
        "tests": tests,
        "assignments": assignments,
        "search": "",
    })


# ---------- label partials ----------

def _render_labels(request: Request, cfg: dict) -> HTMLResponse:
    return templates.TemplateResponse(request, "partials/config_labels.html", context={
        "request": request,
        "labels": cfg.get("labels", []),
    })


@router.post("/ui/config/labels/add", response_class=HTMLResponse)
async def labels_add(request: Request, name: str = Form(...), color: str = Form("slate")):
    cfg = _load_config()
    name = name.strip().lower().replace(" ", "_")
    if name and not any(l["name"] == name for l in cfg.get("labels", [])):
        cfg.setdefault("labels", []).append({"name": name, "color": color})
        _save_config(cfg)
    return _render_labels(request, cfg)


@router.post("/ui/config/labels/delete", response_class=HTMLResponse)
async def labels_delete(request: Request, name: str = Form(...)):
    cfg = _load_config()
    cfg["labels"] = [l for l in cfg.get("labels", []) if l["name"] != name]
    _save_config(cfg)
    return _render_labels(request, cfg)


# ---------- priority partials ----------

def _render_priorities(request: Request, cfg: dict) -> HTMLResponse:
    return templates.TemplateResponse(request, "partials/config_priorities.html", context={
        "request": request,
        "priorities": cfg.get("priorities", []),
    })


@router.post("/ui/config/priorities/add", response_class=HTMLResponse)
async def priorities_add(request: Request, name: str = Form(...), color: str = Form("slate")):
    cfg = _load_config()
    name = name.strip().upper().replace(" ", "")
    if name and not any(p["name"] == name for p in cfg.get("priorities", [])):
        cfg.setdefault("priorities", []).append({"name": name, "color": color})
        _save_config(cfg)
    return _render_priorities(request, cfg)


@router.post("/ui/config/priorities/delete", response_class=HTMLResponse)
async def priorities_delete(request: Request, name: str = Form(...)):
    cfg = _load_config()
    cfg["priorities"] = [p for p in cfg.get("priorities", []) if p["name"] != name]
    _save_config(cfg)
    return _render_priorities(request, cfg)


# ---------- custom field partials ----------

def _render_fields(request: Request, cfg: dict) -> HTMLResponse:
    return templates.TemplateResponse(request, "partials/config_fields.html", context={
        "request": request,
        "custom_fields": cfg.get("custom_fields", []),
    })


@router.post("/ui/config/fields/add", response_class=HTMLResponse)
async def fields_add(request: Request, name: str = Form(...), field_type: str = Form("text")):
    cfg = _load_config()
    name = name.strip().lower().replace(" ", "_")
    if name and not any(f["name"] == name for f in cfg.get("custom_fields", [])):
        cfg.setdefault("custom_fields", []).append({"name": name, "type": field_type})
        _save_config(cfg)
    return _render_fields(request, cfg)


@router.post("/ui/config/fields/delete", response_class=HTMLResponse)
async def fields_delete(request: Request, name: str = Form(...)):
    cfg = _load_config()
    cfg["custom_fields"] = [f for f in cfg.get("custom_fields", []) if f["name"] != name]
    _save_config(cfg)
    return _render_fields(request, cfg)


# ---------- test type distribution ----------

@router.post("/ui/config/test-types/save", response_class=HTMLResponse)
async def test_types_save(request: Request, sanity: int = Form(...)):
    sanity = max(0, min(100, sanity))
    regression = 100 - sanity
    cfg = _load_config()
    cfg["test_type_distribution"] = {"sanity": sanity, "regression": regression}
    _save_config(cfg)
    return templates.TemplateResponse(request, "partials/config_test_types.html", context={
        "request": request,
        "dist": cfg["test_type_distribution"],
        "saved": True,
    })


# ---------- test assignments ----------

def _apply_assignment_filters(
    tests: list,
    assignments: dict,
    search: str = "",
    filter_labels: list = None,
    filter_priority: str = "",
    filter_owner: str = "",
    filter_jira_exists: str = "",
) -> list:
    if search:
        tests = [t for t in tests if search.lower() in t["name"].lower()]
    if filter_labels:
        tests = [t for t in tests if any(
            lbl in assignments.get(t["name"], {}).get("labels", []) for lbl in filter_labels
        )]
    if filter_priority:
        tests = [t for t in tests if assignments.get(t["name"], {}).get("priority") == filter_priority]
    if filter_owner:
        tests = [t for t in tests if filter_owner.lower() in
                 assignments.get(t["name"], {}).get("custom_fields", {}).get("owner", "").lower()]
    if filter_jira_exists == "1":
        tests = [t for t in tests if assignments.get(t["name"], {}).get("custom_fields", {}).get("jira_ticket", "")]
    return tests


def _assignments_ctx(request, tests, assignments, cfg, product, search,
                     filter_labels, filter_priority, filter_owner, filter_jira_exists,
                     saved_test=""):
    return templates.TemplateResponse(request, "partials/config_assignments.html", context={
        "request": request,
        "tests": tests,
        "assignments": assignments,
        "labels": cfg.get("labels", []),
        "priorities": cfg.get("priorities", []),
        "custom_fields": cfg.get("custom_fields", []),
        "filter_product": product,
        "search": search,
        "filter_labels": filter_labels or [],
        "filter_priority": filter_priority,
        "filter_owner": filter_owner,
        "filter_jira_exists": filter_jira_exists,
        "saved_test": saved_test,
    })


@router.get("/ui/config/assignments", response_class=HTMLResponse)
async def assignments_partial(
    request: Request,
    product: str = "",
    search: str = "",
    filter_labels: List[str] = Query(default=[]),
    filter_priority: str = "",
    filter_owner: str = "",
    filter_jira_exists: str = "",
):
    assignments = _load_assignments()
    cfg = _load_config()
    tests = _all_tests()
    if product:
        tests = [t for t in tests if t["product"] == product]
    tests = _apply_assignment_filters(tests, assignments, search, filter_labels,
                                      filter_priority, filter_owner, filter_jira_exists)
    return _assignments_ctx(request, tests, assignments, cfg, product, search,
                            filter_labels, filter_priority, filter_owner, filter_jira_exists)


@router.post("/ui/config/assignments/save", response_class=HTMLResponse)
async def assignments_save(request: Request):
    form = await request.form()
    test_name = form.get("test_name", "")
    labels = form.getlist("labels")
    priority = form.get("priority", "")
    product = form.get("filter_product", "")
    search = form.get("search", "")
    filter_labels = form.getlist("filter_labels")
    filter_priority = form.get("filter_priority", "")
    filter_owner = form.get("filter_owner", "")
    filter_jira_exists = form.get("filter_jira_exists", "")

    cfg = _load_config()
    custom_fields = {f["name"]: form.get(f"cf_{f['name']}", "") for f in cfg.get("custom_fields", [])}

    assignments = _load_assignments()
    assignments[test_name] = {"labels": labels, "priority": priority, "custom_fields": custom_fields}
    _save_assignments(assignments)

    tests = _all_tests()
    if product:
        tests = [t for t in tests if t["product"] == product]
    tests = _apply_assignment_filters(tests, assignments, search, filter_labels,
                                      filter_priority, filter_owner, filter_jira_exists)
    return _assignments_ctx(request, tests, assignments, cfg, product, search,
                            filter_labels, filter_priority, filter_owner, filter_jira_exists,
                            saved_test=test_name)
