"""Pipeline trigger and background job tracking."""
from __future__ import annotations

import json
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel

from filelock import FileLock
from utils.activity_log import ActivityLog
from utils.paths import ROOT as _ROOT_DIR

router = APIRouter(prefix="/pipeline", tags=["pipeline"])

_JOBS_PATH = _ROOT_DIR / "framework_knowledge" / "pipeline_jobs.json"
_alog = ActivityLog()
_MAX_JOBS = 50


class TriggerBody(BaseModel):
    product: str
    feature: str
    domain: str
    increment_file: str = ""          # optional — pass --increment instead of --feature
    local_url: str = "http://localhost:11434"
    doc_model: str = "mistral:7b-instruct-v0.3-q4_K_M"
    script_model: str = "qwen2.5-coder:14b-instruct-q4_K_M"
    skip_script: bool = False
    source: str = ""                  # optional — OpenAPI spec path/URL, service code path


@router.post("/trigger")
def trigger(body: TriggerBody, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    _write_job({
        "id": job_id,
        "started": datetime.now(timezone.utc).isoformat(),
        "product": body.product,
        "feature": body.feature,
        "domain": body.domain,
        "increment_file": body.increment_file,
        "status": "running",
        "output": "",
        "finished": None,
    })
    background_tasks.add_task(_run, job_id, body)
    return {"job_id": job_id, "status": "started"}


@router.get("/jobs")
def list_jobs():
    return {"jobs": list(reversed(_load_jobs()))[:_MAX_JOBS]}


@router.get("/jobs/{job_id}")
def get_job(job_id: str):
    job = next((j for j in _load_jobs() if j["id"] == job_id), None)
    if not job:
        from fastapi import HTTPException
        raise HTTPException(404, "Job not found")
    return job


# ── internals ──────────────────────────────────────────────────────────────

def _run(job_id: str, body: TriggerBody):
    if body.increment_file:
        mode_args = ["--increment", body.increment_file]
    else:
        mode_args = ["--feature", body.feature]

    cmd = [
        sys.executable, "-m", "ai.pipeline.orchestrator",
        *mode_args,
        "--domain", body.domain,
        "--project", body.product,
        "--output-base", str(_ROOT_DIR / "examples" / body.product),
        "--local",
        "--local-url", body.local_url,
        "--doc-model", body.doc_model,
        "--script-model", body.script_model,
    ]
    if body.skip_script:
        cmd.append("--skip-script")
    if body.source:
        cmd.extend(["--source", body.source])

    _alog.append(
        event_type="pipeline_run", agent="pipeline",
        domain=body.domain, product=body.product,
        status="pending",
        summary=f"Pipeline started — {body.feature or body.increment_file} / {body.domain}",
    )

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=600, cwd=str(_ROOT_DIR)
        )
        ok = result.returncode == 0
        output = (result.stdout + result.stderr).strip()
        _patch_job(job_id, "completed" if ok else "failed", output)
        _alog.append(
            event_type="pipeline_run", agent="pipeline",
            domain=body.domain, product=body.product,
            status="success" if ok else "error",
            summary=f"Pipeline {'completed' if ok else 'failed'} — {body.feature or body.increment_file}",
            output={"returncode": result.returncode, "log": output[-2000:]},
        )
    except subprocess.TimeoutExpired:
        _patch_job(job_id, "failed", "Timeout — exceeded 10 minutes")
        _alog.append(
            event_type="pipeline_run", agent="pipeline",
            domain=body.domain, product=body.product,
            status="error", summary=f"Pipeline timeout — {body.feature}",
        )
    except Exception as exc:
        _patch_job(job_id, "failed", str(exc))


def _load_jobs() -> list[dict[str, Any]]:
    if not _JOBS_PATH.exists():
        return []
    with _JOBS_PATH.open(encoding="utf-8") as f:
        return json.load(f).get("jobs", [])


def _write_job(job: dict[str, Any]):
    jobs = _load_jobs()
    jobs.append(job)
    if len(jobs) > _MAX_JOBS:
        jobs = jobs[-_MAX_JOBS:]
    _JOBS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with FileLock(str(_JOBS_PATH) + ".lock"):
        with _JOBS_PATH.open("w", encoding="utf-8") as f:
            json.dump({"jobs": jobs}, f, indent=2)


def _patch_job(job_id: str, status: str, output: str):
    jobs = _load_jobs()
    for j in jobs:
        if j["id"] == job_id:
            j["status"] = status
            j["output"] = output
            j["finished"] = datetime.now(timezone.utc).isoformat()
            break
    with FileLock(str(_JOBS_PATH) + ".lock"):
        with _JOBS_PATH.open("w", encoding="utf-8") as f:
            json.dump({"jobs": jobs}, f, indent=2)
