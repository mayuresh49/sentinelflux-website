from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml
from fastapi import APIRouter

from utils.activity_log import ActivityLog

router = APIRouter(prefix="/quality", tags=["quality"])

_ROOT_DIR = Path(__file__).resolve().parent.parent.parent
_EXAMPLES_DIR = _ROOT_DIR / "examples"
_KB_DIR = _ROOT_DIR / "ai" / "knowledge_base"
_QUARANTINE_FILE = _ROOT_DIR / "framework_knowledge" / "quarantine.yaml"
_SKIP_KB = {"__pycache__", "increments"}

_alog = ActivityLog()


def _all_products() -> list[str]:
    from dashboard.routers.kb import _list_products
    return _list_products()


def _script_features(product: str) -> set[str]:
    base = _EXAMPLES_DIR / product / "tests"
    if not base.exists():
        return set()
    return {py.stem.removeprefix("test_") for py in base.rglob("test_*.py")}


def _scripts_by_domain(product: str) -> dict[str, int]:
    base = _EXAMPLES_DIR / product / "tests"
    if not base.exists():
        return {}
    counts: dict[str, int] = {}
    for py in base.rglob("test_*.py"):
        parts = py.relative_to(base).parts
        if len(parts) >= 2:
            domain = parts[0]
            counts[domain] = counts.get(domain, 0) + 1
    return counts


def _doc_features(product: str) -> set[str]:
    base = _EXAMPLES_DIR / product / "docs" / "test_cases"
    if not base.exists():
        return set()
    return {md.stem for md in base.rglob("*.md") if md.stem != "README"}


def _load_quarantine() -> list:
    if not _QUARANTINE_FILE.exists():
        return []
    data = yaml.safe_load(_QUARANTINE_FILE.read_text(encoding="utf-8")) or {}
    return data.get("quarantined", [])


def _parse_ts(ts: str) -> datetime:
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except Exception:
        return datetime.min.replace(tzinfo=timezone.utc)


def compute_metrics(product: str | None = None) -> dict:
    all_prods = _all_products()
    scope = [product] if (product and product in all_prods) else all_prods

    all_entries = _alog.all()
    quarantined = _load_quarantine()
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)

    per_product: list[dict] = []

    for p in scope:
        scripts = _script_features(p)
        docs = _doc_features(p)
        documented = scripts & docs
        by_domain = _scripts_by_domain(p)

        p_entries = [e for e in all_entries if e.get("product") == p and e.get("agent") != "human"]
        recent = [e for e in p_entries if _parse_ts(e.get("timestamp", "")) > cutoff]
        runs_total = len([e for e in recent if e.get("status") in ("success", "failure", "error")])
        runs_success = len([e for e in recent if e.get("status") == "success"])
        flaky = len([e for e in p_entries if e.get("agent") == "flaky_detector"])
        p_quarantined = [q for q in quarantined if q.get("product") == p]

        per_product.append({
            "product": p,
            "scripts": len(scripts),
            "scripts_by_domain": by_domain,
            "docs": len(docs),
            "documented": len(documented),
            "doc_coverage": round(len(documented) / len(scripts) * 100) if scripts else 0,
            "quarantined": len(p_quarantined),
            "pass_rate": round(runs_success / runs_total * 100) if runs_total else None,
            "flaky": flaky,
        })

    total_scripts = sum(r["scripts"] for r in per_product)
    total_scripts_by_domain: dict[str, int] = {}
    for r in per_product:
        for d, n in r["scripts_by_domain"].items():
            total_scripts_by_domain[d] = total_scripts_by_domain.get(d, 0) + n
    total_docs = sum(r["docs"] for r in per_product)
    total_documented = sum(r["documented"] for r in per_product)
    total_runs = sum(r["pass_rate"] is not None and 1 or 0 for r in per_product)
    avg_pass = (
        round(sum(r["pass_rate"] for r in per_product if r["pass_rate"] is not None) / total_runs)
        if total_runs else None
    )

    return {
        "summary": {
            "scripts": total_scripts,
            "scripts_by_domain": total_scripts_by_domain,
            "docs": total_docs,
            "doc_coverage": round(total_documented / total_scripts * 100) if total_scripts else 0,
            "quarantined": len(quarantined),
            "pass_rate": avg_pass,
            "flaky": sum(r["flaky"] for r in per_product),
        },
        "per_product": per_product,
        "all_products": all_prods,
        "filter_product": product or "",
    }


def _all_test_functions() -> list[dict]:
    results = []
    for py in _EXAMPLES_DIR.rglob("test_*.py"):
        parts = py.relative_to(_EXAMPLES_DIR).parts
        if len(parts) < 4 or parts[1] != "tests":
            continue
        p, d = parts[0], parts[2]
        try:
            for fn in re.findall(r"^def (test_\w+)", py.read_text(encoding="utf-8"), re.MULTILINE):
                results.append({"name": fn, "product": p, "domain": d})
        except OSError:
            pass
    return sorted(results, key=lambda x: (x["product"], x["domain"], x["name"]))


@router.get("/")
def get_quality(product: str | None = None):
    return compute_metrics(product)
