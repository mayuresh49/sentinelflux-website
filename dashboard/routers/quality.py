from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends

from core.activity_log import ActivityLog
from core.db import get_conn
from dashboard.routers.auth import require_user, user_products
from utils.paths import ROOT as _ROOT_DIR

router = APIRouter(prefix="/quality", tags=["quality"])
_PRODUCTS_DIR = _ROOT_DIR / "products"
_KB_DIR = _ROOT_DIR / "ai" / "knowledge_base"
_SKIP_KB = {"__pycache__", "increments"}

_alog = ActivityLog()


def _all_products() -> list[str]:
    from dashboard.routers.kb import _list_products
    return _list_products()


def _script_features(product: str) -> set[str]:
    base = _PRODUCTS_DIR / product / "tests"
    if not base.exists():
        return set()
    return {py.stem.removeprefix("test_") for py in base.rglob("test_*.py")}


def _scripts_by_domain(product: str) -> dict[str, int]:
    base = _PRODUCTS_DIR / product / "tests"
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
    base = _PRODUCTS_DIR / product / "docs" / "test_cases"
    if not base.exists():
        return set()
    return {md.stem for md in base.rglob("*.md") if md.stem != "README"}


def _count_test_functions(product: str) -> int:
    base = _PRODUCTS_DIR / product / "tests"
    if not base.exists():
        return 0
    count = 0
    for py in base.rglob("test_*.py"):
        try:
            count += len(re.findall(r"^def (test_\w+)", py.read_text(encoding="utf-8"), re.MULTILINE))
        except OSError:
            pass
    return count


def _load_quarantine() -> list:
    rows = get_conn().execute("SELECT * FROM quarantine").fetchall()
    return [dict(r) for r in rows]


def _run_stats_from_db(products: list[str], days: int = 7) -> dict:
    """Aggregate actual pytest results from test_runs table."""
    if not products:
        return {"total": 0, "passed": 0, "failed": 0, "skipped": 0, "errors": 0, "duration": 0.0, "pass_rate": None}
    conn = get_conn()
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    ph = ",".join("?" * len(products))
    rows = conn.execute(
        f"SELECT total, passed, failed, skipped, errors, duration FROM test_runs "
        f"WHERE product IN ({ph}) AND triggered_at >= ? AND status = 'completed' AND total > 0",
        (*products, cutoff)
    ).fetchall()
    if not rows:
        return {"total": 0, "passed": 0, "failed": 0, "skipped": 0, "errors": 0, "duration": 0.0, "pass_rate": None}
    total = sum(r["total"] for r in rows)
    passed = sum(r["passed"] for r in rows)
    failed = sum(r["failed"] for r in rows)
    skipped = sum(r["skipped"] for r in rows)
    errors = sum(r["errors"] for r in rows)
    duration = sum(r["duration"] for r in rows)
    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "errors": errors,
        "duration": round(duration, 1),
        "pass_rate": round(passed / total * 100) if total > 0 else None,
    }


def _daily_pass_rate_from_runs(products: list[str], days: int = 7) -> list:
    """7-day pass rate trend from actual test_runs, one value per day."""
    if not products:
        return [None] * days
    conn = get_conn()
    now = datetime.now(timezone.utc)
    ph = ",".join("?" * len(products))
    trend = []
    for d in range(days - 1, -1, -1):
        day_start = (now - timedelta(days=d)).replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        row = conn.execute(
            f"SELECT SUM(passed) AS p, SUM(total) AS t FROM test_runs "
            f"WHERE product IN ({ph}) AND triggered_at >= ? AND triggered_at < ? "
            f"AND status = 'completed' AND total > 0",
            (*products, day_start.isoformat(), day_end.isoformat())
        ).fetchone()
        if row and row["t"]:
            trend.append(round(row["p"] / row["t"] * 100))
        else:
            trend.append(None)
    return trend


