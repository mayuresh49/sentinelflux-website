"""Remote runner API — claim/progress/result endpoints for decoupled test execution.

A runner agent (sentinelflux runner) polls GET /api/runner/claim to grab queued runs,
executes pytest locally, then POSTs results back to POST /api/runner/{run_id}/result.
Auth: Bearer token (runner_tokens in data/config.yaml, managed via /api/config/runner-tokens).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from core.run_manager import RunManager
from dashboard.routers.auth import require_runner_token
from utils.paths import ROOT as _ROOT

router = APIRouter(tags=["runner"])

_rm = RunManager()
_RUNS_DIR = _ROOT / "data" / "runs"
_ARTIFACTS_DIR = _ROOT / "data" / "artifacts"


# ── Pydantic bodies ───────────────────────────────────────────────────────────

class ProgressBody(BaseModel):
    total: int = 0
    done: int = 0


class ResultBody(BaseModel):
    report: dict[str, Any] = {}
    returncode: int = 0


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/runner/claim")
def claim_run(
    product: str | None = None,
    runner: dict = Depends(require_runner_token),
):
    """Return the oldest queued run the runner is authorised for, marking it running."""
    allowed = runner.get("products") or []  # empty list = all products
    runs = _rm.all_runs(product=product) if product else _rm.all_runs()
    queued = [
        r for r in runs
        if r["status"] == "queued"
        and (not allowed or r.get("product") in allowed)
    ]
    if not queued:
        return {"run": None}
    # Oldest first
    run = min(queued, key=lambda r: r.get("triggered_at", ""))
    _rm.patch_run(run["id"], status="running", claimed_by=runner.get("name", "runner"))
    return {"run": run}


@router.post("/runner/{run_id}/progress")
def update_progress(
    run_id: str,
    body: ProgressBody,
    runner: dict = Depends(require_runner_token),
):
    """Runner streams live progress updates during a run."""
    _assert_runner_owns(run_id, runner)
    _rm.patch_run(run_id, progress_total=body.total, progress_done=body.done)
    return {"ok": True}


@router.post("/runner/{run_id}/result")
def post_result(
    run_id: str,
    body: ResultBody,
    runner: dict = Depends(require_runner_token),
):
    """Runner posts the full pytest-json-report payload when the run finishes."""
    _assert_runner_owns(run_id, runner)

    # Persist report to disk (same location the dashboard expects)
    run = _rm.get_run(run_id)
    if not run:
        raise HTTPException(404, "Run not found")

    report_path = _ROOT / run["report_path"]
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(body.report, indent=2), encoding="utf-8")

    stats = _parse_report(report_path)
    ok = body.returncode in (0, 1)
    _rm.patch_run(
        run_id,
        status="completed" if ok else "failed",
        finished_at=datetime.now(timezone.utc).isoformat(),
        progress_done=stats.get("total", 0),
        **stats,
    )

    if stats.get("failed", 0) > 0:
        _trigger_analysis(run_id, run.get("domain", "api"), report_path)

    return {"ok": True, "stats": stats}


# ── helpers ───────────────────────────────────────────────────────────────────

def _assert_runner_owns(run_id: str, runner: dict) -> None:
    allowed = runner.get("products") or []
    if not allowed:
        return  # unrestricted token
    run = _rm.get_run(run_id)
    if run and run.get("product") not in allowed:
        raise HTTPException(403, "Runner not authorised for this run's product")


def _parse_report(report_path: Path) -> dict[str, Any]:
    if not report_path.exists():
        return {"total": 0, "passed": 0, "failed": 0, "skipped": 0, "errors": 0, "duration": 0.0, "failures": []}
    try:
        data = json.loads(report_path.read_text(encoding="utf-8"))
        summary = data.get("summary", {})
        failures = []
        for t in data.get("tests", []):
            if t.get("outcome") in ("failed", "error"):
                error = t.get("call", {}).get("longrepr", "") or t.get("longrepr", "") or ""
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


def _trigger_analysis(run_id: str, domain: str, report_path: Path) -> None:
    import threading
    threading.Thread(target=_analyze, args=(run_id, domain, report_path), daemon=True).start()


def _analyze(run_id: str, domain: str, report_path: Path) -> None:
    try:
        from dashboard.routers.runs import _build_ai_client, _analyze_failures
        _analyze_failures(run_id, domain, report_path)
    except Exception:
        pass
