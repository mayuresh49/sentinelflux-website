"""Config subpackage: assembles all config routes into one router."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from dashboard.routers.auth import require_user, user_products
from dashboard.routers.config import _assignments, _meta, _products, _run_config, _runners, _users
from dashboard.routers.config._helpers import (
    _all_tests,
    _load_assignments,
    _load_config,
    templates,
)

router = APIRouter(tags=["config"], dependencies=[Depends(require_user)])

router.include_router(_meta.router)
router.include_router(_users.router)
router.include_router(_products.router)
router.include_router(_assignments.router)
router.include_router(_run_config.router)
router.include_router(_runners.router)


@router.get("/config", response_class=HTMLResponse)
async def config_page(request: Request, product: Optional[str] = None,
                      current_user: dict = Depends(require_user)):
    cfg = _load_config()
    assignments = _load_assignments()
    tests = _all_tests()
    from core.approval_manager import ApprovalManager
    _am = ApprovalManager()
    all_prods = [p["name"] for p in cfg.get("products", []) if p.get("active", True)]
    visible_products = user_products(current_user, all_prods)
    enriched_products = []
    for _p in cfg.get("products", []):
        tc = _products._product_test_count(_p["name"])
        enriched_products.append({**_p, "has_tests": tc > 0, "test_count": tc})
    from core.audit_logger import recent as _audit_recent
    user_prod_set = set(current_user.get("products", []))
    prods = cfg.get("products", [])

    def _has_flag(flag: str) -> bool:
        return bool(current_user.get("admin") or any(
            p.get(flag) and p["name"] in user_prod_set for p in prods
        ))

    return templates.TemplateResponse(request, "config.html", context={
        "pending_count": len(_am.pending()),
        "all_products": visible_products,
        "current_user": current_user,
        "vapt_access": _has_flag("vapt_enabled"),
        "perf_access": _has_flag("perf_enabled"),
        "a11y_access": _has_flag("a11y_enabled"),
        "contract_access": _has_flag("contract_enabled"),
        "visual_access": _has_flag("visual_enabled"),
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
        "audit_events": [e for e in _audit_recent(100) if e.get("type") == "config_change"],
    })


# Re-export public API so external callers can still import from the subpackage
from dashboard.routers.config._helpers import (  # noqa: E402, F401
    _save_assignments,
    _save_config,
    assignments_summary_by_feature,
    get_generation_categories_instruction,
    get_generation_type_instruction,
    get_test_type_for_index,
)
