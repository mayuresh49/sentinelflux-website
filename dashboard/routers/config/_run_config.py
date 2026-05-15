"""Per-product run configuration: environments, browsers, devices, credentials, defaults.

Run config is stored in data/product_config/<product>.yaml (separate from main config.yaml
so 50+ products don't bloat the global config on every mutation).
"""
from __future__ import annotations

import json as _json

import yaml as _yaml
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse

from dashboard.routers.auth import get_session_user, require_user
from dashboard.routers.config._helpers import (
    _audit_config,
    _load_config,
    _product_entry as _find_product,
    templates,
)
from utils.paths import ROOT as _ROOT

router = APIRouter()

_PRODUCT_CONFIG_DIR = _ROOT / "data" / "product_config"


def _require_admin(current_user: dict = Depends(require_user)) -> dict:
    if not current_user.get("admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


# ── per-product run_config storage ────────────────────────────────────────────

def _load_rc(product: str) -> dict:
    path = _PRODUCT_CONFIG_DIR / f"{product}.yaml"
    if path.exists():
        data = _yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return data.get("run_config", {})
    # Fallback: migrate from legacy location in config.yaml
    cfg = _load_config()
    p = _find_product(cfg, product)
    return (p or {}).get("run_config", {})


def _save_rc(product: str, rc: dict) -> None:
    _PRODUCT_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    path = _PRODUCT_CONFIG_DIR / f"{product}.yaml"
    path.write_text(
        _yaml.dump({"run_config": rc}, default_flow_style=False, allow_unicode=True),
        encoding="utf-8",
    )


def _backfill_rc(rc: dict) -> dict:
    rc.setdefault("environments", [])
    rc.setdefault("browsers", [])
    rc.setdefault("devices", [])
    rc.setdefault("credentials", [])
    defaults = rc.setdefault("defaults", {})
    defaults.setdefault("environment", "")
    defaults.setdefault("browser", "")
    defaults.setdefault("device", "")
    defaults.setdefault("skip_quarantined", True)
    return rc


def _assert_product_exists(product: str) -> None:
    cfg = _load_config()
    if not _find_product(cfg, product):
        raise HTTPException(404, "Product not found")


def _render(request: Request, product: str, flash: str = "") -> HTMLResponse:
    _assert_product_exists(product)
    rc = _backfill_rc(_load_rc(product))
    current_user = get_session_user(request) or {}
    return templates.TemplateResponse(request, "partials/config_run_config.html", context={
        "request": request,
        "product": product,
        "rc": rc,
        "flash": flash,
        "current_user": current_user,
    })


# ── JSON endpoint for frontend fetch ─────────────────────────────────────────

@router.get("/api/config/run-config/{product}")
def run_config_json(product: str, _: dict = Depends(require_user)):
    _assert_product_exists(product)
    return _backfill_rc(_load_rc(product))


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
    _assert_product_exists(product)
    rc = _backfill_rc(_load_rc(product))
    name = name.strip()
    if not name:
        return _render(request, product, flash="Please select an environment.")
    if any(e["name"] == name for e in rc["environments"]):
        return _render(request, product, flash=f"Environment '{name}' already exists.")
    rc["environments"].append({"name": name, "base_url": base_url.strip(), "api_url": api_url.strip()})
    _save_rc(product, rc)
    _audit_config(request, "Run Configuration", f"[{product}] Added environment '{name}'")
    return _render(request, product, flash=f"Environment '{name}' added.")


@router.post("/ui/config/run-config/{product}/env/delete", response_class=HTMLResponse)
async def env_delete(
    request: Request, product: str, name: str = Form(...),
    _: dict = Depends(_require_admin),
):
    _assert_product_exists(product)
    rc = _backfill_rc(_load_rc(product))
    rc["environments"] = [e for e in rc["environments"] if e["name"] != name]
    if rc["defaults"].get("environment") == name:
        rc["defaults"]["environment"] = ""
    _save_rc(product, rc)
    _audit_config(request, "Run Configuration", f"[{product}] Deleted environment '{name}'")
    return _render(request, product)


# ── Browsers ──────────────────────────────────────────────────────────────────

@router.post("/ui/config/run-config/{product}/browser/add", response_class=HTMLResponse)
async def browser_add(
    request: Request, product: str,
    name: str = Form(...), browser: str = Form("chromium"), headless: str = Form("false"),
    _: dict = Depends(_require_admin),
):
    _assert_product_exists(product)
    rc = _backfill_rc(_load_rc(product))
    name = name.strip()
    if not name:
        return _render(request, product, flash="Please enter a browser profile name.")
    if any(b["name"] == name for b in rc["browsers"]):
        return _render(request, product, flash=f"Browser profile '{name}' already exists.")
    rc["browsers"].append({
        "name": name,
        "browser": browser,
        "headless": headless.lower() in ("true", "on", "1", "yes"),
    })
    _save_rc(product, rc)
    _audit_config(request, "Run Configuration", f"[{product}] Added browser profile '{name}'")
    return _render(request, product, flash=f"Browser profile '{name}' added.")


@router.post("/ui/config/run-config/{product}/browser/delete", response_class=HTMLResponse)
async def browser_delete(
    request: Request, product: str, name: str = Form(...),
    _: dict = Depends(_require_admin),
):
    _assert_product_exists(product)
    rc = _backfill_rc(_load_rc(product))
    rc["browsers"] = [b for b in rc["browsers"] if b["name"] != name]
    if rc["defaults"].get("browser") == name:
        rc["defaults"]["browser"] = ""
    _save_rc(product, rc)
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
    _assert_product_exists(product)
    rc = _backfill_rc(_load_rc(product))
    name = name.strip()
    if not name:
        return _render(request, product, flash="Please enter a device profile name.")
    if any(d["name"] == name for d in rc["devices"]):
        return _render(request, product, flash=f"Device profile '{name}' already exists.")
    try:
        caps = _json.loads(capabilities)
    except Exception:
        caps = {}
    rc["devices"].append({
        "name": name,
        "platform": platform,
        "appium_url": appium_url.strip(),
        "capabilities": caps,
    })
    _save_rc(product, rc)
    _audit_config(request, "Run Configuration", f"[{product}] Added device profile '{name}'")
    return _render(request, product, flash=f"Device profile '{name}' added.")


@router.post("/ui/config/run-config/{product}/device/delete", response_class=HTMLResponse)
async def device_delete(
    request: Request, product: str, name: str = Form(...),
    _: dict = Depends(_require_admin),
):
    _assert_product_exists(product)
    rc = _backfill_rc(_load_rc(product))
    rc["devices"] = [d for d in rc["devices"] if d["name"] != name]
    if rc["defaults"].get("device") == name:
        rc["defaults"]["device"] = ""
    _save_rc(product, rc)
    _audit_config(request, "Run Configuration", f"[{product}] Deleted device profile '{name}'")
    return _render(request, product)


# ── Credentials ───────────────────────────────────────────────────────────────

@router.post("/ui/config/run-config/{product}/credential/add", response_class=HTMLResponse)
async def credential_add(
    request: Request, product: str,
    name: str = Form(...), username: str = Form(""), password_env: str = Form(""),
    _: dict = Depends(_require_admin),
):
    _assert_product_exists(product)
    rc = _backfill_rc(_load_rc(product))
    name = name.strip()
    if not name:
        return _render(request, product, flash="Please enter a credential name.")
    if any(c["name"] == name for c in rc["credentials"]):
        return _render(request, product, flash=f"Credential '{name}' already exists.")
    rc["credentials"].append({
        "name": name,
        "username": username.strip(),
        "password_env": password_env.strip(),
    })
    _save_rc(product, rc)
    _audit_config(request, "Run Configuration", f"[{product}] Added credential '{name}'")
    return _render(request, product, flash=f"Credential '{name}' added.")


@router.post("/ui/config/run-config/{product}/credential/delete", response_class=HTMLResponse)
async def credential_delete(
    request: Request, product: str, name: str = Form(...),
    _: dict = Depends(_require_admin),
):
    _assert_product_exists(product)
    rc = _backfill_rc(_load_rc(product))
    rc["credentials"] = [c for c in rc["credentials"] if c["name"] != name]
    _save_rc(product, rc)
    _audit_config(request, "Run Configuration", f"[{product}] Deleted credential '{name}'")
    return _render(request, product)


# ── Toggle Defaults ───────────────────────────────────────────────────────────

@router.post("/ui/config/run-config/{product}/env/toggle-default", response_class=HTMLResponse)
async def env_toggle_default(
    request: Request, product: str, name: str = Form(...),
    _: dict = Depends(_require_admin),
):
    _assert_product_exists(product)
    rc = _backfill_rc(_load_rc(product))
    current = rc["defaults"].get("environment", "")
    rc["defaults"]["environment"] = "" if current == name else name
    _save_rc(product, rc)
    action = "Unset" if current == name else "Set"
    _audit_config(request, "Run Configuration", f"[{product}] {action} default environment '{name}'")
    return _render(request, product)


@router.post("/ui/config/run-config/{product}/browser/toggle-default", response_class=HTMLResponse)
async def browser_toggle_default(
    request: Request, product: str, name: str = Form(...),
    _: dict = Depends(_require_admin),
):
    _assert_product_exists(product)
    rc = _backfill_rc(_load_rc(product))
    current = rc["defaults"].get("browser", "")
    rc["defaults"]["browser"] = "" if current == name else name
    _save_rc(product, rc)
    action = "Unset" if current == name else "Set"
    _audit_config(request, "Run Configuration", f"[{product}] {action} default browser '{name}'")
    return _render(request, product)


@router.post("/ui/config/run-config/{product}/device/toggle-default", response_class=HTMLResponse)
async def device_toggle_default(
    request: Request, product: str, name: str = Form(...),
    _: dict = Depends(_require_admin),
):
    _assert_product_exists(product)
    rc = _backfill_rc(_load_rc(product))
    current = rc["defaults"].get("device", "")
    rc["defaults"]["device"] = "" if current == name else name
    _save_rc(product, rc)
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
    _assert_product_exists(product)
    rc = _backfill_rc(_load_rc(product))
    rc["defaults"] = {
        "environment": environment,
        "browser": browser,
        "device": device,
        "skip_quarantined": rc["defaults"].get("skip_quarantined", True),
    }
    _save_rc(product, rc)
    _audit_config(request, "Run Configuration", f"[{product}] Updated default profile")
    return _render(request, product, flash="Defaults saved.")


# ── Quarantine behavior ───────────────────────────────────────────────────────

@router.post("/ui/config/run-config/{product}/toggle-skip-quarantined", response_class=HTMLResponse)
async def toggle_skip_quarantined(
    request: Request, product: str,
    _: dict = Depends(_require_admin),
):
    _assert_product_exists(product)
    rc = _backfill_rc(_load_rc(product))
    current = rc["defaults"].get("skip_quarantined", True)
    rc["defaults"]["skip_quarantined"] = not current
    _save_rc(product, rc)
    verb = "enabled" if not current else "disabled"
    _audit_config(request, "Run Configuration", f"[{product}] Skip Quarantined Tests {verb}")
    return _render(request, product)
