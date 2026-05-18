"""Performance testing module — load/stress/spike/soak test execution with httpx + asyncio."""
from __future__ import annotations

import asyncio
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel

from core.perf_manager import PerfManager
from dashboard.routers.auth import require_user, user_products
from dashboard.routers.config._helpers import _load_config, _require_admin

router = APIRouter(tags=["perf"])

_ROOT = Path(__file__).resolve().parent.parent.parent
_pm = PerfManager()

_PROFILE_TYPES = ("load", "stress", "spike", "soak")


def _perf_products(current_user: dict) -> list[str]:
    cfg = _load_config()
    all_prods = [p["name"] for p in cfg.get("products", []) if p.get("perf_enabled")]
    return user_products(current_user, all_prods)


def _check_product_access(product: str, current_user: dict) -> None:
    if product not in _perf_products(current_user):
        raise HTTPException(403, detail="Access denied or performance testing not enabled for this product")


# ── Pydantic models ───────────────────────────────────────────────────────────

class CreateEngBody(BaseModel):
    product: str
    name: str
    target_url: str


class EndpointSpec(BaseModel):
    method: str = "GET"
    path: str
    expected_status: int = 200
    body: dict | None = None
    headers: dict[str, str] = {}


class ProfileBody(BaseModel):
    profile_id: str | None = None
    type: str = "load"
    vus: int = 10
    duration_s: int = 60
    ramp_up_s: int = 10
    endpoints: list[EndpointSpec] = []
    thresholds: dict[str, float] = {"p95_ms": 2000.0, "error_rate_pct": 5.0}


# ── helper: PDF ───────────────────────────────────────────────────────────────

def _to_pdf(html: str) -> bytes | None:
    try:
        from weasyprint import HTML
        import jinja2
        env = jinja2.Environment(autoescape=True,
                                 loader=jinja2.FileSystemLoader(
                                     str(_ROOT / "dashboard" / "templates")))
        return HTML(string=html).write_pdf()
    except Exception:
        try:
            from weasyprint import HTML
            return HTML(string=html).write_pdf()
        except Exception:
            return None


def _render_report_html(eng: dict) -> str:
    from jinja2 import Environment, FileSystemLoader
    env = Environment(autoescape=True,
                      loader=FileSystemLoader(str(_ROOT / "dashboard" / "templates")))
    tpl = env.get_template("perf_report_pdf.html")
    runs_with_profile = []
    profiles_by_id = {p["profile_id"]: p for p in eng.get("profiles", [])}
    for r in eng.get("runs", []):
        runs_with_profile.append({**r, "profile": profiles_by_id.get(r.get("profile_id"), {})})
    return tpl.render(eng=eng, runs=runs_with_profile,
                      generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))


# ── engagement CRUD ───────────────────────────────────────────────────────────

@router.post("/perf/engagements")
def create_engagement(body: CreateEngBody,
                      current_user: dict = Depends(require_user)) -> dict:
    _check_product_access(body.product, current_user)
    return _pm.create(body.product, body.name, body.target_url,
                      current_user.get("name", "unknown"))


@router.get("/perf/engagements")
def list_engagements(product: str,
                     current_user: dict = Depends(require_user)) -> list[dict]:
    _check_product_access(product, current_user)
    return _pm.list_engagements(product)


@router.get("/perf/engagement/{eng_id}")
def get_engagement(eng_id: str, product: str,
                   current_user: dict = Depends(require_user)) -> dict:
    _check_product_access(product, current_user)
    eng = _pm.get(product, eng_id)
    if not eng:
        raise HTTPException(404, detail="Engagement not found")
    return eng


@router.delete("/perf/engagement/{eng_id}")
def delete_engagement(eng_id: str, product: str,
                      _: dict = Depends(_require_admin)) -> dict:
    if not _pm.delete(product, eng_id):
        raise HTTPException(404, detail="Engagement not found")
    return {"deleted": True}


# ── profile management ────────────────────────────────────────────────────────

@router.put("/perf/engagement/{eng_id}/profile")
def upsert_profile(eng_id: str, product: str, body: ProfileBody,
                   current_user: dict = Depends(require_user)) -> dict:
    _check_product_access(product, current_user)
    eng = _pm.upsert_profile(product, eng_id, body.model_dump())
    if not eng:
        raise HTTPException(404, detail="Engagement not found")
    return eng


@router.delete("/perf/engagement/{eng_id}/profile/{profile_id}")
def delete_profile(eng_id: str, profile_id: str, product: str,
                   current_user: dict = Depends(require_user)) -> dict:
    _check_product_access(product, current_user)
    eng = _pm.delete_profile(product, eng_id, profile_id)
    if not eng:
        raise HTTPException(404, detail="Engagement not found")
    return eng


# ── run management ────────────────────────────────────────────────────────────

@router.post("/perf/engagement/{eng_id}/run")
def trigger_run(eng_id: str, product: str, profile_id: str,
                background_tasks: BackgroundTasks,
                current_user: dict = Depends(require_user)) -> dict:
    _check_product_access(product, current_user)
    eng = _pm.get(product, eng_id)
    if not eng:
        raise HTTPException(404, detail="Engagement not found")
    profile = next((p for p in eng.get("profiles", []) if p["profile_id"] == profile_id), None)
    if not profile:
        raise HTTPException(404, detail="Profile not found")
    run = _pm.add_run(product, eng_id, profile_id, current_user.get("name", "unknown"))
    if not run:
        raise HTTPException(500, detail="Failed to create run record")
    background_tasks.add_task(_execute_perf_run, product, eng_id, run["run_id"], profile)
    return run


