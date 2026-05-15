"""User management routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse

from dashboard.routers.config._helpers import _audit_config, _load_config, _require_admin, _save_config, templates

router = APIRouter()


def _render_users(request: Request, cfg: dict) -> HTMLResponse:
    return templates.TemplateResponse(request, "partials/config_users.html", context={
        "request": request,
        "users": cfg.get("users", []),
        "all_products": [p["name"] for p in cfg.get("products", []) if p.get("active", True)],
    })


@router.post("/ui/config/users/add", response_class=HTMLResponse)
async def users_add(request: Request, name: str = Form(...), email: str = Form(""),
                    _: dict = Depends(_require_admin)):
    cfg = _load_config()
    name = name.strip()
    email = email.strip().lower()
    if name and not any(u["name"] == name for u in cfg.get("users", [])):
        cfg.setdefault("users", []).append({
            "name": name, "email": email,
            "products": [], "admin": False, "password_hash": "",
        })
        _save_config(cfg)
        _audit_config(request, "User Management", f"Added user '{name}' ({email})")
    return _render_users(request, cfg)


@router.post("/ui/config/users/delete", response_class=HTMLResponse)
async def users_delete(request: Request, name: str = Form(...), _: dict = Depends(_require_admin)):
    cfg = _load_config()
    cfg["users"] = [u for u in cfg.get("users", []) if u["name"] != name]
    _save_config(cfg)
    _audit_config(request, "User Management", f"Removed user '{name}'")
    return _render_users(request, cfg)


@router.post("/ui/config/users/set-password", response_class=HTMLResponse)
async def users_set_password(request: Request, name: str = Form(...), password: str = Form(...),
                             _: dict = Depends(_require_admin)):
    import bcrypt as _bcrypt
    cfg = _load_config()
    for u in cfg.get("users", []):
        if u["name"] == name:
            u["password_hash"] = (
                _bcrypt.hashpw(password.strip().encode(), _bcrypt.gensalt()).decode()
                if password.strip() else ""
            )
            break
    _save_config(cfg)
    _audit_config(request, "User Management", f"{'Set' if password.strip() else 'Cleared'} password for '{name}'")
    return _render_users(request, cfg)


@router.post("/ui/config/users/set-admin", response_class=HTMLResponse)
async def users_set_admin(request: Request, name: str = Form(...),
                          admin: str = Form(default=""), _: dict = Depends(_require_admin)):
    cfg = _load_config()
    for u in cfg.get("users", []):
        if u["name"] == name:
            u["admin"] = admin == "on"
            break
    _save_config(cfg)
    _audit_config(request, "User Management", f"{'Granted' if admin == 'on' else 'Revoked'} admin role for '{name}'")
    return _render_users(request, cfg)


@router.post("/ui/config/users/set-products", response_class=HTMLResponse)
async def users_set_products(request: Request, _: dict = Depends(_require_admin)):
    form = await request.form()
    name = form.get("name", "")
    products = form.getlist("products")
    cfg = _load_config()
    for u in cfg.get("users", []):
        if u["name"] == name:
            u["products"] = products
            break
    _save_config(cfg)
    _audit_config(request, "User Management",
                  f"Updated product access for '{name}': {', '.join(products) or 'none'}")
    return _render_users(request, cfg)
