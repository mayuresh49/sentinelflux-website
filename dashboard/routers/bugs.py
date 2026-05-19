from __future__ import annotations

import mimetypes
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel

from core.bug_manager import BugManager
from dashboard.routers.auth import get_session_user, user_products
from utils.constants import BUG_ARTIFACT_MAX_MB
from utils.paths import ROOT

router = APIRouter(tags=["bugs"])
_bm = BugManager()

_ARTIFACT_TYPE_MAP = {
    "image/png": "screenshot", "image/jpeg": "screenshot", "image/webp": "screenshot",
    "image/gif": "screenshot",
    "video/mp4": "video", "video/webm": "video", "video/quicktime": "video",
    "text/plain": "log", "text/x-log": "log",
    "application/json": "report",
    "application/pdf": "document",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "document",
    "text/markdown": "document",
}


def _require_user(request: Request) -> dict:
    user = get_session_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


def _infer_artifact_type(mime: str, filename: str) -> str:
    t = _ARTIFACT_TYPE_MAP.get(mime)
    if t:
        return t
    ext = Path(filename).suffix.lower()
    if ext in {".png", ".jpg", ".jpeg", ".webp", ".gif"}:
        return "screenshot"
    if ext in {".mp4", ".webm", ".mov"}:
        return "video"
    if ext in {".log", ".txt"}:
        return "log"
    if ext in {".har"}:
        return "har"
    if ext in {".json"}:
        return "report"
    if ext in {".pdf", ".docx", ".md"}:
        return "document"
    return "document"


# ── Request bodies ────────────────────────────────────────────────────────────

class CreateBugBody(BaseModel):
    product: str
    title: str
    description: str = ""
    priority: str = "P2"
    severity: str = "major"
    bug_type: str = "functional"
    component: str = ""
    environment: str = ""
    build_version: str = ""
    assignee: str = ""
    steps_to_reproduce: str = ""
    expected_result: str = ""
    actual_result: str = ""
    tags: list[str] = []
    linked_tc_id: str = ""
    linked_run_id: str = ""
    linked_plan_id: str = ""


class PatchBugBody(BaseModel):
    title: str | None = None
    description: str | None = None
    priority: str | None = None
    severity: str | None = None
    bug_type: str | None = None
    component: str | None = None
    environment: str | None = None
    build_version: str | None = None
    assignee: str | None = None
    steps_to_reproduce: str | None = None
    expected_result: str | None = None
    actual_result: str | None = None
    root_cause: str | None = None
    fix_notes: str | None = None
    tags: list[str] | None = None
    linked_tc_id: str | None = None
    linked_run_id: str | None = None
    linked_plan_id: str | None = None


class TransitionBody(BaseModel):
    to_state: str
    comment: str = ""


class CommentBody(BaseModel):
    body: str


# ── List / Create ─────────────────────────────────────────────────────────────

@router.get("/bugs")
def list_bugs(
    request: Request,
    product: str | None = None,
    state: str | None = None,
    priority: str | None = None,
    assignee: str | None = None,
    component: str | None = None,
    current_user: dict = Depends(_require_user),
):
    visible = set(user_products(current_user, _all_products()))
    if product and product not in visible:
        raise HTTPException(403, "Product not accessible")
    bugs = _bm.list_bugs(
        product=product, state=state, priority=priority,
        assignee=assignee, component=component,
    )
    if not current_user.get("admin"):
        bugs = [b for b in bugs if b["product"] in visible]
    return bugs


@router.post("/bugs")
def create_bug(
    body: CreateBugBody,
    request: Request,
    current_user: dict = Depends(_require_user),
):
    visible = set(user_products(current_user, _all_products()))
    if body.product not in visible:
        raise HTTPException(403, "Product not accessible")
    return _bm.create(
        product=body.product, title=body.title, description=body.description,
        reporter=current_user.get("name", ""),
        priority=body.priority, severity=body.severity, bug_type=body.bug_type,
        component=body.component, environment=body.environment,
        build_version=body.build_version, assignee=body.assignee,
        steps_to_reproduce=body.steps_to_reproduce,
        expected_result=body.expected_result, actual_result=body.actual_result,
        tags=body.tags, linked_tc_id=body.linked_tc_id,
        linked_run_id=body.linked_run_id, linked_plan_id=body.linked_plan_id,
    )


# ── Single bug ────────────────────────────────────────────────────────────────

