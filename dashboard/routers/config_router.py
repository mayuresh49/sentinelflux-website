from __future__ import annotations

from pathlib import Path
from typing import List, Optional

import yaml
from fastapi import APIRouter, Depends, File, Form, Query, Request, UploadFile
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates
from dashboard.routers.auth import require_user, user_products

router = APIRouter(tags=["config"], dependencies=[Depends(require_user)])
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))

_FK_DIR = Path(__file__).resolve().parent.parent.parent / "framework_knowledge"
_CONFIG_PATH = _FK_DIR / "config.yaml"
_ASSIGNMENTS_PATH = _FK_DIR / "test_assignments.yaml"
_EXAMPLES_DIR = _FK_DIR.parent / "examples"
_KB_PRODUCTS_DIR = _FK_DIR.parent / "ai" / "knowledge_base"
_SAFE_PRODUCT_RE = __import__("re").compile(r"^[a-zA-Z0-9_\-]+$")


# ---------- data helpers ----------

_DEFAULT_GENERATION_CATEGORIES = {
    "functional": True,
    "negative": True,
    "edge": True,
    "security": True,
    "accessibility": False,
}


def _load_config() -> dict:
    if _CONFIG_PATH.exists():
        cfg = yaml.safe_load(_CONFIG_PATH.read_text(encoding="utf-8")) or {}
        cats = cfg.setdefault("generation_categories", {})
        for k, v in _DEFAULT_GENERATION_CATEGORIES.items():
            cats.setdefault(k, v)
        cfg.setdefault("users", [])
        for u in cfg["users"]:
            u.setdefault("products", [])
            u.setdefault("admin", False)
            u.setdefault("password_hash", "")
        _backfill_products(cfg)
        return cfg
    cfg = {
        "labels": [],
        "priorities": [],
        "custom_fields": [],
        "test_type_distribution": {"sanity": 30, "regression": 70},
        "generation_categories": dict(_DEFAULT_GENERATION_CATEGORIES),
        "users": [],
        "products": [],
    }
    _backfill_products(cfg)
    return cfg


def _backfill_products(cfg: dict) -> None:
    cfg.setdefault("products", [])
    if not _KB_PRODUCTS_DIR.exists():
        return
    known = {p["name"] for p in cfg["products"]}
    skip = {"__pycache__", "increments"}
    for d in sorted(_KB_PRODUCTS_DIR.iterdir()):
        if d.is_dir() and d.name not in skip and d.name not in known:
            cfg["products"].append({
                "name": d.name,
                "display_name": d.name.replace("_", " ").title(),
                "active": True,
            })


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


def get_generation_categories_instruction(cfg: dict | None = None) -> str:
    """Return a prompt rule that tells the AI which test categories to generate."""
    if cfg is None:
        cfg = _load_config()
    cats = cfg.get("generation_categories", _DEFAULT_GENERATION_CATEGORIES)

    _LABELS = {
        "functional": "positive / happy-path functional tests",
        "negative": "negative tests (invalid input, missing fields, error paths)",
        "edge": "edge cases (boundary values, optional fields, limits)",
        "security": "security tests (auth, access control, injection, sensitive data)",
        "accessibility": "accessibility tests (ARIA, keyboard navigation, screen-reader compatibility)",
    }

    enabled = [_LABELS[k] for k in _LABELS if cats.get(k, False)]
    disabled = [_LABELS[k] for k in _LABELS if not cats.get(k, False)]

    lines = ["- Test categories to generate (STRICTLY follow this — do not add categories not listed here):"]
    lines.append(f"  INCLUDE: {', '.join(enabled) if enabled else 'none'}")
    if disabled:
        lines.append(f"  EXCLUDE (do not generate): {', '.join(disabled)}")
    return "\n".join(lines)


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
    return {
        "request": request,
        "pending_count": 0,
        "all_products": [p["name"] for p in cfg.get("products", []) if p.get("active", True)],
        "cfg": cfg,
        "filter_product": product,
    }


