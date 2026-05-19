"""Bug workflow (state transition) configuration routes."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse

from dashboard.routers.config._helpers import (
    _audit_config,
    _load_config,
    _require_admin,
    _save_config,
    templates,
)

router = APIRouter()

_ALL_STATES = ["new", "open", "in_progress", "resolved", "closed", "deferred", "wont_fix"]

_DEFAULT_TRANSITIONS: dict[str, list[str]] = {
    "new":         ["open", "deferred", "wont_fix"],
    "open":        ["in_progress", "deferred", "wont_fix"],
    "in_progress": ["resolved", "open"],
    "resolved":    ["closed", "open"],
    "closed":      ["open"],
    "deferred":    ["open"],
    "wont_fix":    [],
}


def _load_product_transitions(product: str) -> dict[str, list[str]]:
    cfg = _load_config()
    for p in cfg.get("products", []):
        if p["name"] == product:
            raw = p.get("bug_transitions")
            if raw:
                return {s: list(raw.get(s, [])) for s in _ALL_STATES}
    return {s: list(v) for s, v in _DEFAULT_TRANSITIONS.items()}


def _render(request: Request, product: str, flash: str = "") -> HTMLResponse:
    return templates.TemplateResponse(request, "partials/config_bug_transitions.html", context={
        "product": product,
        "transitions": _load_product_transitions(product),
        "all_states": _ALL_STATES,
        "flash": flash,
    })


@router.get("/ui/config/bug-transitions/{product}", response_class=HTMLResponse)
async def bug_transitions_get(request: Request, product: str, _: dict = Depends(_require_admin)):
    return _render(request, product)


@router.post("/ui/config/bug-transitions/save", response_class=HTMLResponse)
async def bug_transitions_save(
    request: Request,
    product: str = Form(...),
    transitions: List[str] = Form(default=[]),
    _: dict = Depends(_require_admin),
):
    result: dict[str, list[str]] = {s: [] for s in _ALL_STATES}
    for pair in transitions:
        parts = pair.split(":", 1)
        if len(parts) == 2:
            from_s, to_s = parts
            if from_s in _ALL_STATES and to_s in _ALL_STATES and from_s != to_s:
                result[from_s].append(to_s)

    cfg = _load_config()
    for p in cfg.get("products", []):
        if p["name"] == product:
            p["bug_transitions"] = result
            break
    _save_config(cfg)
    _audit_config(request, "Bug Workflow", f"Updated bug state transitions for '{product}'")
    return _render(request, product, flash=f"Transitions saved for '{product}'.")


@router.post("/ui/config/bug-transitions/reset", response_class=HTMLResponse)
async def bug_transitions_reset(
    request: Request,
    product: str = Form(...),
    _: dict = Depends(_require_admin),
):
    cfg = _load_config()
    for p in cfg.get("products", []):
        if p["name"] == product:
            p.pop("bug_transitions", None)
            break
    _save_config(cfg)
    _audit_config(request, "Bug Workflow", f"Reset bug transitions to defaults for '{product}'")
    return _render(request, product, flash=f"Transitions reset to defaults for '{product}'.")
