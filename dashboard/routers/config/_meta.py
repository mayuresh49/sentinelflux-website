"""Labels, priorities, custom fields, test-type distribution, generation-category routes."""
from __future__ import annotations

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse

from dashboard.routers.config._helpers import _load_config, _save_config, templates

router = APIRouter()


def _render_labels(request: Request, cfg: dict) -> HTMLResponse:
    return templates.TemplateResponse(request, "partials/config_labels.html", context={
        "request": request, "labels": cfg.get("labels", []),
    })


def _render_priorities(request: Request, cfg: dict) -> HTMLResponse:
    return templates.TemplateResponse(request, "partials/config_priorities.html", context={
        "request": request, "priorities": cfg.get("priorities", []),
    })


def _render_fields(request: Request, cfg: dict) -> HTMLResponse:
    return templates.TemplateResponse(request, "partials/config_fields.html", context={
        "request": request, "custom_fields": cfg.get("custom_fields", []),
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


@router.post("/ui/config/test-types/save", response_class=HTMLResponse)
async def test_types_save(request: Request, sanity: int = Form(...)):
    sanity = max(0, min(100, sanity))
    cfg = _load_config()
    cfg["test_type_distribution"] = {"sanity": sanity, "regression": 100 - sanity}
    _save_config(cfg)
    return templates.TemplateResponse(request, "partials/config_test_types.html", context={
        "request": request, "dist": cfg["test_type_distribution"], "saved": True,
    })


@router.post("/ui/config/generation-categories/save", response_class=HTMLResponse)
async def generation_categories_save(request: Request):
    form = await request.form()
    cfg = _load_config()
    cfg["generation_categories"] = {
        "functional": True,
        "negative": form.get("negative") == "on",
        "edge": form.get("edge") == "on",
        "security": form.get("security") == "on",
        "accessibility": form.get("accessibility") == "on",
    }
    _save_config(cfg)
    return templates.TemplateResponse(request, "partials/config_generation_categories.html", context={
        "request": request, "cats": cfg["generation_categories"], "saved": True,
    })
