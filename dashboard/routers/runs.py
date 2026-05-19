"""Test suite run triggering, history, failure analysis, and schedule management."""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel

from dashboard.routers.auth import require_user, user_products

from core.run_manager import RunManager
from utils.paths import ROOT as _ROOT

router = APIRouter(prefix="/runs", tags=["runs"])
_ARTIFACTS_DIR = _ROOT / "reports" / "artifacts"
_rm = RunManager()


def _visible_products(current_user: dict) -> list[str]:
    from dashboard.routers.kb import _list_products
    return user_products(current_user, _list_products())


def _check_product(product: str, current_user: dict) -> None:
    if product not in _visible_products(current_user):
        raise HTTPException(403, "Access denied to this product")


# ── request models ────────────────────────────────────────────────────────────

class TriggerRunBody(BaseModel):
    product: str
    domain: str = "all"       # all | api | web | mobile | security
    module: str = ""          # specific test file stem, e.g. "test_login"; "" = run all
    extra_args: str = ""       # appended verbatim to pytest command
    environment: str = ""     # name of environment profile; "" = use product default
    browser: str = ""         # name of browser profile; "" = use product default
    device: str = ""          # name of device profile; "" = use product default

class CreateScheduleBody(BaseModel):
    name: str
    product: str
    domain: str = "all"
    module: str = ""
    hour: int = 2
    minute: int = 0
    days: list[str] = ["mon", "tue", "wed", "thu", "fri"]
    environment: str = ""
    browser: str = ""
    device: str = ""


# ── trigger & history ─────────────────────────────────────────────────────────

@router.get("/modules")
def list_modules(product: str, domain: str = "all", current_user: dict = Depends(require_user)):
    """Return test file stems for a product+domain combo."""
    _check_product(product, current_user)
    base = _resolve_test_path(product, domain)
    if not base:
        return {"modules": []}
    pattern = "test_*.py"
    files = sorted(p.stem for p in base.glob(pattern) if p.is_file())
    return {"modules": files}


@router.post("/trigger")
def trigger_run(body: TriggerRunBody, background_tasks: BackgroundTasks, current_user: dict = Depends(require_user)):
    _check_product(body.product, current_user)
    snapshot = _build_run_config_snapshot(body.product, body.environment, body.browser, body.device)
    run = _rm.create_run(product=body.product, domain=body.domain, module=body.module,
                         trigger="manual", run_config_snapshot=snapshot)
    background_tasks.add_task(_execute_run, run["id"], body.product, body.domain, body.module,
                               body.extra_args, body.environment, body.browser, body.device)
    return {"run_id": run["id"], "status": "queued"}


@router.get("/")
def list_runs(product: str | None = None, domain: str | None = None,
              status: str | None = None, limit: int = 50,
              current_user: dict = Depends(require_user)):
    visible = _visible_products(current_user)
    runs = list(reversed(_rm.all_runs()))
    if product:
        if product not in visible:
            return {"runs": [], "total": 0}
        runs = [r for r in runs if r.get("product") == product]
    else:
        runs = [r for r in runs if r.get("product") in visible]
    if domain:
        runs = [r for r in runs if r.get("domain") == domain]
    if status:
        runs = [r for r in runs if r.get("status") == status]
    return {"runs": runs[:limit], "total": len(runs)}


@router.get("/{run_id}")
def get_run(run_id: str, current_user: dict = Depends(require_user)):
    run = _rm.get_run(run_id)
    if not run:
        raise HTTPException(404, "Run not found")
    if run.get("product") not in _visible_products(current_user):
        raise HTTPException(403, "Access denied")
    return run


@router.delete("/{run_id}")
def delete_run(run_id: str, current_user: dict = Depends(require_user)):
    run = _rm.get_run(run_id)
    if not run:
        raise HTTPException(404, "Run not found")
    if run.get("product") not in _visible_products(current_user):
        raise HTTPException(403, "Access denied")
    _rm.delete_run(run_id)
    return {"deleted": run_id}


@router.post("/{run_id}/analyze")
def analyze_run(run_id: str, background_tasks: BackgroundTasks, current_user: dict = Depends(require_user)):
    run = _rm.get_run(run_id)
    if not run:
        raise HTTPException(404, "Run not found")
    if run.get("product") not in _visible_products(current_user):
        raise HTTPException(403, "Access denied")
    if run.get("status") not in ("completed", "failed"):
        raise HTTPException(400, "Run not finished yet")
    report_path = _ROOT / run["report_path"]
    if not report_path.exists():
        raise HTTPException(404, "Report file not found — re-run to regenerate")
    background_tasks.add_task(_run_post_suite, run_id, run["product"], run["domain"], report_path)
    return {"status": "analysis_queued", "run_id": run_id}


