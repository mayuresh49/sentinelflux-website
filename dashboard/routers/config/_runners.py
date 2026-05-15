"""Runner token management — admin-only CRUD for machine-to-machine runner auth."""
from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timezone

import yaml
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from dashboard.routers.config._helpers import _audit_config, _load_config, _require_admin
from utils.paths import ROOT as _ROOT

router = APIRouter()

_CONFIG_PATH = _ROOT / "data" / "config.yaml"


# ── helpers ───────────────────────────────────────────────────────────────────

def _load_tokens(cfg: dict) -> list[dict]:
    return cfg.setdefault("runner_tokens", [])


def _save_config_file(cfg: dict) -> None:
    _CONFIG_PATH.write_text(
        yaml.dump(cfg, default_flow_style=False, allow_unicode=True),
        encoding="utf-8",
    )


# ── Pydantic bodies ───────────────────────────────────────────────────────────

class CreateTokenBody(BaseModel):
    name: str
    products: list[str] = []   # empty = allowed for all products


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/api/config/runner-tokens")
def list_runner_tokens(admin: dict = Depends(_require_admin)):
    """List all runner tokens (token hashes only, never plain-text)."""
    cfg = _load_config()
    tokens = _load_tokens(cfg)
    return {"tokens": [_safe(t) for t in tokens]}


@router.post("/api/config/runner-tokens")
def create_runner_token(body: CreateTokenBody, request=None, admin: dict = Depends(_require_admin)):
    """Create a new runner token. The plain token is returned ONCE — store it securely."""
    import bcrypt
    name = body.name.strip()
    if not name:
        raise HTTPException(400, "Token name is required")

    plain = f"sfr_{secrets.token_urlsafe(32)}"
    hashed = bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()

    token = {
        "id": f"rt_{uuid.uuid4().hex[:12]}",
        "name": name,
        "token_hash": hashed,
        "products": body.products,
        "enabled": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    cfg = _load_config()
    _load_tokens(cfg).append(token)
    _save_config_file(cfg)

    return {"token": _safe(token), "plain_token": plain}


@router.post("/api/config/runner-tokens/{token_id}/toggle")
def toggle_runner_token(token_id: str, admin: dict = Depends(_require_admin)):
    cfg = _load_config()
    tokens = _load_tokens(cfg)
    t = next((t for t in tokens if t["id"] == token_id), None)
    if not t:
        raise HTTPException(404, "Token not found")
    t["enabled"] = not t.get("enabled", True)
    _save_config_file(cfg)
    return {"token": _safe(t)}


@router.delete("/api/config/runner-tokens/{token_id}")
def delete_runner_token(token_id: str, admin: dict = Depends(_require_admin)):
    cfg = _load_config()
    tokens = _load_tokens(cfg)
    new = [t for t in tokens if t["id"] != token_id]
    if len(new) == len(tokens):
        raise HTTPException(404, "Token not found")
    cfg["runner_tokens"] = new
    _save_config_file(cfg)
    return {"ok": True}


def _safe(t: dict) -> dict:
    """Strip token_hash before returning to client."""
    return {k: v for k, v in t.items() if k != "token_hash"}
