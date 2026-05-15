"""Per-product run configuration: environments, browsers, devices, credentials, defaults."""
from __future__ import annotations

import json as _json

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse

from dashboard.routers.auth import get_session_user, require_user
from dashboard.routers.config._helpers import (
    _audit_config,
    _load_config,
    _save_config,
    templates,
)

router = APIRouter()


def _require_admin(current_user: dict = Depends(require_user)) -> dict:
    if not current_user.get("admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


def _backfill_run_config(p: dict) -> None:
    rc = p.setdefault("run_config", {})
    rc.setdefault("environments", [])
    rc.setdefault("browsers", [])
    rc.setdefault("devices", [])
    rc.setdefault("credentials", [])
    defaults = rc.setdefault("defaults", {})
    defaults.setdefault("environment", "")
    defaults.setdefault("browser", "")
    defaults.setdefault("device", "")
    defaults.setdefault("skip_quarantined", True)


def _find_product(cfg: dict, product: str) -> dict | None:
    return next((p for p in cfg.get("products", []) if p["name"] == product), None)


def _render(request: Request, product: str, flash: str = "") -> HTMLResponse:
    cfg = _load_config()
    p = _find_product(cfg, product)
    if not p:
        raise HTTPException(404, "Product not found")
    _backfill_run_config(p)
    current_user = get_session_user(request) or {}
    return templates.TemplateResponse(request, "partials/config_run_config.html", context={
        "request": request,
        "product": product,
        "rc": p["run_config"],
        "flash": flash,
        "current_user": current_user,
    })


# ── JSON endpoint for frontend fetch ─────────────────────────────────────────

@router.get("/api/config/run-config/{product}")
def run_config_json(product: str, _: dict = Depends(require_user)):
    cfg = _load_config()
    p = _find_product(cfg, product)
    if not p:
        raise HTTPException(404, "Product not found")
    _backfill_run_config(p)
    return p["run_config"]


# ── HTMX partial loader ───────────────────────────────────────────────────────

@router.get("/ui/config/run-config/{product}", response_class=HTMLResponse)
async def run_config_partial(request: Request, product: str):
    return _render(request, product)


# ── Environments ──────────────────────────────────────────────────────────────

@router.post("/ui/config/run-config/{product}/env/add", response_class=HTMLResponse)
async def env_add(
    request: Request, product: str,
    name: str = Form(...), base_url: str = Form(""), api_url: str = Form(""),
    _: dict = Depends(_require_admin),
):
    cfg = _load_config()
    p = _find_product(cfg, product)
    if not p:
        raise HTTPException(404)
    _backfill_run_config(p)
    name = name.strip()
    if not name:
        return _render(request, product, flash="Please select an environment.")
    if any(e["name"] == name for e in p["run_config"]["environments"]):
        return _render(request, product, flash=f"Environment '{name}' already exists.")
    p["run_config"]["environments"].append({"name": name, "base_url": base_url.strip(), "api_url": api_url.strip()})
    _save_config(cfg)
    _audit_config(request, "Run Configuration", f"[{product}] Added environment '{name}'")
    return _render(request, product, flash=f"Environment '{name}' added.")


@router.post("/ui/config/run-config/{product}/env/delete", response_class=HTMLResponse)
async def env_delete(
    request: Request, product: str, name: str = Form(...),
    _: dict = Depends(_require_admin),
):
    cfg = _load_config()
    p = _find_product(cfg, product)
    if not p:
        raise HTTPException(404)
    _backfill_run_config(p)
    p["run_config"]["environments"] = [e for e in p["run_config"]["environments"] if e["name"] != name]
    if p["run_config"]["defaults"].get("environment") == name:
        p["run_config"]["defaults"]["environment"] = ""
    _save_config(cfg)
    _audit_config(request, "Run Configuration", f"[{product}] Deleted environment '{name}'")
    return _render(request, product)


# ── Browsers ──────────────────────────────────────────────────────────────────

@router.post("/ui/config/run-config/{product}/browser/add", response_class=HTMLResponse)
async def browser_add(
    request: Request, product: str,
    name: str = Form(...), browser: str = Form("chromium"), headless: str = Form("false"),
    _: dict = Depends(_require_admin),
):
    cfg = _load_config()
    p = _find_product(cfg, product)
    if not p:
        raise HTTPException(404)
    _backfill_run_config(p)
    name = name.strip()
    if not name:
        return _render(request, product, flash="Please enter a browser profile name.")
    if any(b["name"] == name for b in p["run_config"]["browsers"]):
        return _render(request, product, flash=f"Browser profile '{name}' already exists.")
    p["run_config"]["browsers"].append({
        "name": name,
        "browser": browser,
        "headless": headless.lower() in ("true", "on", "1", "yes"),
    })
    _save_config(cfg)
    _audit_config(request, "Run Configuration", f"[{product}] Added browser profile '{name}'")
    return _render(request, product, flash=f"Browser profile '{name}' added.")


@router.post("/ui/config/run-config/{product}/browser/delete", response_class=HTMLResponse)
async def browser_delete(
    request: Request, product: str, name: str = Form(...),
    _: dict = Depends(_require_admin),
):
    cfg = _load_config()
    p = _find_product(cfg, product)
    if not p:
        raise HTTPException(404)
    _backfill_run_config(p)
    p["run_config"]["browsers"] = [b for b in p["run_config"]["browsers"] if b["name"] != name]
    if p["run_config"]["defaults"].get("browser") == name:
        p["run_config"]["defaults"]["browser"] = ""
    _save_config(cfg)
    _audit_config(request, "Run Configuration", f"[{product}] Deleted browser profile '{name}'")
    return _render(request, product)


# ── Devices ───────────────────────────────────────────────────────────────────

@router.post("/ui/config/run-config/{product}/device/add", response_class=HTMLResponse)
async def device_add(
    request: Request, product: str,
    name: str = Form(...), platform: str = Form("android"),
    appium_url: str = Form("http://localhost:4723"),
    capabilities: str = Form("{}"),
    _: dict = Depends(_require_admin),
):
    cfg = _load_config()
    p = _find_product(cfg, product)
    if not p:
        raise HTTPException(404)
    _backfill_run_config(p)
    name = name.strip()
    if not name:
        return _render(request, product, flash="Please enter a device profile name.")
    if any(d["name"] == name for d in p["run_config"]["devices"]):
        return _render(request, product, flash=f"Device profile '{name}' already exists.")
    try:
        caps = _json.loads(capabilities)
    except Exception:
        caps = {}
    p["run_config"]["devices"].append({
        "name": name,
        "platform": platform,
        "appium_url": appium_url.strip(),
        "capabilities": caps,
    })
    _save_config(cfg)
    _audit_config(request, "Run Configuration", f"[{product}] Added device profile '{name}'")
    return _render(request, product, flash=f"Device profile '{name}' added.")


@router.post("/ui/config/run-config/{product}/device/delete", response_class=HTMLResponse)
async def device_delete(
    request: Request, product: str, name: str = Form(...),
    _: dict = Depends(_require_admin),
):
    cfg = _load_config()
    p = _find_product(cfg, product)
    if not p:
        raise HTTPException(404)
    _backfill_run_config(p)
    p["run_config"]["devices"] = [d for d in p["run_config"]["devices"] if d["name"] != name]
    if p["run_config"]["defaults"].get("device") == name:
        p["run_config"]["defaults"]["device"] = ""
    _save_config(cfg)
    _audit_config(request, "Run Configuration", f"[{product}] Deleted device profile '{name}'")
    return _render(request, product)


# ── Credentials ───────────────────────────────────────────────────────────────

@router.post("/ui/config/run-config/{product}/credential/add", response_class=HTMLResponse)
async def credential_add(
    request: Request, product: str,
    name: str = Form(...), username: str = Form(""), password_env: str = Form(""),
    _: dict = Depends(_require_admin),
):
    cfg = _load_config()
    p = _find_product(cfg, product)
    if not p:
        raise HTTPException(404)
    _backfill_run_config(p)
    name = name.strip()
    if not name:
        return _render(request, product, flash="Please enter a credential name.")
    if any(c["name"] == name for c in p["run_config"]["credentials"]):
        return _render(request, product, flash=f"Credential '{name}' already exists.")
    p["run_config"]["credentials"].append({
        "name": name,
        "username": username.strip(),
        "password_env": password_env.strip(),
    })
    _save_config(cfg)
    _audit_config(request, "Run Configuration", f"[{product}] Added credential '{name}'")
    return _render(request, product, flash=f"Credential '{name}' added.")


@router.post("/ui/config/run-config/{product}/credential/delete", response_class=HTMLResponse)
async def credential_delete(
    request: Request, product: str, name: str = Form(...),
    _: dict = Depends(_require_admin),
):
    cfg = _load_config()
    p = _find_product(cfg, product)
    if not p:
        raise HTTPException(404)
    _backfill_run_config(p)
    p["run_config"]["credentials"] = [c for c in p["run_config"]["credentials"] if c["name"] != name]
    _save_config(cfg)
    _audit_config(request, "Run Configuration", f"[{product}] Deleted credential '{name}'")
    return _render(request, product)


# ── Toggle Defaults ───────────────────────────────────────────────────────────

@router.post("/ui/config/run-config/{product}/env/toggle-default", response_class=HTMLResponse)
async def env_toggle_default(
    request: Request, product: str, name: str = Form(...),
    _: dict = Depends(_require_admin),
):
    cfg = _load_config()
    p = _find_product(cfg, product)
    if not p:
        raise HTTPException(404)
    _backfill_run_config(p)
    current = p["run_config"]["defaults"].get("environment", "")
    p["run_config"]["defaults"]["environment"] = "" if current == name else name
    _save_config(cfg)
    action = "Unset" if current == name else "Set"
    _audit_config(request, "Run Configuration", f"[{product}] {action} default environment '{name}'")
    return _render(request, product)


@router.post("/ui/config/run-config/{product}/browser/toggle-default", response_class=HTMLResponse)
async def browser_toggle_default(
    request: Request, product: str, name: str = Form(...),
    _: dict = Depends(_require_admin),
):
    cfg = _load_config()
    p = _find_product(cfg, product)
    if not p:
        raise HTTPException(404)
    _backfill_run_config(p)
    current = p["run_config"]["defaults"].get("browser", "")
    p["run_config"]["defaults"]["browser"] = "" if current == name else name
    _save_config(cfg)
    action = "Unset" if current == name else "Set"
    _audit_config(request, "Run Configuration", f"[{product}] {action} default browser '{name}'")
    return _render(request, product)


@router.post("/ui/config/run-config/{product}/device/toggle-default", response_class=HTMLResponse)
async def device_toggle_default(
    request: Request, product: str, name: str = Form(...),
    _: dict = Depends(_require_admin),
):
    cfg = _load_config()
    p = _find_product(cfg, product)
    if not p:
        raise HTTPException(404)
    _backfill_run_config(p)
    current = p["run_config"]["defaults"].get("device", "")
    p["run_config"]["defaults"]["device"] = "" if current == name else name
    _save_config(cfg)
    action = "Unset" if current == name else "Set"
    _audit_config(request, "Run Configuration", f"[{product}] {action} default device '{name}'")
    return _render(request, product)


# ── Defaults ──────────────────────────────────────────────────────────────────

@router.post("/ui/config/run-config/{product}/defaults", response_class=HTMLResponse)
async def defaults_save(
    request: Request, product: str,
    environment: str = Form(""), browser: str = Form(""), device: str = Form(""),
    _: dict = Depends(_require_admin),
):
    cfg = _load_config()
    p = _find_product(cfg, product)
    if not p:
        raise HTTPException(404)
    _backfill_run_config(p)
    existing = p["run_config"]["defaults"]
    p["run_config"]["defaults"] = {
        "environment": environment,
        "browser": browser,
        "device": device,
        "skip_quarantined": existing.get("skip_quarantined", True),
    }
    _save_config(cfg)
    _audit_config(request, "Run Configuration", f"[{product}] Updated default profile")
    return _render(request, product, flash="Defaults saved.")


# ── Quarantine behavior ───────────────────────────────────────────────────────

@router.post("/ui/config/run-config/{product}/toggle-skip-quarantined", response_class=HTMLResponse)
async def toggle_skip_quarantined(
    request: Request, product: str,
    _: dict = Depends(_require_admin),
):
    cfg = _load_config()
    p = _find_product(cfg, product)
    if not p:
        raise HTTPException(404)
    _backfill_run_config(p)
    current = p["run_config"]["defaults"].get("skip_quarantined", True)
    p["run_config"]["defaults"]["skip_quarantined"] = not current
    _save_config(cfg)
    verb = "enabled" if not current else "disabled"
    _audit_config(request, "Run Configuration", f"[{product}] Skip Quarantined Tests {verb}")
    return _render(request, product)