@router.post("/analyze-all")
def analyze_all(background_tasks: BackgroundTasks, current_user: dict = Depends(require_user)):
    """Queue full post-suite chain for every completed/failed run the user can see."""
    visible = _visible_products(current_user)
    queued = []
    for run in _rm.all_runs():
        if run.get("product") not in visible:
            continue
        if run.get("status") not in ("completed", "failed"):
            continue
        report_path = _ROOT / run["report_path"]
        if not report_path.exists():
            continue
        background_tasks.add_task(_run_post_suite, run["id"], run["product"], run["domain"], report_path)
        queued.append(run["id"])
    return {"status": "analysis_queued", "queued": len(queued), "run_ids": queued}


@router.post("/{run_id}/rerun")
def rerun(run_id: str, background_tasks: BackgroundTasks, current_user: dict = Depends(require_user)):
    run = _rm.get_run(run_id)
    if not run:
        raise HTTPException(404, "Run not found")
    if run.get("product") not in _visible_products(current_user):
        raise HTTPException(403, "Access denied")
    snap = run.get("run_config_snapshot", {})
    new_run = _rm.create_run(
        product=run["product"], domain=run["domain"], module=run.get("module", ""),
        trigger="manual", run_config_snapshot=snap,
    )
    background_tasks.add_task(_execute_run, new_run["id"], run["product"], run["domain"],
                               run.get("module", ""), "",
                               snap.get("environment", ""), snap.get("browser", ""), snap.get("device", ""))
    return {"run_id": new_run["id"], "status": "queued"}


# ── schedules ─────────────────────────────────────────────────────────────────

@router.get("/schedules/all")
def list_schedules(current_user: dict = Depends(require_user)):
    visible = _visible_products(current_user)
    schedules = [s for s in _rm.all_schedules() if s.get("product") in visible]
    return {"schedules": schedules}


@router.post("/schedules")
def create_schedule(body: CreateScheduleBody, current_user: dict = Depends(require_user)):
    _check_product(body.product, current_user)
    sched = _rm.create_schedule(
        name=body.name,
        product=body.product,
        domain=body.domain,
        module=body.module,
        hour=body.hour,
        minute=body.minute,
        days=body.days,
        environment=body.environment,
        browser=body.browser,
        device=body.device,
    )
    return sched


@router.post("/schedules/{sched_id}/toggle")
def toggle_schedule(sched_id: str, current_user: dict = Depends(require_user)):
    sched = _rm.get_schedule(sched_id)
    if not sched:
        raise HTTPException(404, "Schedule not found")
    _check_product(sched["product"], current_user)
    updated = _rm.patch_schedule(sched_id, enabled=not sched.get("enabled", True))
    return updated


@router.delete("/schedules/{sched_id}")
def delete_schedule(sched_id: str, current_user: dict = Depends(require_user)):
    sched = _rm.get_schedule(sched_id)
    if not sched:
        raise HTTPException(404, "Schedule not found")
    _check_product(sched["product"], current_user)
    _rm.delete_schedule(sched_id)
    return {"deleted": sched_id}


@router.post("/schedules/{sched_id}/run-now")
def schedule_run_now(sched_id: str, background_tasks: BackgroundTasks, current_user: dict = Depends(require_user)):
    sched = _rm.get_schedule(sched_id)
    if not sched:
        raise HTTPException(404, "Schedule not found")
    _check_product(sched["product"], current_user)
    env = sched.get("environment", "")
    browser = sched.get("browser", "")
    device = sched.get("device", "")
    snapshot = _build_run_config_snapshot(sched["product"], env, browser, device)
    module = sched.get("module", "")
    run = _rm.create_run(
        product=sched["product"], domain=sched["domain"], module=module,
        trigger="schedule", schedule_id=sched_id,
        run_config_snapshot=snapshot,
    )
    background_tasks.add_task(_execute_run, run["id"], sched["product"], sched["domain"],
                               module, "", env, browser, device)
    return {"run_id": run["id"], "status": "queued"}


# ── background tasks ──────────────────────────────────────────────────────────

