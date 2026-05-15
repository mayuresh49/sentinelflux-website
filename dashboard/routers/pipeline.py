"""Pipeline trigger and background job tracking."""
from __future__ import annotations

import subprocess
import sys
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel

from core.activity_log import ActivityLog
from core.db import get_conn
from utils.paths import ROOT as _ROOT_DIR

router = APIRouter(prefix="/pipeline", tags=["pipeline"])

_alog = ActivityLog()
_MAX_JOBS = 50


class TriggerBody(BaseModel):
    product: str
    feature: str
    domain: str
    increment_file: str = ""
    local_url: str = "http://localhost:11434"
    doc_model: str = "mistral:7b-instruct-v0.3-q4_K_M"
    script_model: str = "qwen2.5-coder:14b-instruct-q4_K_M"
    skip_script: bool = False
    source: str = ""


@router.post("/trigger")
def trigger(body: TriggerBody, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    conn = get_conn()
    conn.execute(
        """INSERT INTO pipeline_jobs
           (id, started, finished, product, feature, domain, increment_file, status, output)
           VALUES (?, ?, NULL, ?, ?, ?, ?, 'running', '')""",
        (
            job_id,
            datetime.now(timezone.utc).isoformat(),
            body.product, body.feature, body.domain, body.increment_file,
        ),
    )
    # Enforce max jobs cap
    conn.execute(
        "DELETE FROM pipeline_jobs WHERE id NOT IN "
        "(SELECT id FROM pipeline_jobs ORDER BY started DESC LIMIT ?)",
        (_MAX_JOBS,),
    )
    conn.commit()
    background_tasks.add_task(_run, job_id, body)
    return {"job_id": job_id, "status": "started"}


@router.get("/jobs")
def list_jobs():
    rows = get_conn().execute(
        "SELECT * FROM pipeline_jobs ORDER BY started DESC LIMIT ?", (_MAX_JOBS,)
    ).fetchall()
    return {"jobs": [dict(r) for r in rows]}


@router.get("/jobs/{job_id}")
def get_job(job_id: str):
    row = get_conn().execute(
        "SELECT * FROM pipeline_jobs WHERE id = ?", (job_id,)
    ).fetchone()
    if not row:
        from fastapi import HTTPException
        raise HTTPException(404, "Job not found")
    return dict(row)


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
        "--output-base", str(_ROOT_DIR / "products" / body.product),
        "--local",
        "--local-url", body.local_url,
        "--doc-model", body.doc_model,
        "--script-model", body.script_model,
    ]
    if body.skip_script:
        cmd.append("--skip-script")
    source = body.source
    if not source:
        try:
            from dashboard.routers.kb import _product_kb_dir
            import yaml as _yaml
            openapi_file = _product_kb_dir(body.product) / "openapi_specs.yaml"
            if openapi_file.exists():
                source = (_yaml.safe_load(openapi_file.read_text(encoding="utf-8")) or {}).get("openapi_url", "")
        except Exception:
            pass
    if source:
        cmd.extend(["--source", source])

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


def _patch_job(job_id: str, status: str, output: str):
    conn = get_conn()
    conn.execute(
        "UPDATE pipeline_jobs SET status = ?, output = ?, finished = ? WHERE id = ?",
        (status, output, datetime.now(timezone.utc).isoformat(), job_id),
    )
    conn.commit()