@router.get("/bugs/{bug_id}")
def get_bug(bug_id: str, current_user: dict = Depends(_require_user)):
    bug = _bm.get(bug_id)
    if not bug:
        raise HTTPException(404)
    _check_product_access(bug["product"], current_user)
    return bug


@router.patch("/bugs/{bug_id}")
def patch_bug(bug_id: str, body: PatchBugBody, current_user: dict = Depends(_require_user)):
    bug = _bm.get(bug_id)
    if not bug:
        raise HTTPException(404)
    _check_product_access(bug["product"], current_user)
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    return _bm.patch(bug_id, **updates)


@router.delete("/bugs/{bug_id}")
def delete_bug(bug_id: str, current_user: dict = Depends(_require_user)):
    if not current_user.get("admin"):
        raise HTTPException(403, "Admin required")
    if not _bm.delete(bug_id):
        raise HTTPException(404)
    return {"deleted": bug_id}


# ── State transitions ─────────────────────────────────────────────────────────

@router.post("/bugs/{bug_id}/transition")
def transition_bug(bug_id: str, body: TransitionBody, current_user: dict = Depends(_require_user)):
    bug = _bm.get(bug_id)
    if not bug:
        raise HTTPException(404)
    _check_product_access(bug["product"], current_user)
    try:
        return _bm.transition(bug_id, body.to_state, current_user.get("name", ""), body.comment)
    except ValueError as e:
        raise HTTPException(400, detail=str(e))


@router.get("/bugs/{bug_id}/history")
def get_history(bug_id: str, current_user: dict = Depends(_require_user)):
    bug = _bm.get(bug_id)
    if not bug:
        raise HTTPException(404)
    _check_product_access(bug["product"], current_user)
    return _bm.get_history(bug_id)


# ── Comments ──────────────────────────────────────────────────────────────────

@router.post("/bugs/{bug_id}/comments")
def add_comment(bug_id: str, body: CommentBody, current_user: dict = Depends(_require_user)):
    bug = _bm.get(bug_id)
    if not bug:
        raise HTTPException(404)
    _check_product_access(bug["product"], current_user)
    if not body.body.strip():
        raise HTTPException(400, "Comment body cannot be empty")
    return _bm.add_comment(bug_id, current_user.get("name", ""), body.body.strip())


@router.get("/bugs/{bug_id}/comments")
def list_comments(bug_id: str, current_user: dict = Depends(_require_user)):
    bug = _bm.get(bug_id)
    if not bug:
        raise HTTPException(404)
    _check_product_access(bug["product"], current_user)
    return _bm.list_comments(bug_id)


# ── Artifacts ─────────────────────────────────────────────────────────────────

@router.get("/bugs/{bug_id}/artifacts")
def list_artifacts(bug_id: str, current_user: dict = Depends(_require_user)):
    bug = _bm.get(bug_id)
    if not bug:
        raise HTTPException(404)
    _check_product_access(bug["product"], current_user)
    return _bm.list_artifacts(bug_id)


@router.post("/bugs/{bug_id}/artifacts")
async def upload_artifact(
    bug_id: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(_require_user),
):
    bug = _bm.get(bug_id)
    if not bug:
        raise HTTPException(404)
    _check_product_access(bug["product"], current_user)

    import uuid as _uuid
    aid = str(_uuid.uuid4())
    mime = file.content_type or mimetypes.guess_type(file.filename or "")[0] or "application/octet-stream"
    artifact_type = _infer_artifact_type(mime, file.filename or "")

    dest = _bm.artifact_storage_path(bug["product"], bug_id, aid, file.filename or "file")
    data = await file.read()
    max_bytes = BUG_ARTIFACT_MAX_MB * 1024 * 1024
    if len(data) > max_bytes:
        raise HTTPException(400, f"File exceeds {BUG_ARTIFACT_MAX_MB} MB limit")

    dest.write_bytes(data)
    rel_path = str(dest.relative_to(ROOT))
    return _bm.add_artifact(
        bug_id=bug_id,
        filename=file.filename or "file",
        artifact_type=artifact_type,
        mime_type=mime,
        size_bytes=len(data),
        storage_path=rel_path,
        uploaded_by=current_user.get("name", ""),
    )


