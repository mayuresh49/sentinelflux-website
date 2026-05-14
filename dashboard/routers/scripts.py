from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException

from utils.paths import ROOT as _ROOT_DIR

router = APIRouter(prefix="/scripts", tags=["scripts"])
_EXAMPLES_DIR = _ROOT_DIR / "examples"


def _find_scripts(product: str | None = None, domain: str | None = None) -> list[dict]:
    results = []
    for py in _EXAMPLES_DIR.rglob("test_*.py"):
        parts = py.relative_to(_EXAMPLES_DIR).parts
        # Expected: <product>/tests/<domain>/test_<feature>.py
        if len(parts) < 4 or parts[1] != "tests":
            continue
        p, _, d, fname = parts[0], parts[1], parts[2], parts[3]
        if product and p != product:
            continue
        if domain and d != domain:
            continue
        results.append({
            "product": p,
            "domain": d,
            "feature": fname.removesuffix(".py").removeprefix("test_"),
            "path": str(py.relative_to(_ROOT_DIR)),
        })
    return results


@router.get("/")
def list_scripts(product: str | None = None, domain: str | None = None):
    scripts = _find_scripts(product, domain)
    return {"scripts": scripts, "total": len(scripts)}


@router.get("/{product}/{domain}/{feature}")
def get_script(product: str, domain: str, feature: str):
    path = _EXAMPLES_DIR / product / "tests" / domain / f"test_{feature}.py"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Script not found")
    return {
        "product": product,
        "domain": domain,
        "feature": feature,
        "content": path.read_text(encoding="utf-8"),
        "path": str(path.relative_to(_ROOT_DIR)),
    }
