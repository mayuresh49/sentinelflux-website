"""Labels, priorities, custom fields, test-type distribution, generation-category routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse

from dashboard.routers.config._helpers import (
    _audit_config,
    _load_config,
    _product_dist,
    _product_entry,
    _product_gen_cats,
    _product_labels,
    _product_priorities,
    _require_admin,
    _save_config,
    templates,
)

router = APIRouter()


def _render_labels(request: Request, cfg: dict, product: str = "") -> HTMLResponse:
    labels = _product_labels(cfg, product) if product else cfg.get("labels", [])
    return templates.TemplateResponse(request, "partials/config_labels.html", context={
        "request": request, "labels": labels, "product": product,
    })


def _render_priorities(request: Request, cfg: dict, product: str = "") -> HTMLResponse:
    priorities = _product_priorities(cfg, product) if product else cfg.get("priorities", [])
    return templates.TemplateResponse(request, "partials/config_priorities.html", context={
        "request": request, "priorities": priorities, "product": product,
    })


def _render_fields(request: Request, cfg: dict) -> HTMLResponse:
    return templates.TemplateResponse(request, "partials/config_fields.html", context={
        "request": request, "custom_fields": cfg.get("custom_fields", []),
    })


# ── Labels ───────────────────────────────────────────────────────────────────

@router.get("/ui/config/labels/{product}", response_class=HTMLResponse)
async def labels_for_product(request: Request, product: str):
    cfg = _load_config()
    return _render_labels(request, cfg, product)


@router.post("/ui/config/labels/add", response_class=HTMLResponse)
async def labels_add(request: Request, name: str = Form(...), color: str = Form("slate"),
                     product: str = Form(""), _: dict = Depends(_require_admin)):
    cfg = _load_config()
    name = name.strip().lower().replace(" ", "_")
    if not name:
        return _render_labels(request, cfg, product)
    if product:
        p = _product_entry(cfg, product)
        if p is not None:
            p.setdefault("labels", [])
            if not any(lbl["name"] == name for lbl in p["labels"]):
                p["labels"].append({"name": name, "color": color})
                _save_config(cfg)
                _audit_config(request, "Test Types", f"[{product}] Added label '{name}'")
    else:
        if not any(lbl["name"] == name for lbl in cfg.get("labels", [])):
            cfg.setdefault("labels", []).append({"name": name, "color": color})
            _save_config(cfg)
            _audit_config(request, "Test Types", f"Added test type label '{name}'")
    return _render_labels(request, cfg, product)


@router.post("/ui/config/labels/delete", response_class=HTMLResponse)
async def labels_delete(request: Request, name: str = Form(...), product: str = Form(""),
                        _: dict = Depends(_require_admin)):
    cfg = _load_config()
    if product:
        p = _product_entry(cfg, product)
        if p is not None and "labels" in p:
            p["labels"] = [lbl for lbl in p["labels"] if lbl["name"] != name]
            _save_config(cfg)
            _audit_config(request, "Test Types", f"[{product}] Deleted label '{name}'")
    else:
        cfg["labels"] = [lbl for lbl in cfg.get("labels", []) if lbl["name"] != name]
        _save_config(cfg)
        _audit_config(request, "Test Types", f"Deleted test type label '{name}'")
    return _render_labels(request, cfg, product)


# ── Priorities ────────────────────────────────────────────────────────────────

@router.get("/ui/config/priorities/{product}", response_class=HTMLResponse)
async def priorities_for_product(request: Request, product: str):
    cfg = _load_config()
    return _render_priorities(request, cfg, product)


@router.post("/ui/config/priorities/add", response_class=HTMLResponse)
async def priorities_add(request: Request, name: str = Form(...), color: str = Form("slate"),
                         product: str = Form(""), _: dict = Depends(_require_admin)):
    cfg = _load_config()
    name = name.strip().upper().replace(" ", "")
    if not name:
        return _render_priorities(request, cfg, product)
    if product:
        p = _product_entry(cfg, product)
        if p is not None:
            p.setdefault("priorities", [])
            if not any(pr["name"] == name for pr in p["priorities"]):
                p["priorities"].append({"name": name, "color": color})
                _save_config(cfg)
                _audit_config(request, "Priorities", f"[{product}] Added priority '{name}'")
    else:
        if not any(pr["name"] == name for pr in cfg.get("priorities", [])):
            cfg.setdefault("priorities", []).append({"name": name, "color": color})
            _save_config(cfg)
            _audit_config(request, "Priorities", f"Added priority '{name}'")
    return _render_priorities(request, cfg, product)


@router.post("/ui/config/priorities/delete", response_class=HTMLResponse)
async def priorities_delete(request: Request, name: str = Form(...), product: str = Form(""),
                            _: dict = Depends(_require_admin)):
    cfg = _load_config()
    if product:
        p = _product_entry(cfg, product)
        if p is not None and "priorities" in p:
            p["priorities"] = [pr for pr in p["priorities"] if pr["name"] != name]
            _save_config(cfg)
            _audit_config(request, "Priorities", f"[{product}] Deleted priority '{name}'")
    else:
        cfg["priorities"] = [pr for pr in cfg.get("priorities", []) if pr["name"] != name]
        _save_config(cfg)
        _audit_config(request, "Priorities", f"Deleted priority '{name}'")
    return _render_priorities(request, cfg, product)


# ── Custom Fields ─────────────────────────────────────────────────────────────

@router.post("/ui/config/fields/add", response_class=HTMLResponse)
async def fields_add(request: Request, name: str = Form(...), field_type: str = Form("text"),
                     _: dict = Depends(_require_admin)):
    cfg = _load_config()
    name = name.strip().lower().replace(" ", "_")
    if name and not any(f["name"] == name for f in cfg.get("custom_fields", [])):
        cfg.setdefault("custom_fields", []).append({"name": name, "type": field_type})
        _save_config(cfg)
        _audit_config(request, "Custom Fields", f"Added custom field '{name}' ({field_type})")
    return _render_fields(request, cfg)


@router.post("/ui/config/fields/delete", response_class=HTMLResponse)
async def fields_delete(request: Request, name: str = Form(...), _: dict = Depends(_require_admin)):
    cfg = _load_config()
    cfg["custom_fields"] = [f for f in cfg.get("custom_fields", []) if f["name"] != name]
    _save_config(cfg)
    _audit_config(request, "Custom Fields", f"Deleted custom field '{name}'")
    return _render_fields(request, cfg)


# ── Test Distribution ─────────────────────────────────────────────────────────

@router.get("/ui/config/test-distribution/{product}", response_class=HTMLResponse)
async def test_distribution_for_product(request: Request, product: str):
    cfg = _load_config()
    dist = _product_dist(cfg, product)
    return templates.TemplateResponse(request, "partials/config_test_types.html", context={
        "request": request, "dist": dist, "product": product,
    })


@router.post("/ui/config/test-types/save", response_class=HTMLResponse)
async def test_types_save(request: Request, sanity: int = Form(...),
                          product: str = Form(""), _: dict = Depends(_require_admin)):
    sanity = max(0, min(100, sanity))
    dist = {"sanity": sanity, "regression": 100 - sanity}
    cfg = _load_config()
    if product:
        p = _product_entry(cfg, product)
        if p is not None:
            p["test_type_distribution"] = dist
            _save_config(cfg)
            _audit_config(request, "Test Distribution",
                          f"[{product}] Set sanity {sanity}% / regression {100 - sanity}%")
    else:
        cfg["test_type_distribution"] = dist
        _save_config(cfg)
        _audit_config(request, "Test Distribution", f"Set sanity {sanity}% / regression {100 - sanity}%")
    return templates.TemplateResponse(request, "partials/config_test_types.html", context={
        "request": request, "dist": dist, "product": product, "saved": True,
    })


# ── Generation Categories ─────────────────────────────────────────────────────

@router.get("/ui/config/generation-categories/{product}", response_class=HTMLResponse)
async def generation_categories_for_product(request: Request, product: str):
    cfg = _load_config()
    cats = _product_gen_cats(cfg, product)
    return templates.TemplateResponse(request, "partials/config_generation_categories.html", context={
        "request": request, "cats": cats, "product": product,
    })


@router.post("/ui/config/generation-categories/save", response_class=HTMLResponse)
async def generation_categories_save(request: Request, _: dict = Depends(_require_admin)):
    form = await request.form()
    product = str(form.get("product", "")).strip()
    new_cats = {
        "functional": True,
        "negative": form.get("negative") == "on",
        "edge": form.get("edge") == "on",
        "security": form.get("security") == "on",
        "accessibility": form.get("accessibility") == "on",
    }
    cfg = _load_config()
    if product:
        p = _product_entry(cfg, product)
        if p is not None:
            p["generation_categories"] = new_cats
    else:
        cfg["generation_categories"] = new_cats
    _save_config(cfg)
    enabled = [k for k, v in new_cats.items() if v]
    _audit_config(request, "Test Generation",
                  f"[{product or 'global'}] Updated generation categories: {', '.join(enabled)}")
    return templates.TemplateResponse(request, "partials/config_generation_categories.html", context={
        "request": request, "cats": new_cats, "product": product, "saved": True,
    })
