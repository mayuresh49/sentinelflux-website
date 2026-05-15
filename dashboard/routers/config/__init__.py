"""Config subpackage: assembles all config routes into one router."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from dashboard.routers.auth import require_user, user_products
from dashboard.routers.config import _assignments, _meta, _products, _run_config, _users
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


# Re-export public API so external callers can still import from the subpackage
from dashboard.routers.config._helpers import (  # noqa: E402, F401
    _save_assignments,
    _save_config,
    assignments_summary_by_feature,
    get_generation_categories_instruction,
    get_generation_type_instruction,
    get_test_type_for_index,
)
