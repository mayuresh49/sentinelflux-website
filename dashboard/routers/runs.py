"""Test suite run triggering, history, failure analysis, and schedule management."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from core.run_manager import RunManager
from utils.paths import ROOT as _ROOT

router = APIRouter(prefix="/runs", tags=["runs"])
_ARTIFACTS_DIR = _ROOT / "reports" / "artifacts"
_rm = RunManager()


# ── request models ────────────────────────────────────────────────────────────

class TriggerRunBody(BaseModel):
    product: str
    domain: str = "all"       # all | api | web | mobile | security
    extra_args: str = ""       # appended verbatim to pytest command
    environment: str = ""     # name of environment profile; "" = use product default
    browser: str = ""         # name of browser profile; "" = use product default
    device: str = ""          # name of device profile; "" = use product default

class CreateScheduleBody(BaseModel):
    name: str
    product: str
    domain: str = "all"
    hour: int = 2
    minute: int = 0
    days: list[str] = ["mon", "tue", "wed", "thu", "fri"]
    environment: str = ""
    browser: str = ""
    device: str = ""


# ── trigger & history ─────────────────────────────────────────────────────────

@router.post("/trigger")
def trigger_run(body: TriggerRunBody, background_tasks: BackgroundTasks):
    snapshot = _build_run_config_snapshot(body.product, body.environment, body.browser, body.device)
    run = _rm.create_run(product=body.product, domain=body.domain, trigger="manual",
                         run_config_snapshot=snapshot)
    background_tasks.add_task(_execute_run, run["id"], body.product, body.domain, body.extra_args,
                               body.environment, body.browser, body.device)
    return {"run_id": run["id"], "status": "queued"}


@router.get("/")
def list_runs(product: str | None = None, domain: str | None = None,
              status: str | None = None, limit: int = 50):
    runs = list(reversed(_rm.all_runs()))
    if product:
        runs = [r for r in runs if r.get("product") == product]
    if domain:
        runs = [r for r in runs if r.get("domain") == domain]
    if status:
        runs = [r for r in runs if r.get("status") == status]
    return {"runs": runs[:limit], "total": len(runs)}


@router.get("/{run_id}")
def get_run(run_id: str):
    run = _rm.get_run(run_id)
    if not run:
        raise HTTPException(404, "Run not found")
    return run


@router.post("/{run_id}/analyze")
def analyze_run(run_id: str, background_tasks: BackgroundTasks):
    run = _rm.get_run(run_id)
    if not run:
        raise HTTPException(404, "Run not found")
    if run.get("status") not in ("completed", "failed"):
        raise HTTPException(400, "Run not finished yet")
    report_path = _ROOT / run["report_path"]
    if not report_path.exists():
        raise HTTPException(404, "Report file not found — re-run to regenerate")
    background_tasks.add_task(_analyze_failures, run_id, run["domain"], report_path)
    return {"status": "analysis_queued", "run_id": run_id}


@router.post("/{run_id}/rerun")
def rerun(run_id: str, background_tasks: BackgroundTasks):
    run = _rm.get_run(run_id)
    if not run:
        raise HTTPException(404, "Run not found")
    snap = run.get("run_config_snapshot", {})
    new_run = _rm.create_run(
        product=run["product"], domain=run["domain"], trigger="manual",
        run_config_snapshot=snap,
    )
    background_tasks.add_task(_execute_run, new_run["id"], run["product"], run["domain"], "",
                               snap.get("environment", ""), snap.get("browser", ""), snap.get("device", ""))
    return {"run_id": new_run["id"], "status": "queued"}


# ── schedules ─────────────────────────────────────────────────────────────────

@router.get("/schedules/all")
def list_schedules():
    return {"schedules": _rm.all_schedules()}


@router.post("/schedules")
def create_schedule(body: CreateScheduleBody):
    sched = _rm.create_schedule(
        name=body.name,
        product=body.product,
        domain=body.domain,
        hour=body.hour,
        minute=body.minute,
        days=body.days,
        environment=body.environment,
        browser=body.browser,
        device=body.device,
    )
    return sched


@router.post("/schedules/{sched_id}/toggle")
def toggle_schedule(sched_id: str):
    sched = _rm.get_schedule(sched_id)
    if not sched:
        raise HTTPException(404, "Schedule not found")
    updated = _rm.patch_schedule(sched_id, enabled=not sched.get("enabled", True))
    return updated


@router.delete("/schedules/{sched_id}")
def delete_schedule(sched_id: str):
    if not _rm.delete_schedule(sched_id):
        raise HTTPException(404, "Schedule not found")
    return {"deleted": sched_id}


@router.post("/schedules/{sched_id}/run-now")
def schedule_run_now(sched_id: str, background_tasks: BackgroundTasks):
    sched = _rm.get_schedule(sched_id)
    if not sched:
        raise HTTPException(404, "Schedule not found")
    env = sched.get("environment", "")
    browser = sched.get("browser", "")
    device = sched.get("device", "")
    snapshot = _build_run_config_snapshot(sched["product"], env, browser, device)
    run = _rm.create_run(
        product=sched["product"], domain=sched["domain"],
        trigger="schedule", schedule_id=sched_id,
        run_config_snapshot=snapshot,
    )
    background_tasks.add_task(_execute_run, run["id"], sched["product"], sched["domain"], "",
                               env, browser, device)
    return {"run_id": run["id"], "status": "queued"}


# ── background tasks ──────────────────────────────────────────────────────────

def _execute_run(run_id: str, product: str, domain: str, extra_args: str,
                 environment: str = "", browser: str = "", device: str = "") -> None:
    _rm.patch_run(run_id, status="running")
    report_path = _ROOT / _rm.get_run(run_id)["report_path"]
    report_path.parent.mkdir(parents=True, exist_ok=True)

    env_overrides = _build_env_overrides(product, environment, browser, device)

    test_path = _resolve_test_path(product, domain)
    if not test_path:
        _rm.patch_run(run_id, status="failed",
                      finished_at=datetime.now(timezone.utc).isoformat(),
                      failures=[],
                      total=0,
                      summary_error=f"No tests found for product={product} domain={domain}")
        return

    cmd = [
        sys.executable, "-m", "pytest",
        str(test_path),
        "--json-report",
        f"--json-report-file={report_path}",
        "-q", "--tb=short", "--no-header",
        "--override-ini=addopts=",   # suppress html/screenshot opts for programmatic runs
    ]
    if extra_args.strip():
        cmd.extend(extra_args.split())

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=600, cwd=str(_ROOT),
            env={**os.environ, **env_overrides},
        )
        stats = _parse_report(report_path)
        ok = result.returncode in (0, 1)  # 0=all pass, 1=some fail — both are valid runs
        _rm.patch_run(
            run_id,
            status="completed" if ok else "failed",
            finished_at=datetime.now(timezone.utc).isoformat(),
            **stats,
        )
        if stats.get("failed", 0) > 0 and report_path.exists():
            _analyze_failures(run_id, domain, report_path)
    except subprocess.TimeoutExpired:
        _rm.patch_run(run_id, status="failed",
                      finished_at=datetime.now(timezone.utc).isoformat())
    except Exception as exc:
        _rm.patch_run(run_id, status="failed",
                      finished_at=datetime.now(timezone.utc).isoformat(),
                      summary_error=str(exc))


def _analyze_failures(run_id: str, domain: str, report_path: Path) -> None:
    """Run ResultAnalyzerAgent if an AI client is available; update run record."""
    try:
        from ai.agents.base_agent import AgentContext
        from ai.agents.result_analyzer_agent import ResultAnalyzerAgent
        client = _build_ai_client()
        if not client:
            return
        ctx = AgentContext(domain=domain or "api")
        agent = ResultAnalyzerAgent(ai_client=client, context=ctx)
        result = agent.run(report_path=report_path, artifacts_dir=_ARTIFACTS_DIR)
        _rm.patch_run(
            run_id,
            analyzed=True,
            failure_categories=result.get("by_classification", {}),
            failures=result.get("failures", []),
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


def _resolve_test_path(product: str, domain: str) -> Path | None:
    base = _ROOT / "products" / product / "tests"
    if base.exists():
        if domain and domain != "all":
            specific = base / domain
            return specific if specific.exists() else base
        return base
    fallback = _ROOT / "tests"
    if domain and domain != "all":
        dp = fallback / domain
        return dp if dp.exists() else (fallback if fallback.exists() else None)
    return fallback if fallback.exists() else None


def _build_ai_client():
    """Build an AI client from the dashboard chat config, or return None."""
    try:
        cfg_path = _ROOT / "dashboard" / "chat_config.json"
        if not cfg_path.exists():
            return None
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        provider = cfg.get("provider", "ollama")
        model = cfg.get("model", "")
        if provider == "ollama":
            from ai.clients.mistral_client import MistralClient
            return MistralClient(model=model, base_url=cfg.get("base_url", "http://localhost:11434"))
        if provider == "openai":
            import os
            api_key = os.environ.get("OPENAI_API_KEY", "")
            if not api_key:
                return None
            from ai.clients.openai_client import OpenAIClient
            return OpenAIClient(api_key=api_key, model=model or "gpt-4o-mini")
        if provider == "anthropic":
            import os
            api_key = os.environ.get("ANTHROPIC_API_KEY", "")
            if not api_key:
                return None
            from ai.clients.anthropic_client import AnthropicClient
            return AnthropicClient(api_key=api_key, model=model or "claude-haiku-4-5-20251001")
        return None
    except Exception:
        return None


# ── run config resolution ─────────────────────────────────────────────────────

def _load_product_run_config(product: str) -> dict:
    try:
        cfg_path = _ROOT / "data" / "config.yaml"
        if not cfg_path.exists():
            return {}
        cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
        p = next((p for p in cfg.get("products", []) if p["name"] == product), None)
        return (p or {}).get("run_config", {})
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
    snapshot = _build_run_config_snapshot(sched["product"], env, browser, device)
    run = _rm.create_run(
        product=sched["product"], domain=sched["domain"],
        trigger="schedule", schedule_id=sched_id,
        run_config_snapshot=snapshot,
    )
    import threading
    t = threading.Thread(
        target=_execute_run,
        args=(run["id"], sched["product"], sched["domain"], "", env, browser, device),
        daemon=True,
    )
    t.start()
    _rm.patch_schedule(sched_id, last_run_id=run["id"],
                       last_run_at=datetime.now(timezone.utc).isoformat())
    return run["id"]
