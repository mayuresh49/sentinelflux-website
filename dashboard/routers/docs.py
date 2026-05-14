from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException

from utils.paths import ROOT as _ROOT_DIR

router = APIRouter(prefix="/docs", tags=["docs"])
_PRODUCTS_DIR = _ROOT_DIR / "products"


def _find_docs(product: str | None = None, domain: str | None = None) -> list[dict]:
    results = []
    for md in _PRODUCTS_DIR.rglob("*.md"):
        parts = md.relative_to(_PRODUCTS_DIR).parts
        # Expected: <product>/docs/test_cases/<domain>/<feature>.md
        if len(parts) < 5 or parts[1] != "docs" or parts[2] != "test_cases":
            continue
        p, _, _, d, fname = parts[0], parts[1], parts[2], parts[3], parts[4]
        if product and p != product:
            continue
        if domain and d != domain:
            continue
        results.append({
            "product": p,
            "domain": d,
            "feature": fname.removesuffix(".md"),
            "path": str(md.relative_to(_ROOT_DIR)),
        })
    return results


@router.get("/")
def list_docs(product: str | None = None, domain: str | None = None):
    docs = _find_docs(product, domain)
    return {"docs": docs, "total": len(docs)}


@router.get("/{product}/{domain}/{feature}")
def get_doc(product: str, domain: str, feature: str):
    path = _PRODUCTS_DIR / product / "docs" / "test_cases" / domain / f"{feature}.md"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Doc not found")
    return {
        "product": product,
        "domain": domain,
        "feature": feature,
        "content": path.read_text(encoding="utf-8"),
        "path": str(path.relative_to(_ROOT_DIR)),
    }
