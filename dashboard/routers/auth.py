from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import bcrypt as _bcrypt
import yaml as _yaml
from fastapi import APIRouter, Form, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from utils.paths import ROOT as _ROOT

router = APIRouter(tags=["auth"])
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))


def _hash_password(password: str) -> str:
    return _bcrypt.hashpw(password.encode(), _bcrypt.gensalt()).decode()


def _verify_password(password: str, hashed: str) -> bool:
    try:
        return _bcrypt.checkpw(password.encode(), hashed.encode())
    except Exception:
        return False

_DATA_DIR = _ROOT / "data"
_CONFIG_PATH = _DATA_DIR / "config.yaml"


def _load_users() -> list[dict]:
    import yaml
    if not _CONFIG_PATH.exists():
        return []
    cfg = yaml.safe_load(_CONFIG_PATH.read_text(encoding="utf-8")) or {}
    return cfg.get("users", [])


def get_session_user(request: Request) -> dict | None:
    """Return the logged-in user dict, or None if not authenticated."""
    email = request.session.get("user_email")
    if not email:
        return None
    return next((u for u in _load_users() if u.get("email") == email), None)


def require_user(request: Request) -> dict:
    """FastAPI dependency — redirects to /login if not authenticated."""
    user = get_session_user(request)
    if user is None:
        # raise a redirect; caller catches it via exception handler
        from fastapi import HTTPException
        raise HTTPException(status_code=307, headers={"Location": "/login"})
    return user


def user_products(user: dict, all_products: list[str]) -> list[str]:
    """Return the product list visible to this user."""
    if user.get("admin"):
        return all_products
    assigned = user.get("products") or []
    # keep filesystem order, filter to assigned
    return [p for p in all_products if p in assigned]


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, next_url: str = Query(default="/", alias="next")):
    if get_session_user(request):
        return RedirectResponse(next_url, status_code=302)
    return templates.TemplateResponse(request, "login.html", {"error": None, "next": next_url})


@router.post("/login", response_class=HTMLResponse)
async def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    next_url: str = Form(default="/", alias="next"),
):
    users = _load_users()
    matched = next((u for u in users if u.get("email", "").lower() == email.strip().lower()), None)

    if not matched:
        return templates.TemplateResponse(request, "login.html",
                                          {"error": "Invalid email or password.", "next": next_url})

    pw_hash = matched.get("password_hash", "")
    if not pw_hash:
        return templates.TemplateResponse(request, "login.html",
                                          {"error": "Account has no password set. Ask an admin to set one.", "next": next_url})

    if not _verify_password(password, pw_hash):
        return templates.TemplateResponse(request, "login.html",
                                          {"error": "Invalid email or password.", "next": next_url})

    request.session["user_email"] = matched["email"]

    # Persist last login timestamp
    try:
        cfg_data = _yaml.safe_load(_CONFIG_PATH.read_text(encoding="utf-8")) or {}
        for _u in cfg_data.get("users", []):
            if _u.get("email", "").lower() == matched["email"].lower():
                _u["last_login_at"] = datetime.now(timezone.utc).isoformat()
                break
        _CONFIG_PATH.write_text(
            _yaml.dump(cfg_data, default_flow_style=False, allow_unicode=True),
            encoding="utf-8",
        )
    except Exception:
        pass

    # Audit
    try:
        from core.audit_logger import log as _audit
        _audit(
            "login", matched["email"], matched.get("name", ""),
            f"Logged in",
            ip=request.client.host if request.client else "",
        )
    except Exception:
        pass

    return RedirectResponse(next_url if next_url.startswith("/") else "/", status_code=302)


@router.get("/logout")
async def logout(request: Request):
    try:
        user = get_session_user(request)
        if user:
            from core.audit_logger import log as _audit
            _audit(
                "logout", user["email"], user.get("name", ""),
                "Logged out",
                ip=request.client.host if request.client else "",
            )
    except Exception:
        pass
    request.session.clear()
    return RedirectResponse("/login", status_code=302)