def _execute_run(run_id: str, product: str, domain: str, module: str, extra_args: str,
                 environment: str = "", browser: str = "", device: str = "") -> None:
    _rm.patch_run(run_id, status="running")
    report_path = _ROOT / _rm.get_run(run_id)["report_path"]
    report_path.parent.mkdir(parents=True, exist_ok=True)

    env_overrides = _build_env_overrides(product, environment, browser, device)

    test_path = _resolve_test_path(product, domain, module)
    if not test_path:
        _rm.patch_run(run_id, status="failed",
                      finished_at=datetime.now(timezone.utc).isoformat(),
                      failures=[],
                      total=0,
                      summary_error=f"No tests found for {product}/{domain}/{module}")
        return

    cmd = [
        sys.executable, "-m", "pytest",
        str(test_path),
        "--json-report",
        f"--json-report-file={report_path}",
        "-v", "--tb=short", "--no-header",
        "--override-ini=addopts=",
    ]
    if extra_args.strip():
        cmd.extend(extra_args.split())

    _collected_re = re.compile(r"collected (\d+) item")
    _result_re = re.compile(r"\s(PASSED|FAILED|ERROR|SKIPPED)\s")

    try:
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, cwd=str(_ROOT), env={**os.environ, **env_overrides},
        )
        progress_total = 0
        progress_done = 0
        last_patch = 0.0
        for line in proc.stdout:
            m = _collected_re.search(line)
            if m:
                progress_total = int(m.group(1))
                _rm.patch_run(run_id, progress_total=progress_total, progress_done=0)
            elif _result_re.search(line):
                progress_done += 1
                now = time.monotonic()
                if now - last_patch >= 2.0:
                    _rm.patch_run(run_id, progress_done=progress_done)
                    last_patch = now

        try:
            proc.wait(timeout=600)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
            _rm.patch_run(run_id, status="failed",
                          finished_at=datetime.now(timezone.utc).isoformat())
            return

        stats = _parse_report(report_path)
        ok = proc.returncode in (0, 1)
        _rm.patch_run(
            run_id,
            status="completed" if ok else "failed",
            finished_at=datetime.now(timezone.utc).isoformat(),
            progress_done=stats.get("total", progress_done),
            **stats,
        )
        if report_path.exists():
            _run_post_suite(run_id, product, domain, report_path)
    except Exception as exc:
        _rm.patch_run(run_id, status="failed",
                      finished_at=datetime.now(timezone.utc).isoformat(),
                      summary_error=str(exc))


def _run_post_suite(run_id: str, product: str, domain: str, report_path: Path) -> None:
    """Run full SentinelOrchestrator chain after suite completion; best-effort."""
    try:
        from ai.agents.sentinel_orchestrator import SentinelOrchestrator
        client = _build_ai_client()
        tests_dir = _ROOT / "products" / product / "tests"
        orch = SentinelOrchestrator(ai_client=client)
        summary = orch.run_post_suite(
            current_report=report_path,
            domain=domain or "api",
            product=product,
            artifacts_dir=_ARTIFACTS_DIR,
            tests_dir=tests_dir if tests_dir.exists() else None,
        )
        _rm.patch_run(
            run_id,
            analyzed=True,
            failure_categories=summary.get("blockers", []),
            post_suite_summary={
                "blockers_count": summary.get("blockers_count", 0),
                "failure_count": summary.get("failure_count", 0),
                "regression_count": summary.get("regression_count", 0),
                "flaky_candidates": summary.get("flaky_candidates", 0),
                "coverage_gaps": summary.get("coverage_gaps", 0),
                "locator_heals": summary.get("locator_heals", 0),
                "requires_human": summary.get("requires_human", False),
            },
        )
    except Exception:
        pass  # analysis is best-effort; raw failures already stored from report parse



def _parse_report(report_path: Path) -> dict[str, Any]:
    if not report_path.exists():
        return {"total": 0, "passed": 0, "failed": 0, "skipped": 0, "errors": 0, "duration": 0.0, "failures": []}
    try:
        data = json.loads(report_path.read_text(encoding="utf-8"))
        summary = data.get("summary", {})
        failures = []
        for t in data.get("tests", []):
            if t.get("outcome") in ("failed", "error"):
                error = (
                    t.get("call", {}).get("longrepr", "")
                    or t.get("longrepr", "")
                    or ""
                )
                failures.append({
                    "test_id": t.get("nodeid", ""),
                    "category": "unanalyzed",
                    "confidence": 0.0,
                    "summary": str(error)[:300],
                    "suggestion": "",
                })
        return {
            "total": summary.get("total", 0),
            "passed": summary.get("passed", 0),
            "failed": summary.get("failed", 0) + summary.get("error", 0),
            "skipped": summary.get("skipped", 0),
            "errors": summary.get("error", 0),
            "duration": round(data.get("duration", 0.0), 2),
            "failures": failures,
        }
    except Exception:
        return {"total": 0, "passed": 0, "failed": 0, "skipped": 0, "errors": 0, "duration": 0.0, "failures": []}