@router.get("/config", response_class=HTMLResponse)
async def config_page(request: Request, product: Optional[str] = None,
                      current_user: dict = Depends(require_user)):
    cfg = _load_config()
    assignments = _load_assignments()
    tests = _all_tests()
    from utils.approval_manager import ApprovalManager
    _am = ApprovalManager()
    all_prods = [p["name"] for p in cfg.get("products", []) if p.get("active", True)]
    visible_products = user_products(current_user, all_prods)
    enriched_products = []
    for _p in cfg.get("products", []):
        _tc = _product_test_count(_p["name"])
        enriched_products.append({**_p, "has_tests": _tc > 0, "test_count": _tc})
    return templates.TemplateResponse(request, "config.html", context={
        "pending_count": len(_am.pending()),
        "all_products": visible_products,
        "current_user": current_user,
        "products": enriched_products,
        "cfg": cfg,
        "labels": cfg.get("labels", []),
        "priorities": cfg.get("priorities", []),
        "custom_fields": cfg.get("custom_fields", []),
        "users": cfg.get("users", []),
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


# ---------- users ----------

def _render_users(request: Request, cfg: dict) -> HTMLResponse:
    return templates.TemplateResponse(request, "partials/config_users.html", context={
        "request": request,
        "users": cfg.get("users", []),
        "all_products": [p["name"] for p in cfg.get("products", []) if p.get("active", True)],
    })


@router.post("/ui/config/users/add", response_class=HTMLResponse)
async def users_add(request: Request, name: str = Form(...), email: str = Form("")):
    cfg = _load_config()
    name = name.strip()
    email = email.strip().lower()
    if name and not any(u["name"] == name for u in cfg.get("users", [])):
        cfg.setdefault("users", []).append({
            "name": name, "email": email,
            "products": [], "admin": False, "password_hash": "",
        })
        _save_config(cfg)
    return _render_users(request, cfg)


@router.post("/ui/config/users/delete", response_class=HTMLResponse)
async def users_delete(request: Request, name: str = Form(...)):
    cfg = _load_config()
    cfg["users"] = [u for u in cfg.get("users", []) if u["name"] != name]
    _save_config(cfg)
    return _render_users(request, cfg)


@router.post("/ui/config/users/set-password", response_class=HTMLResponse)
async def users_set_password(request: Request, name: str = Form(...), password: str = Form(...)):
    import bcrypt as _bcrypt
    cfg = _load_config()
    for u in cfg.get("users", []):
        if u["name"] == name:
            u["password_hash"] = _bcrypt.hashpw(password.strip().encode(), _bcrypt.gensalt()).decode() if password.strip() else ""
            break
    _save_config(cfg)
    return _render_users(request, cfg)


@router.post("/ui/config/users/set-admin", response_class=HTMLResponse)
async def users_set_admin(request: Request, name: str = Form(...), admin: str = Form(default="")):
    cfg = _load_config()
    for u in cfg.get("users", []):
        if u["name"] == name:
            u["admin"] = admin == "on"
            break
    _save_config(cfg)
    return _render_users(request, cfg)


@router.post("/ui/config/users/set-products", response_class=HTMLResponse)
async def users_set_products(request: Request):
    form = await request.form()
    name = form.get("name", "")
    products = form.getlist("products")
    cfg = _load_config()
    for u in cfg.get("users", []):
        if u["name"] == name:
            u["products"] = products
            break
    _save_config(cfg)
    return _render_users(request, cfg)


# ---------- products ----------

def _product_test_count(product: str) -> int:
    import re as _re
    tests_dir = _EXAMPLES_DIR / product / "tests"
    if not tests_dir.exists():
        return 0
    count = 0
    for py in tests_dir.rglob("test_*.py"):
        try:
            count += len(_re.findall(r"^def (test_\w+)", py.read_text(encoding="utf-8"), _re.MULTILINE))
        except OSError:
            pass
    return count


def _render_products(request: Request, cfg: dict, flash: str = "") -> HTMLResponse:
    enriched = []
    for p in cfg.get("products", []):
        tc = _product_test_count(p["name"])
        enriched.append({**p, "has_tests": tc > 0, "test_count": tc})
    return templates.TemplateResponse(request, "partials/config_products.html", context={
        "request": request,
        "products": enriched,
        "flash": flash,
    })


@router.post("/ui/config/products/add", response_class=HTMLResponse)
async def products_add(request: Request, name: str = Form(...), display_name: str = Form("")):
    name = name.strip().lower().replace(" ", "_")
    cfg = _load_config()
    if name and _SAFE_PRODUCT_RE.match(name) and not any(p["name"] == name for p in cfg.get("products", [])):
        cfg.setdefault("products", []).append({
            "name": name,
            "display_name": display_name.strip() or name.replace("_", " ").title(),
            "active": True,
        })
        _save_config(cfg)
        (_KB_PRODUCTS_DIR / name).mkdir(parents=True, exist_ok=True)
        (_EXAMPLES_DIR / name / "tests").mkdir(parents=True, exist_ok=True)
        (_EXAMPLES_DIR / name / "pages").mkdir(parents=True, exist_ok=True)
    return _render_products(request, cfg)


def _purge_product_data(name: str, cfg: dict) -> None:
    """Remove all data associated with a product across every data store."""
    import shutil, json, re as _re

    # 1. Test assignments — remove entries for tests that belong to this product
    if _ASSIGNMENTS_PATH.exists():
        raw = yaml.safe_load(_ASSIGNMENTS_PATH.read_text(encoding="utf-8")) or {}
        assignments = raw.get("assignments", {})
        tests_dir = _EXAMPLES_DIR / name / "tests"
        product_fns: set[str] = set()
        if tests_dir.exists():
            for py in tests_dir.rglob("test_*.py"):
                try:
                    product_fns.update(_re.findall(r"^def (test_\w+)", py.read_text(encoding="utf-8"), _re.MULTILINE))
                except OSError:
                    pass
        pruned = {k: v for k, v in assignments.items() if k not in product_fns}
        if pruned != assignments:
            _ASSIGNMENTS_PATH.write_text(
                "# Maps test function name -> label/priority/custom field assignments\n"
                "# Managed via dashboard Config > Test Assignments\n"
                + yaml.dump({"assignments": pruned}, default_flow_style=False, allow_unicode=True),
                encoding="utf-8",
            )

    # 2. Pipeline jobs — drop jobs for this product
    jobs_path = _FK_DIR / "pipeline_jobs.json"
    if jobs_path.exists():
        data = json.loads(jobs_path.read_text(encoding="utf-8"))
        data["jobs"] = [j for j in data.get("jobs", []) if j.get("product") != name]
        jobs_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    # 3. Activity log — drop entries for this product
    alog_path = _FK_DIR / "activity_log.json"
    if alog_path.exists():
        data = json.loads(alog_path.read_text(encoding="utf-8"))
        data["entries"] = [e for e in data.get("entries", []) if e.get("product") != name]
        alog_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    # 4. KB increments log — drop entries whose paths are under examples/<name>/
    kb_log_path = _FK_DIR / "kb_increments_log.yaml"
    if kb_log_path.exists():
        raw = yaml.safe_load(kb_log_path.read_text(encoding="utf-8")) or {}
        prefix = f"examples/{name}/"
        raw["processed"] = [
            e for e in raw.get("processed", [])
            if not (str(e.get("generated_doc", "")).startswith(prefix)
                    or str(e.get("generated_script", "")).startswith(prefix))
        ]
        kb_log_path.write_text(yaml.dump(raw, default_flow_style=False, allow_unicode=True), encoding="utf-8")

    # 5. Pending approvals — drop pending_actions and resolved entries for this product
    approvals_path = _FK_DIR / "pending_approvals.yaml"
    if approvals_path.exists():
        raw = yaml.safe_load(approvals_path.read_text(encoding="utf-8")) or {}
        for key in ("pending_actions", "resolved", "pending"):
            raw[key] = [e for e in raw.get(key, []) if e.get("product") != name]
        approvals_path.write_text(yaml.dump(raw, default_flow_style=False, allow_unicode=True), encoding="utf-8")

    # 6. Run history — drop test nodeids that live under examples/<name>/
    run_history_path = _FK_DIR / "run_history.yaml"
    if run_history_path.exists():
        raw = yaml.safe_load(run_history_path.read_text(encoding="utf-8")) or {}
        prefix = f"examples/{name}/"
        raw["tests"] = {k: v for k, v in raw.get("tests", {}).items() if not k.startswith(prefix)}
        run_history_path.write_text(
            "# SentinelFlux Run History\n"
            "# Managed by QuarantineManager.record_run() — do not edit manually.\n"
            + yaml.dump({"tests": raw["tests"]}, default_flow_style=False, allow_unicode=True),
            encoding="utf-8",
        )

    # 7. Unassign product from all users
    for u in cfg.get("users", []):
        u["products"] = [p for p in u.get("products", []) if p != name]

    # 8. Remove from products list in config
    cfg["products"] = [p for p in cfg.get("products", []) if p["name"] != name]
    _save_config(cfg)

    # 9. Delete filesystem directories
    for d in [_KB_PRODUCTS_DIR / name, _EXAMPLES_DIR / name]:
        if d.exists():
            shutil.rmtree(d)


@router.post("/ui/config/products/delete", response_class=HTMLResponse)
async def products_delete(request: Request, name: str = Form(...)):
    name = name.strip()
    cfg = _load_config()
    _purge_product_data(name, cfg)
    return _render_products(request, cfg, flash=f"'{name}' and all associated data have been permanently deleted.")


@router.post("/ui/config/products/set-active", response_class=HTMLResponse)
async def products_set_active(request: Request, name: str = Form(...), active: str = Form("true")):
    cfg = _load_config()
    is_active = active.lower() not in {"false", "0", "no"}
    for p in cfg.get("products", []):
        if p["name"] == name:
            p["active"] = is_active
            break
    _save_config(cfg)
    flash = f"'{name}' is now {'active' if is_active else 'inactive'}."
    return _render_products(request, cfg, flash=flash)


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


@router.post("/ui/config/generation-categories/save", response_class=HTMLResponse)
async def generation_categories_save(request: Request):
    form = await request.form()
    cfg = _load_config()
    cats = {
        "functional": True,  # always on
        "negative": form.get("negative") == "on",
        "edge": form.get("edge") == "on",
        "security": form.get("security") == "on",
        "accessibility": form.get("accessibility") == "on",
    }
    cfg["generation_categories"] = cats
    _save_config(cfg)
    return templates.TemplateResponse(request, "partials/config_generation_categories.html", context={
        "request": request,
        "cats": cats,
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
        tests = [t for t in tests if
                 assignments.get(t["name"], {}).get("custom_fields", {}).get("owner", "") == filter_owner]
    if filter_jira_exists == "1":
        tests = [t for t in tests if assignments.get(t["name"], {}).get("custom_fields", {}).get("jira_ticket", "")]
    return tests


def _assignments_ctx(request, tests, assignments, cfg, product, search,
                     filter_labels, filter_priority, filter_owner, filter_jira_exists,
                     saved_test="", bulk_result=None):
    return templates.TemplateResponse(request, "partials/config_assignments.html", context={
        "request": request,
        "tests": tests,
        "assignments": assignments,
        "labels": cfg.get("labels", []),
        "priorities": cfg.get("priorities", []),
        "custom_fields": cfg.get("custom_fields", []),
        "users": cfg.get("users", []),
        "filter_product": product,
        "search": search,
        "filter_labels": filter_labels or [],
        "filter_priority": filter_priority,
        "filter_owner": filter_owner,
        "filter_jira_exists": filter_jira_exists,
        "saved_test": saved_test,
        "bulk_result": bulk_result,
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


@router.get("/ui/assignments/export")
async def assignments_export():
    import csv, io
    assignments = _load_assignments()
    cfg = _load_config()
    cf_names = [f["name"] for f in cfg.get("custom_fields", [])]
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=["test_name", "labels", "priority"] + cf_names)
    writer.writeheader()
    for test_name, asgn in sorted(assignments.items()):
        row = {
            "test_name": test_name,
            "labels": ",".join(asgn.get("labels", [])),
            "priority": asgn.get("priority", ""),
        }
        for cf in cf_names:
            row[cf] = asgn.get("custom_fields", {}).get(cf, "")
        writer.writerow(row)
    return Response(
        content=out.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=test_assignments.csv"},
    )


@router.get("/ui/assignments/csv-template")
async def assignments_csv_template_v2():
    cfg = _load_config()
    cf_names = [f["name"] for f in cfg.get("custom_fields", [])]
    header = ",".join(["test_name", "labels", "priority"] + cf_names)
    example = ",".join(["test_example_function", '"sanity,regression"', "P1"] + ["" for _ in cf_names])
    return Response(
        content=header + "\n" + example + "\n",
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=assignments_template.csv"},
    )


@router.get("/ui/assignments/list", response_class=HTMLResponse)
async def assignments_list_partial(
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
    return templates.TemplateResponse(request, "partials/assignment_list.html", context={
        "request": request,
        "tests": tests,
        "assignments": assignments,
        "labels": cfg.get("labels", []),
        "priorities": cfg.get("priorities", []),
        "search": search,
        "filter_product": product,
        "filter_labels": filter_labels,
        "filter_priority": filter_priority,
        "filter_owner": filter_owner,
        "filter_jira_exists": filter_jira_exists,
    })


@router.post("/ui/assignments/bulk-upload", response_class=HTMLResponse)
async def assignments_bulk_upload_v2(request: Request, file: UploadFile = File(...)):
    import csv, io
    content = (await file.read()).decode("utf-8", errors="replace")
    reader = csv.DictReader(io.StringIO(content))
    known_tests = {t["name"] for t in _all_tests()}
    assignments = _load_assignments()
    cfg = _load_config()
    updated = 0
    skipped: list[str] = []
    for row in reader:
        test_name = (row.get("test_name") or "").strip()
        if not test_name or test_name not in known_tests:
            if test_name:
                skipped.append(test_name)
            continue
        existing = assignments.get(test_name, {"labels": [], "priority": "", "custom_fields": {}})
        raw_labels = (row.get("labels") or "").strip()
        if raw_labels:
            new_labels = [l.strip() for l in raw_labels.split(",") if l.strip()]
            existing["labels"] = list(dict.fromkeys(existing.get("labels", []) + new_labels))
        priority = (row.get("priority") or "").strip()
        if priority:
            existing["priority"] = priority
        cf = existing.get("custom_fields", {})
        for f in cfg.get("custom_fields", []):
            val = (row.get(f["name"]) or "").strip()
            if val:
                cf[f["name"]] = val
        existing["custom_fields"] = cf
        assignments[test_name] = existing
        updated += 1
    _save_assignments(assignments)
    tests = _all_tests()
    bulk_result = {"updated": updated, "skipped": len(skipped), "skipped_names": skipped[:10]}
    return templates.TemplateResponse(request, "partials/assignment_list.html", context={
        "request": request,
        "tests": tests,
        "assignments": assignments,
        "labels": cfg.get("labels", []),
        "priorities": cfg.get("priorities", []),
        "search": "",
        "filter_product": "",
        "filter_labels": [],
        "filter_priority": "",
        "filter_owner": "",
        "filter_jira_exists": "",
        "bulk_result": bulk_result,
    })


@router.get("/ui/assignments/form", response_class=HTMLResponse)
async def assignment_form_partial(request: Request, test_name: str):
    assignments = _load_assignments()
    cfg = _load_config()
    asgn = assignments.get(test_name, {})
    return templates.TemplateResponse(request, "partials/assignment_form.html", context={
        "request": request,
        "test_name": test_name,
        "asgn": asgn,
        "labels": cfg.get("labels", []),
        "priorities": cfg.get("priorities", []),
        "custom_fields": cfg.get("custom_fields", []),
        "users": cfg.get("users", []),
        "saved": False,
    })


@router.post("/ui/assignments/save", response_class=HTMLResponse)
async def assignments_save_v2(request: Request):
    form = await request.form()
    test_name = form.get("test_name", "")
    labels = form.getlist("labels")
    priority = form.get("priority", "")
    cfg = _load_config()
    custom_fields = {f["name"]: form.get(f"cf_{f['name']}", "") for f in cfg.get("custom_fields", [])}
    assignments = _load_assignments()
    assignments[test_name] = {"labels": labels, "priority": priority, "custom_fields": custom_fields}
    _save_assignments(assignments)
    asgn = assignments[test_name]
    return templates.TemplateResponse(request, "partials/assignment_form.html", context={
        "request": request,
        "test_name": test_name,
        "asgn": asgn,
        "labels": cfg.get("labels", []),
        "priorities": cfg.get("priorities", []),
        "custom_fields": cfg.get("custom_fields", []),
        "users": cfg.get("users", []),
        "saved": True,
    })


@router.get("/ui/config/assignments/csv-template")
async def assignments_csv_template():
    content = "test_name,labels,priority,owner,jira_ticket\n"
    content += 'test_example_function,"sanity,regression",P1,Jane Smith,PROJ-123\n'
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=assignments_template.csv"},
    )


@router.post("/ui/config/assignments/bulk-upload", response_class=HTMLResponse)
async def assignments_bulk_upload(request: Request, file: UploadFile = File(...)):
    import csv, io

    content = (await file.read()).decode("utf-8", errors="replace")
    reader = csv.DictReader(io.StringIO(content))

    known_tests = {t["name"] for t in _all_tests()}
    assignments = _load_assignments()
    cfg = _load_config()

    updated = 0
    skipped: list[str] = []

    for row in reader:
        test_name = (row.get("test_name") or "").strip()
        if not test_name or test_name not in known_tests:
            if test_name:
                skipped.append(test_name)
            continue

        existing = assignments.get(test_name, {"labels": [], "priority": "", "custom_fields": {}})

        raw_labels = (row.get("labels") or "").strip()
        if raw_labels:
            new_labels = [l.strip() for l in raw_labels.split(",") if l.strip()]
            existing["labels"] = list(dict.fromkeys(existing.get("labels", []) + new_labels))

        priority = (row.get("priority") or "").strip()
        if priority:
            existing["priority"] = priority

        cf = existing.get("custom_fields", {})
        for field_name in ("owner", "jira_ticket"):
            val = (row.get(field_name) or "").strip()
            if val:
                cf[field_name] = val
        existing["custom_fields"] = cf

        assignments[test_name] = existing
        updated += 1

    _save_assignments(assignments)

    tests = _all_tests()
    bulk_result = {"updated": updated, "skipped": len(skipped), "skipped_names": skipped[:10]}
    return _assignments_ctx(request, tests, assignments, cfg, "", "", [], "", "", "",
                            bulk_result=bulk_result)


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
