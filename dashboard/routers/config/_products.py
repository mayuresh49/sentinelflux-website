"""Product management routes."""
from __future__ import annotations

import json
import re as _re
import shutil
from typing import List

import yaml
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse

from dashboard.routers.config._helpers import (
    _ASSIGNMENTS_PATH,
    _DATA_DIR,
    _KB_PRODUCTS_DIR,
    _PRODUCTS_DIR,
    _SAFE_PRODUCT_RE,
    _audit_config,
    _load_config,
    _require_admin,
    _save_assignments,
    _save_config,
    templates,
)

router = APIRouter()


def _product_test_count(product: str) -> int:
    tests_dir = _PRODUCTS_DIR / product / "tests"
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
    enriched = [{**p, "has_tests": (tc := _product_test_count(p["name"])) > 0, "test_count": tc}
                for p in cfg.get("products", [])]
    return templates.TemplateResponse(request, "partials/config_products.html", context={
        "request": request, "products": enriched, "flash": flash,
    })


def _purge_product_data(name: str, cfg: dict) -> None:
    """Remove all data associated with a product across every data store."""
    # 1. Test assignments
    if _ASSIGNMENTS_PATH.exists():
        raw = yaml.safe_load(_ASSIGNMENTS_PATH.read_text(encoding="utf-8")) or {}
        assignments = raw.get("assignments", {})
        tests_dir = _PRODUCTS_DIR / name / "tests"
        product_fns: set[str] = set()
        if tests_dir.exists():
            for py in tests_dir.rglob("test_*.py"):
                try:
                    product_fns.update(_re.findall(r"^def (test_\w+)", py.read_text(encoding="utf-8"), _re.MULTILINE))
                except OSError:
                    pass
        pruned = {k: v for k, v in assignments.items() if k not in product_fns}
        if pruned != assignments:
            _save_assignments(pruned)

    # 2. Pipeline jobs
    jobs_path = _DATA_DIR / "pipeline_jobs.json"
    if jobs_path.exists():
        data = json.loads(jobs_path.read_text(encoding="utf-8"))
        data["jobs"] = [j for j in data.get("jobs", []) if j.get("product") != name]
        jobs_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    # 3. Activity log
    alog_path = _DATA_DIR / "activity_log.json"
    if alog_path.exists():
        data = json.loads(alog_path.read_text(encoding="utf-8"))
        data["entries"] = [e for e in data.get("entries", []) if e.get("product") != name]
        alog_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    # 4. KB increments log
    kb_log_path = _DATA_DIR / "kb_increments_log.yaml"
    if kb_log_path.exists():
        raw = yaml.safe_load(kb_log_path.read_text(encoding="utf-8")) or {}
        prefix = f"products/{name}/"
        raw["processed"] = [
            e for e in raw.get("processed", [])
            if not (str(e.get("generated_doc", "")).startswith(prefix)
                    or str(e.get("generated_script", "")).startswith(prefix))
        ]
        kb_log_path.write_text(yaml.dump(raw, default_flow_style=False, allow_unicode=True), encoding="utf-8")

    # 5. Pending approvals + quarantine data
    from core.db import get_conn as _get_conn
    _conn = _get_conn()
    _conn.execute("DELETE FROM approvals WHERE product = ?", (name,))
    _conn.execute("DELETE FROM quarantine WHERE product = ?", (name,))
    _conn.execute("DELETE FROM quarantine_pending WHERE product = ?", (name,))
    _conn.execute("DELETE FROM test_runs WHERE product = ?", (name,))
    _conn.execute("DELETE FROM test_schedules WHERE product = ?", (name,))
    # run_history has no product column in all rows, but node IDs include product path
    prefix = f"products/{name}/"
    _conn.execute("DELETE FROM run_history WHERE test_id LIKE ?", (prefix + "%",))
    _conn.commit()

    # 7. Unassign product from all users + remove from products list
    for u in cfg.get("users", []):
        u["products"] = [p for p in u.get("products", []) if p != name]
    cfg["products"] = [p for p in cfg.get("products", []) if p["name"] != name]
    _save_config(cfg)

    # 8. Delete filesystem directories
    for d in [_KB_PRODUCTS_DIR / name, _PRODUCTS_DIR / name]:
        if d.exists():
            shutil.rmtree(d)


_VALID_DOMAINS = {"web", "api", "mobile"}


@router.post("/ui/config/products/add", response_class=HTMLResponse)
async def products_add(
    request: Request,
    name: str = Form(...),
    display_name: str = Form(""),
    domains: List[str] = Form(default=[]),
    _: dict = Depends(_require_admin),
):
    name = name.strip().lower().replace(" ", "_")
    cfg = _load_config()
    if name and _SAFE_PRODUCT_RE.match(name) and not any(p["name"] == name for p in cfg.get("products", [])):
        sanitized_domains = sorted({d for d in domains if d in _VALID_DOMAINS})
        cfg.setdefault("products", []).append({
            "name": name,
            "display_name": display_name.strip() or name.replace("_", " ").title(),
            "active": True,
            "domains": sanitized_domains,
        })
        _save_config(cfg)
        (_KB_PRODUCTS_DIR / name).mkdir(parents=True, exist_ok=True)
        (_PRODUCTS_DIR / name / "tests").mkdir(parents=True, exist_ok=True)
        (_PRODUCTS_DIR / name / "pages").mkdir(parents=True, exist_ok=True)
        _audit_config(request, "Products", f"Added product '{name}'")
    return _render_products(request, cfg)


@router.post("/ui/config/products/delete", response_class=HTMLResponse)
async def products_delete(request: Request, name: str = Form(...), _: dict = Depends(_require_admin)):
    name = name.strip()
    cfg = _load_config()
    _audit_config(request, "Products", f"Deleted product '{name}' and all associated data")
    _purge_product_data(name, cfg)
    return _render_products(request, cfg, flash=f"'{name}' and all associated data have been permanently deleted.")


@router.post("/ui/config/products/set-active", response_class=HTMLResponse)
async def products_set_active(request: Request, name: str = Form(...), active: str = Form("true"),
                              _: dict = Depends(_require_admin)):
    cfg = _load_config()
    is_active = active.lower() not in {"false", "0", "no"}
    for p in cfg.get("products", []):
        if p["name"] == name:
            p["active"] = is_active
            break
    _save_config(cfg)
    _audit_config(request, "Products", f"Set product '{name}' {'active' if is_active else 'inactive'}")
    return _render_products(request, cfg, flash=f"'{name}' is now {'active' if is_active else 'inactive'}.")


@router.post("/ui/config/products/set-vapt", response_class=HTMLResponse)
async def products_set_vapt(request: Request, name: str = Form(...), vapt: str = Form("true"),
                            _: dict = Depends(_require_admin)):
    cfg = _load_config()
    enabled = vapt.lower() not in {"false", "0", "no"}
    for p in cfg.get("products", []):
        if p["name"] == name:
            p["vapt_enabled"] = enabled
            break
    _save_config(cfg)
    _audit_config(request, "Products", f"Set VAPT {'enabled' if enabled else 'disabled'} for '{name}'")
    return _render_products(request, cfg, flash=f"VAPT {'enabled' if enabled else 'disabled'} for '{name}'.")