def _risk_score(pass_rate: int | None, quarantined: int, total_fns: int, doc_coverage: int, flaky: int) -> int:
    """Composite risk 0–100: pass rate (50pts) + quarantine rate (20pts) + doc gap (20pts) + flaky (10pts)."""
    score = (100 - pass_rate) * 0.5 if pass_rate is not None else 25.0
    if total_fns > 0:
        score += min(quarantined / total_fns * 100 * 0.4, 20)
    score += (100 - doc_coverage) * 0.2
    score += min(flaky * 2, 10)
    return round(min(score, 100))


def compute_metrics(product: str | None = None, allowed_products: list[str] | None = None) -> dict:
    all_prods = allowed_products if allowed_products is not None else _all_products()
    scope = [product] if (product and product in all_prods) else all_prods

    quarantined = _load_quarantine()
    all_entries = _alog.all()

    per_product: list[dict] = []

    for p in scope:
        scripts = _script_features(p)
        docs = _doc_features(p)
        documented = scripts & docs
        by_domain = _scripts_by_domain(p)
        test_fns = _count_test_functions(p)
        run_stats = _run_stats_from_db([p])
        p_quarantined = [q for q in quarantined if q.get("product") == p]
        p_entries = [e for e in all_entries if e.get("product") == p and e.get("agent") != "human"]
        flaky = len([e for e in p_entries if e.get("agent") == "flaky_detector"])
        doc_coverage = round(len(documented) / len(scripts) * 100) if scripts else 0

        per_product.append({
            "product": p,
            "scripts": len(scripts),
            "test_functions": test_fns,
            "scripts_by_domain": by_domain,
            "docs": len(docs),
            "documented": len(documented),
            "doc_coverage": doc_coverage,
            "quarantined": len(p_quarantined),
            "pass_rate": run_stats["pass_rate"],
            "executed": run_stats["total"],
            "passed": run_stats["passed"],
            "failed": run_stats["failed"],
            "skipped": run_stats["skipped"],
            "duration": run_stats["duration"],
            "flaky": flaky,
            "risk_score": _risk_score(run_stats["pass_rate"], len(p_quarantined), test_fns, doc_coverage, flaky),
            "scripts_with_docs": len(documented),
        })

    total_scripts = sum(r["scripts"] for r in per_product)
    total_test_fns = sum(r["test_functions"] for r in per_product)
    total_scripts_by_domain: dict[str, int] = {}
    for r in per_product:
        for d, n in r["scripts_by_domain"].items():
            total_scripts_by_domain[d] = total_scripts_by_domain.get(d, 0) + n
    total_docs = sum(r["docs"] for r in per_product)
    total_documented = sum(r["documented"] for r in per_product)
    total_doc_coverage = round(total_documented / total_scripts * 100) if total_scripts else 0
    total_quarantined = sum(r["quarantined"] for r in per_product)
    total_flaky = sum(r["flaky"] for r in per_product)

    global_runs = _run_stats_from_db(scope)
    avg_pass = global_runs["pass_rate"]
    overall_risk = _risk_score(avg_pass, total_quarantined, total_test_fns, total_doc_coverage, total_flaky)

    return {
        "summary": {
            "scripts": total_scripts,
            "test_functions": total_test_fns,
            "scripts_by_domain": total_scripts_by_domain,
            "docs": total_docs,
            "documented": total_documented,
            "doc_coverage": total_doc_coverage,
            "quarantined": total_quarantined,
            "pass_rate": avg_pass,
            "executed": global_runs["total"],
            "passed": global_runs["passed"],
            "failed": global_runs["failed"],
            "skipped": global_runs["skipped"],
            "duration": global_runs["duration"],
            "pass_rate_trend": _daily_pass_rate_from_runs(scope),
            "flaky": total_flaky,
            "risk_score": overall_risk,
        },
        "per_product": per_product,
        "all_products": all_prods,
        "filter_product": product or "",
    }


def _all_test_functions() -> list[dict]:
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


@router.get("/")
def get_quality(product: str | None = None, current_user: dict = Depends(require_user)):
    visible = user_products(current_user, _all_products())
    if product and product not in visible:
        product = None
    return compute_metrics(product, allowed_products=visible)
