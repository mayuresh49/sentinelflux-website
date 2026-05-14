"""Shared data helpers and path constants for the config subpackage."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

import yaml
from fastapi import APIRouter, Depends, HTTPException
from fastapi.templating import Jinja2Templates

from dashboard.routers.auth import require_user, user_products
from utils.paths import ROOT as _ROOT

templates = Jinja2Templates(directory=str(_ROOT / "dashboard" / "templates"))

_DATA_DIR = _ROOT / "data"
_CONFIG_PATH = _DATA_DIR / "config.yaml"
_ASSIGNMENTS_PATH = _DATA_DIR / "test_assignments.yaml"
_PRODUCTS_DIR = _ROOT / "products"
_KB_PRODUCTS_DIR = _ROOT / "ai" / "knowledge_base"
_SAFE_PRODUCT_RE = re.compile(r"^[a-zA-Z0-9_\-]+$")

_DEFAULT_GENERATION_CATEGORIES = {
    "functional": True,
    "negative": True,
    "edge": True,
    "security": True,
    "accessibility": False,
}


def _require_admin(current_user: dict = Depends(require_user)) -> dict:
    if not current_user.get("admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


# ── config load/save ──────────────────────────────────────────────────────────

def _load_config() -> dict:
    if _CONFIG_PATH.exists():
        cfg = yaml.safe_load(_CONFIG_PATH.read_text(encoding="utf-8")) or {}
        cats = cfg.setdefault("generation_categories", {})
        for k, v in _DEFAULT_GENERATION_CATEGORIES.items():
            cats.setdefault(k, v)
        cfg.setdefault("users", [])
        for u in cfg["users"]:
            u.setdefault("products", [])
            u.setdefault("admin", False)
            u.setdefault("password_hash", "")
        _backfill_products(cfg)
        return cfg
    cfg = {
        "labels": [],
        "priorities": [],
        "custom_fields": [],
        "test_type_distribution": {"sanity": 30, "regression": 70},
        "generation_categories": dict(_DEFAULT_GENERATION_CATEGORIES),
        "users": [],
        "products": [],
    }
    _backfill_products(cfg)
    return cfg


def _backfill_products(cfg: dict) -> None:
    cfg.setdefault("products", [])
    if not _KB_PRODUCTS_DIR.exists():
        return
    known = {p["name"] for p in cfg["products"]}
    skip = {"__pycache__", "increments"}
    for d in sorted(_KB_PRODUCTS_DIR.iterdir()):
        if d.is_dir() and d.name not in skip and d.name not in known:
            cfg["products"].append({
                "name": d.name,
                "display_name": d.name.replace("_", " ").title(),
                "active": True,
            })


def _save_config(cfg: dict) -> None:
    _CONFIG_PATH.write_text(yaml.dump(cfg, default_flow_style=False, allow_unicode=True), encoding="utf-8")


def _load_assignments() -> dict:
    if _ASSIGNMENTS_PATH.exists():
        data = yaml.safe_load(_ASSIGNMENTS_PATH.read_text(encoding="utf-8")) or {}
        return data.get("assignments", {})
    return {}


def _save_assignments(assignments: dict) -> None:
    _ASSIGNMENTS_PATH.write_text(
        "# Maps test function name -> label/priority/custom field assignments\n"
        "# Managed via dashboard Config > Test Assignments\n"
        + yaml.dump({"assignments": assignments}, default_flow_style=False, allow_unicode=True),
        encoding="utf-8",
    )


def _all_tests() -> list[dict]:
    results = []
    for py in _PRODUCTS_DIR.rglob("test_*.py"):
        parts = py.relative_to(_PRODUCTS_DIR).parts
        if len(parts) < 4 or parts[1] != "tests":
            continue
        p, d = parts[0], parts[2]
        try:
            for fn in re.findall(r"^def (test_\w+)", py.read_text(encoding="utf-8"), re.MULTILINE):
                results.append({"name": fn, "product": p, "domain": d})
        except OSError:
            pass
    return sorted(results, key=lambda x: (x["product"], x["domain"], x["name"]))


def assignments_summary_by_feature() -> dict:
    """Return {product/domain/feature: {labels, priorities, assigned, total}} for dashboard overlays."""
    assignments = _load_assignments()
    cfg = _load_config()
    label_colors = {l["name"]: l["color"] for l in cfg.get("labels", [])}
    priority_colors = {p["name"]: p["color"] for p in cfg.get("priorities", [])}
    result = {}
    for py in _PRODUCTS_DIR.rglob("test_*.py"):
        parts = py.relative_to(_PRODUCTS_DIR).parts
        if len(parts) < 4 or parts[1] != "tests":
            continue
        product, domain = parts[0], parts[2]
        feature = py.stem[5:]
        try:
            fns = re.findall(r"^def (test_\w+)", py.read_text(encoding="utf-8"), re.MULTILINE)
        except OSError:
            continue
        labels: dict[str, str] = {}
        priorities: dict[str, str] = {}
        assigned = 0
        for fn in fns:
            asgn = assignments.get(fn, {})
            if asgn:
                assigned += 1
                for lbl in asgn.get("labels", []):
                    labels[lbl] = label_colors.get(lbl, "slate")
                if asgn.get("priority"):
                    pr = asgn["priority"]
                    priorities[pr] = priority_colors.get(pr, "slate")
        result[f"{product}/{domain}/{feature}"] = {
            "labels": [{"name": k, "color": v} for k, v in labels.items()],
            "priorities": [{"name": k, "color": v} for k, v in priorities.items()],
            "assigned": assigned,
            "total": len(fns),
        }
    return result


def get_test_type_for_index(index: int, total: int, cfg: dict | None = None) -> str:
    if cfg is None:
        cfg = _load_config()
    dist = cfg.get("test_type_distribution", {})
    sanity_pct = dist.get("sanity", 30)
    sanity_count = max(1, round(total * sanity_pct / 100))
    return "sanity" if index < sanity_count else "regression"


def get_generation_categories_instruction(cfg: dict | None = None) -> str:
    if cfg is None:
        cfg = _load_config()
    cats = cfg.get("generation_categories", _DEFAULT_GENERATION_CATEGORIES)
    _LABELS = {
        "functional": "positive / happy-path functional tests",
        "negative": "negative tests (invalid input, missing fields, error paths)",
        "edge": "edge cases (boundary values, optional fields, limits)",
        "security": "security tests (auth, access control, injection, sensitive data)",
        "accessibility": "accessibility tests (ARIA, keyboard navigation, screen-reader compatibility)",
    }
    enabled = [_LABELS[k] for k in _LABELS if cats.get(k, False)]
    disabled = [_LABELS[k] for k in _LABELS if not cats.get(k, False)]
    lines = ["- Test categories to generate (STRICTLY follow this — do not add categories not listed here):"]
    lines.append(f"  INCLUDE: {', '.join(enabled) if enabled else 'none'}")
    if disabled:
        lines.append(f"  EXCLUDE (do not generate): {', '.join(disabled)}")
    return "\n".join(lines)


def get_generation_type_instruction(cfg: dict | None = None) -> str:
    if cfg is None:
        cfg = _load_config()
    dist = cfg.get("test_type_distribution", {})
    sanity_pct = dist.get("sanity", 30)
    regression_pct = dist.get("regression", 70)
    return (
        f"- Test type markers: add @pytest.mark.sanity OR @pytest.mark.regression to every test function "
        f"(in addition to the domain marker). "
        f"Judge by business importance: mark core happy-paths and business-critical flows as "
        f"@pytest.mark.sanity (~{sanity_pct}% of tests). "
        f"Mark edge cases, error paths, and boundary checks as @pytest.mark.regression "
        f"(~{regression_pct}% of tests). "
        f"Importance — not sequential position — determines the label. "
        f"Every generated test must have exactly one of these two markers."
    )