@router.get("/bugs/{bug_id}/artifacts/{artifact_id}")
def download_artifact(bug_id: str, artifact_id: str, current_user: dict = Depends(_require_user)):
    bug = _bm.get(bug_id)
    if not bug:
        raise HTTPException(404)
    _check_product_access(bug["product"], current_user)
    art = _bm.get_artifact(artifact_id)
    if not art or art["bug_id"] != bug_id:
        raise HTTPException(404)
    path = ROOT / art["storage_path"]
    if not path.exists():
        raise HTTPException(404, "Artifact file not found on disk")
    return FileResponse(
        str(path),
        media_type=art["mime_type"] or "application/octet-stream",
        filename=art["filename"],
    )


@router.delete("/bugs/{bug_id}/artifacts/{artifact_id}")
def delete_artifact(bug_id: str, artifact_id: str, current_user: dict = Depends(_require_user)):
    bug = _bm.get(bug_id)
    if not bug:
        raise HTTPException(404)
    _check_product_access(bug["product"], current_user)
    art = _bm.get_artifact(artifact_id)
    if not art or art["bug_id"] != bug_id:
        raise HTTPException(404)
    _bm.delete_artifact(artifact_id)
    return {"deleted": artifact_id}


# ── Incident report ───────────────────────────────────────────────────────────

@router.get("/bugs/{bug_id}/report")
def bug_report(
    bug_id: str,
    format: str = "html",
    current_user: dict = Depends(_require_user),
):
    bug = _bm.get(bug_id)
    if not bug:
        raise HTTPException(404)
    _check_product_access(bug["product"], current_user)
    html = _render_report_html(bug)
    if format == "pdf":
        pdf = _to_pdf(html)
        if pdf is None:
            raise HTTPException(500, "WeasyPrint not installed. Run: pip install weasyprint")
        filename = f"incident_report_{bug_id[:8]}.pdf"
        return Response(pdf, media_type="application/pdf",
                        headers={"Content-Disposition": f'attachment; filename="{filename}"'})
    return Response(html, media_type="text/html")


# ── Create from run failure ───────────────────────────────────────────────────

@router.post("/bugs/from-run/{run_id}")
def create_bug_from_run(
    run_id: str,
    test_id: str = "",
    current_user: dict = Depends(_require_user),
):
    """Pre-fill a bug from a specific test run. test_id narrows to one failure."""
    from core.run_manager import RunManager
    rm = RunManager()
    run = rm.get_run(run_id)
    if not run:
        raise HTTPException(404, "Run not found")
    _check_product_access(run["product"], current_user)

    failures = run.get("failures", [])
    if test_id:
        failures = [f for f in failures if f.get("test_id") == test_id]
    f = failures[0] if failures else {}

    title = f"[{run['domain'].upper()}] {f.get('test_id', 'Test failure')} failed"
    actual = f.get("summary", "")
    suggestion = f.get("suggestion", "")
    description = suggestion if suggestion else ""
    raw_cat = f.get("category") or f.get("classification", "")
    bug_type = "regression" if raw_cat in ("flaky", "regression") else "functional"

    return _bm.create(
        product=run["product"],
        title=title,
        description=description,
        reporter=current_user.get("name", ""),
        component=run.get("domain", ""),
        environment=run.get("run_config_snapshot", {}).get("environment", ""),
        actual_result=actual,
        linked_run_id=run_id,
        bug_type=bug_type,
    )


# ── Helpers ───────────────────────────────────────────────────────────────────

def _all_products() -> list[str]:
    try:
        from dashboard.routers.config._helpers import _load_config
        return [p["name"] for p in _load_config().get("products", []) if p.get("active", True)]
    except Exception:
        return []


def _check_product_access(product: str, current_user: dict) -> None:
    if current_user.get("admin"):
        return
    visible = set(user_products(current_user, _all_products()))
    if product not in visible:
        raise HTTPException(403, "Product not accessible")


def _to_pdf(html: str) -> bytes | None:
    try:
        from weasyprint import HTML
        return HTML(string=html).write_pdf()
    except Exception:
        return None


def _render_report_html(bug: dict) -> str:
    from datetime import datetime, timezone
    from jinja2 import Environment, FileSystemLoader
    env = Environment(autoescape=True,
                      loader=FileSystemLoader(str(ROOT / "dashboard" / "templates")))
    tpl = env.get_template("bug_report_pdf.html")
    history = _bm.get_history(bug["id"])
    comments = _bm.list_comments(bug["id"])
    artifacts = _bm.list_artifacts(bug["id"])
    return tpl.render(
        bug=bug,
        history=history,
        comments=comments,
        artifacts=artifacts,
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    )


def bug_counts_for_product(product: str) -> dict[str, int]:
    """Used by pages that want open/total bug counts per product."""
    return _bm.counts_by_state(product)