@router.delete("/perf/engagement/{eng_id}/run/{run_id}")
def delete_run(eng_id: str, run_id: str, product: str,
               current_user: dict = Depends(require_user)) -> dict:
    _check_product_access(product, current_user)
    eng = _pm.get(product, eng_id)
    if not eng:
        raise HTTPException(404, detail="Engagement not found")
    target = next((r for r in eng.get("runs", []) if r["run_id"] == run_id), None)
    if target and target.get("status") in ("queued", "running"):
        raise HTTPException(400, detail="Cannot delete a run that is currently active")
    if not _pm.delete_run(product, eng_id, run_id):
        raise HTTPException(404, detail="Run not found")
    return _pm.get(product, eng_id)


# ── report ────────────────────────────────────────────────────────────────────

@router.get("/perf/engagement/{eng_id}/report")
def download_report(eng_id: str, product: str, format: str = "pdf",
                    current_user: dict = Depends(require_user)) -> Response:
    _check_product_access(product, current_user)
    eng = _pm.get(product, eng_id)
    if not eng:
        raise HTTPException(404, detail="Engagement not found")
    html = _render_report_html(eng)
    if format == "pdf":
        pdf = _to_pdf(html)
        if pdf is None:
            raise HTTPException(500, detail="WeasyPrint not installed")
        return Response(pdf, media_type="application/pdf",
                        headers={"Content-Disposition": f'attachment; filename="perf_report_{product}_{eng_id}.pdf"'})
    return Response(html, media_type="text/html")


# ── execution ─────────────────────────────────────────────────────────────────

def _execute_perf_run(product: str, eng_id: str, run_id: str, profile: dict) -> None:
    _pm.patch_run(product, eng_id, run_id, status="running")
    try:
        metrics = asyncio.run(_run_load_test(
            target_url=profile.get("target_url") or _pm.get(product, eng_id).get("target_url", ""),
            profile=profile,
        ))
        _pm.patch_run(product, eng_id, run_id,
                      status="completed",
                      finished_at=datetime.now(timezone.utc).isoformat(),
                      metrics=metrics)
    except Exception as exc:
        _pm.patch_run(product, eng_id, run_id,
                      status="failed",
                      finished_at=datetime.now(timezone.utc).isoformat(),
                      error=str(exc))


async def _run_load_test(target_url: str, profile: dict) -> dict:
    vus = max(1, profile.get("vus", 10))
    duration_s = max(5, profile.get("duration_s", 60))
    ramp_up_s = max(0, min(profile.get("ramp_up_s", 10), duration_s))
    endpoints = profile.get("endpoints", []) or [{"method": "GET", "path": "/", "expected_status": 200}]
    thresholds = profile.get("thresholds", {})
    base = target_url.rstrip("/")

    results: list[dict] = []
    lock = asyncio.Lock()

    async def _one_request(client: httpx.AsyncClient, ep: dict) -> None:
        url = base + ep.get("path", "/")
        method = ep.get("method", "GET").upper()
        exp_status = ep.get("expected_status", 200)
        body = ep.get("body") or None
        hdrs = ep.get("headers") or {}
        t0 = time.perf_counter()
        try:
            resp = await client.request(method, url, json=body, headers=hdrs)
            ms = (time.perf_counter() - t0) * 1000
            async with lock:
                results.append({
                    "ms": ms,
                    "status": resp.status_code,
                    "error": False,
                    "status_ok": resp.status_code == exp_status,
                })
        except Exception:
            ms = (time.perf_counter() - t0) * 1000
            async with lock:
                results.append({"ms": ms, "status": 0, "error": True, "status_ok": False})

    async def _worker(worker_id: int) -> None:
        # simple ramp-up: stagger worker starts
        if ramp_up_s > 0 and vus > 1:
            await asyncio.sleep(ramp_up_s * worker_id / vus)
        deadline = time.monotonic() + duration_s
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            while time.monotonic() < deadline:
                for ep in endpoints:
                    await _one_request(client, ep)
                await asyncio.sleep(0.05)

    await asyncio.gather(*(_worker(i) for i in range(vus)))

    total = len(results)
    errors = sum(1 for r in results if r["error"])
    latencies = sorted(r["ms"] for r in results if not r["error"])

    def _pct(p: float) -> int:
        if not latencies:
            return 0
        idx = int(len(latencies) * p / 100)
        return round(latencies[min(idx, len(latencies) - 1)])

    p50, p75, p95, p99 = _pct(50), _pct(75), _pct(95), _pct(99)
    err_rate = round(errors / total * 100, 2) if total else 0.0
    throughput = round(total / duration_s, 2)

    # Check thresholds
    thresh_results: dict[str, dict] = {}
    passed_all = True
    for key, limit in thresholds.items():
        actual: float | None = None
        if key == "p95_ms":
            actual = p95
        elif key == "p99_ms":
            actual = p99
        elif key == "p50_ms":
            actual = p50
        elif key == "error_rate_pct":
            actual = err_rate
        if actual is not None:
            ok = actual <= limit
            thresh_results[key] = {"limit": limit, "actual": actual, "passed": ok}
            if not ok:
                passed_all = False

    return {
        "total_requests": total,
        "error_count": errors,
        "error_rate_pct": err_rate,
        "throughput_rps": throughput,
        "p50_ms": p50,
        "p75_ms": p75,
        "p95_ms": p95,
        "p99_ms": p99,
        "thresholds_passed": passed_all,
        "threshold_results": thresh_results,
    }
