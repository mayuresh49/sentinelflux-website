from __future__ import annotations

import re

from fastapi import APIRouter, HTTPException

from utils.paths import ROOT as _ROOT_DIR

router = APIRouter(prefix="/docs", tags=["docs"])
_PRODUCTS_DIR = _ROOT_DIR / "products"


def _parse_tc_index(content: str) -> list[dict]:
    """Parse the index table from a test case doc and return structured TC list."""
    tcs: list[dict] = []
    in_table = False
    for line in content.splitlines():
        stripped = line.strip()
        if re.match(r'\|\s*ID\s*\|', stripped, re.IGNORECASE):
            in_table = True
            continue
        if not in_table:
            continue
        if stripped.startswith("|---") or stripped.startswith("| ---"):
            continue
        if not stripped.startswith("|"):
            break
        parts = [p.strip() for p in stripped.strip("|").split("|")]
        if len(parts) >= 6 and parts[0] and not parts[0].startswith("---"):
            tcs.append({
                "id": parts[0], "title": parts[1], "heuristic": parts[2],
                "test_type": parts[3], "status": parts[4], "script": parts[5],
            })
        elif len(parts) >= 5 and parts[0] and not parts[0].startswith("---"):
            tcs.append({
                "id": parts[0], "title": parts[1], "heuristic": parts[2],
                "test_type": "", "status": parts[3], "script": parts[4],
            })
    return tcs


def _parse_tc_block(content: str, tc_id: str) -> str | None:
    """Extract the ### TC-ID block from the test cases section (handles varied headings)."""
    detail_match = re.search(r'^##\s+(Detailed\s+)?Test Cases', content, re.MULTILINE | re.IGNORECASE)
    if not detail_match:
        # Fall back: search entire document for the ### block
        section = content
    else:
        section = content[detail_match.end():]
    pattern = rf'^(###\s+{re.escape(tc_id)}\b[^\n]*\n(?:(?!^###)[\s\S])*)'
    match = re.search(pattern, section, re.MULTILINE)
    return match.group(1).strip() if match else None


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