def _resolve_test_path(product: str, domain: str, module: str = "") -> Path | None:
    base = _ROOT / "products" / product / "tests"
    if base.exists():
        domain_dir = (base / domain) if (domain and domain != "all") else base
        if not domain_dir.exists():
            domain_dir = base
        if module:
            stem = module if module.endswith(".py") else f"{module}.py"
            candidate = domain_dir / stem
            return candidate if candidate.exists() else None
        return domain_dir
    fallback = _ROOT / "tests"
    domain_dir = (fallback / domain) if (domain and domain != "all") else fallback
    if not domain_dir.exists():
        domain_dir = fallback if fallback.exists() else None
    if not domain_dir:
        return None
    if module:
        stem = module if module.endswith(".py") else f"{module}.py"
        candidate = domain_dir / stem
        return candidate if candidate.exists() else None
    return domain_dir


def _build_ai_client():
    from core.ai_factory import create_ai_client_from_dashboard
    return create_ai_client_from_dashboard()


# ── run config resolution ─────────────────────────────────────────────────────

def _load_product_run_config(product: str) -> dict:
    try:
        from dashboard.routers.config._run_config import _load_rc
        return _load_rc(product)
    except Exception:
        return {}


def _build_run_config_snapshot(product: str, environment: str, browser: str, device: str) -> dict:
    rc = _load_product_run_config(product)
    defaults = rc.get("defaults", {})
    env_name = environment or defaults.get("environment", "")
    browser_name = browser or defaults.get("browser", "")
    device_name = device or defaults.get("device", "")

    env_profile = next((e for e in rc.get("environments", []) if e.get("name") == env_name), {})
    browser_profile = next((b for b in rc.get("browsers", []) if b.get("name") == browser_name), {})
    device_profile = next((d for d in rc.get("devices", []) if d.get("name") == device_name), {})

    return {
        "environment": env_name,
        "browser": browser_name,
        "device": device_name,
        "base_url": env_profile.get("base_url", ""),
        "api_url": env_profile.get("api_url", ""),
        "browser_type": browser_profile.get("browser", ""),
        "headless": browser_profile.get("headless", True),
        "appium_url": device_profile.get("appium_url", ""),
        "device_platform": device_profile.get("platform", ""),
        "device_capabilities": device_profile.get("capabilities", {}),
    }


def _build_env_overrides(product: str, environment: str, browser: str, device: str) -> dict[str, str]:
    snap = _build_run_config_snapshot(product, environment, browser, device)
    overrides: dict[str, str] = {}
    if snap.get("environment"):
        overrides["SF_ENV"] = snap["environment"]
    if snap.get("base_url"):
        overrides["SF_BASE_URL"] = snap["base_url"]
    if snap.get("api_url"):
        overrides["SF_API_URL"] = snap["api_url"]
    if snap.get("browser_type"):
        overrides["SF_BROWSER"] = snap["browser_type"]
    overrides["SF_HEADLESS"] = "1" if snap.get("headless", True) else "0"
    if snap.get("appium_url"):
        overrides["SF_APPIUM_URL"] = snap["appium_url"]
    if snap.get("device_platform"):
        overrides["SF_DEVICE_PLATFORM"] = snap["device_platform"]
    if snap.get("device_capabilities"):
        overrides["SF_DEVICE_CAPABILITIES"] = json.dumps(snap["device_capabilities"])
    return overrides


# ── public helper for schedule checker ───────────────────────────────────────

def fire_scheduled_run(sched_id: str) -> str | None:
    """Trigger a scheduled run and return the new run_id."""
    sched = _rm.get_schedule(sched_id)
    if not sched:
        return None
    env = sched.get("environment", "")
    browser = sched.get("browser", "")
    device = sched.get("device", "")
    module = sched.get("module", "")
    snapshot = _build_run_config_snapshot(sched["product"], env, browser, device)
    run = _rm.create_run(
        product=sched["product"], domain=sched["domain"], module=module,
        trigger="schedule", schedule_id=sched_id,
        run_config_snapshot=snapshot,
    )
    import threading
    t = threading.Thread(
        target=_execute_run,
        args=(run["id"], sched["product"], sched["domain"], module, "", env, browser, device),
        daemon=True,
    )
    t.start()
    _rm.patch_schedule(sched_id, last_run_id=run["id"],
                       last_run_at=datetime.now(timezone.utc).isoformat())
    return run["id"]
