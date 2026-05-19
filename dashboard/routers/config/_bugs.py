"""Bug workflow (custom statuses + state transitions) configuration routes."""
from __future__ import annotations

import re
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

_COLORS = ["sky", "amber", "violet", "emerald", "slate", "red", "yellow",
           "rose", "indigo", "teal", "orange", "purple", "cyan"]

_DEFAULT_STATUSES: list[dict] = [
    {"name": "new",         "label": "New",         "color": "sky"},
    {"name": "open",        "label": "Open",        "color": "amber"},
    {"name": "in_progress", "label": "In Progress", "color": "violet"},
    {"name": "resolved",    "label": "Resolved",    "color": "emerald"},
    {"name": "closed",      "label": "Closed",      "color": "slate"},
    {"name": "deferred",    "label": "Deferred",    "color": "yellow"},
    {"name": "wont_fix",    "label": "Won't Fix",   "color": "red"},
]

_DEFAULT_TRANSITIONS: dict[str, list[str]] = {
    "new":         ["open", "deferred", "wont_fix"],
    "open":        ["in_progress", "deferred", "wont_fix"],
    "in_progress": ["resolved", "open"],
    "resolved":    ["closed", "open"],
    "closed":      ["open"],
    "deferred":    ["open"],
    "wont_fix":    [],
}

_SAFE_NAME_RE = re.compile(r"^[a-z][a-z0-9_]{0,31}$")


def _load_product_statuses(product: str) -> list[dict]:
    cfg = _load_config()
    for p in cfg.get("products", []):
        if p["name"] == product:
            raw = p.get("bug_statuses")
            if raw:
                return raw
    return list(_DEFAULT_STATUSES)


def _load_product_transitions(product: str, statuses: list[dict]) -> dict[str, list[str]]:
    state_names = [s["name"] for s in statuses]
    valid = set(state_names)
    cfg = _load_config()
    for p in cfg.get("products", []):
        if p["name"] == product:
            raw = p.get("bug_transitions")
            if raw:
                return {s: [t for t in raw.get(s, []) if t in valid] for s in state_names}
    return {s: [t for t in _DEFAULT_TRANSITIONS.get(s, []) if t in valid] for s in state_names}


def _render_statuses(request: Request, product: str, flash: str = "") -> HTMLResponse:
    statuses = _load_product_statuses(product)
    return templates.TemplateResponse(request, "partials/config_bug_statuses.html", context={
        "product": product,
        "statuses": statuses,
        "colors": _COLORS,
        "flash": flash,
    })


def _render_transitions(request: Request, product: str, flash: str = "") -> HTMLResponse:
    statuses = _load_product_statuses(product)
    transitions = _load_product_transitions(product, statuses)
    return templates.TemplateResponse(request, "partials/config_bug_transitions.html", context={
        "product": product,
        "statuses": statuses,
        "transitions": transitions,
        "flash": flash,
    })


# ── Statuses ──────────────────────────────────────────────────────────────────

@router.get("/ui/config/bug-statuses/{product}", response_class=HTMLResponse)
async def bug_statuses_get(request: Request, product: str, _: dict = Depends(_require_admin)):
    return _render_statuses(request, product)


@router.post("/ui/config/bug-statuses/add", response_class=HTMLResponse)
async def bug_statuses_add(
    request: Request,
    product: str = Form(...),
    name: str = Form(...),
    label: str = Form(...),
    color: str = Form("slate"),
    _: dict = Depends(_require_admin),
):
    name = name.strip().lower().replace(" ", "_")
    label = label.strip()
    if not name or not _SAFE_NAME_RE.match(name):
        return _render_statuses(request, product, flash="Invalid name — use lowercase letters, digits, underscores (start with a letter).")
    if color not in _COLORS:
        color = "slate"

    cfg = _load_config()
    for p in cfg.get("products", []):
        if p["name"] == product:
            statuses = p.get("bug_statuses") or list(_DEFAULT_STATUSES)
            if any(s["name"] == name for s in statuses):
                return _render_statuses(request, product, flash=f"Status '{name}' already exists.")
            statuses.append({"name": name, "label": label or name.replace("_", " ").title(), "color": color})
            p["bug_statuses"] = statuses
            break
    _save_config(cfg)
    _audit_config(request, "Bug Workflow", f"Added bug status '{name}' to '{product}'")
    return _render_statuses(request, product, flash=f"Status '{name}' added.")


@router.post("/ui/config/bug-statuses/delete", response_class=HTMLResponse)
async def bug_statuses_delete(
    request: Request,
    product: str = Form(...),
    name: str = Form(...),
    _: dict = Depends(_require_admin),
):
    cfg = _load_config()
    for p in cfg.get("products", []):
        if p["name"] == product:
            statuses = p.get("bug_statuses") or list(_DEFAULT_STATUSES)
            p["bug_statuses"] = [s for s in statuses if s["name"] != name]
            # prune deleted status from transitions too
            trans = p.get("bug_transitions", {})
            trans.pop(name, None)
            for k in list(trans):
                trans[k] = [t for t in trans[k] if t != name]
            p["bug_transitions"] = trans
            break
    _save_config(cfg)
    _audit_config(request, "Bug Workflow", f"Deleted bug status '{name}' from '{product}'")
    return _render_statuses(request, product, flash=f"Status '{name}' deleted.")


@router.post("/ui/config/bug-statuses/reset", response_class=HTMLResponse)
async def bug_statuses_reset(
    request: Request,
    product: str = Form(...),
    _: dict = Depends(_require_admin),
):
    cfg = _load_config()
    for p in cfg.get("products", []):
        if p["name"] == product:
            p.pop("bug_statuses", None)
            p.pop("bug_transitions", None)
            break
    _save_config(cfg)
    _audit_config(request, "Bug Workflow", f"Reset bug statuses and transitions to defaults for '{product}'")
    return _render_statuses(request, product, flash="Statuses and transitions reset to defaults.")


# ── Transitions ───────────────────────────────────────────────────────────────

@router.get("/ui/config/bug-transitions/{product}", response_class=HTMLResponse)
async def bug_transitions_get(request: Request, product: str, _: dict = Depends(_require_admin)):
    return _render_transitions(request, product)


@router.post("/ui/config/bug-transitions/save", response_class=HTMLResponse)
async def bug_transitions_save(
    request: Request,
    product: str = Form(...),
    transitions: List[str] = Form(default=[]),
    _: dict = Depends(_require_admin),
):
    statuses = _load_product_statuses(product)
    state_names = {s["name"] for s in statuses}
    result: dict[str, list[str]] = {s["name"]: [] for s in statuses}
    for pair in transitions:
        parts = pair.split(":", 1)
        if len(parts) == 2:
            from_s, to_s = parts
            if from_s in state_names and to_s in state_names and from_s != to_s:
                result[from_s].append(to_s)

    cfg = _load_config()
    for p in cfg.get("products", []):
        if p["name"] == product:
            p["bug_transitions"] = result
            break
    _save_config(cfg)
    _audit_config(request, "Bug Workflow", f"Updated bug state transitions for '{product}'")
    return _render_transitions(request, product, flash=f"Transitions saved for '{product}'.")


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
    return _render_transitions(request, product, flash="Transitions reset to defaults.")
