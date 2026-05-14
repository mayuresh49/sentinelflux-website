"""Test suite run triggering, history, failure analysis, and schedule management."""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from utils.run_manager import RunManager

router = APIRouter(prefix="/runs", tags=["runs"])

_ROOT = Path(__file__).resolve().parent.parent.parent
_ARTIFACTS_DIR = _ROOT / "reports" / "artifacts"
_rm = RunManager()


# ── request models ────────────────────────────────────────────────────────────

class TriggerRunBody(BaseModel):
    product: str
    domain: str = "all"       # all | api | web | mobile | security
    extra_args: str = ""       # appended verbatim to pytest command

class CreateScheduleBody(BaseModel):
    name: str
    product: str
    domain: str = "all"
    hour: int = 2
    minute: int = 0
    days: list[str] = ["mon", "tue", "wed", "thu", "fri"]


# ── trigger & history ─────────────────────────────────────────────────────────

@router.post("/trigger")
def trigger_run(body: TriggerRunBody, background_tasks: BackgroundTasks):
    run = _rm.create_run(product=body.product, domain=body.domain, trigger="manual")
    background_tasks.add_task(_execute_run, run["id"], body.product, body.domain, body.extra_args)
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
    report_path = Path(run["report_path"])
    if not report_path.exists():
        raise HTTPException(404, "Report file not found — re-run to regenerate")
    background_tasks.add_task(_analyze_failures, run_id, run["domain"], report_path)
    return {"status": "analysis_queued", "run_id": run_id}


@router.post("/{run_id}/rerun")
def rerun(run_id: str, background_tasks: BackgroundTasks):
    run = _rm.get_run(run_id)
    if not run:
        raise HTTPException(404, "Run not found")
    new_run = _rm.create_run(
        product=run["product"], domain=run["domain"], trigger="manual"
    )
    background_tasks.add_task(_execute_run, new_run["id"], run["product"], run["domain"], "")
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
    run = _rm.create_run(
        product=sched["product"], domain=sched["domain"],
        trigger="schedule", schedule_id=sched_id,
    )
    background_tasks.add_task(_execute_run, run["id"], sched["product"], sched["domain"], "")
    return {"run_id": run["id"], "status": "queued"}


# ── background tasks ──────────────────────────────────────────────────────────

def _execute_run(run_id: str, product: str, domain: str, extra_args: str) -> None:
    _rm.patch_run(run_id, status="running")
    report_path = Path(_rm.get_run(run_id)["report_path"])
    report_path.parent.mkdir(parents=True, exist_ok=True)

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
            cmd, capture_output=True, text=True, timeout=600, cwd=str(_ROOT)
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
        from ai.agents.result_analyzer_agent import ResultAnalyzerAgent
        from ai.agents.base_agent import AgentContext
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
    base = _ROOT / "examples" / product / "tests"
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
        cfg_path = Path(__file__).resolve().parent.parent / "chat_config.json"
        if not cfg_path.exists():
            return None
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        provider = cfg.get("provider", "ollama")
        model = cfg.get("model", "")
        if provider == "ollama":
            from ai.clients.mistral_client import MistralClient
            return MistralClient(model=model, base_url=cfg.get("base_url", "http://localhost:11434"))
        # Other providers not yet wired to the AI client layer
        return None
    except Exception:
        return None


# ── public helper for schedule checker ───────────────────────────────────────

def fire_scheduled_run(sched_id: str) -> str | None:
    """Trigger a scheduled run and return the new run_id."""
    sched = _rm.get_schedule(sched_id)
    if not sched:
        return None
    run = _rm.create_run(
        product=sched["product"], domain=sched["domain"],
        trigger="schedule", schedule_id=sched_id,
    )
    import threading
    t = threading.Thread(
        target=_execute_run,
        args=(run["id"], sched["product"], sched["domain"], ""),
        daemon=True,
    )
    t.start()
    _rm.patch_schedule(sched_id, last_run_id=run["id"],
                       last_run_at=datetime.now(timezone.utc).isoformat())
    return run["id"]
