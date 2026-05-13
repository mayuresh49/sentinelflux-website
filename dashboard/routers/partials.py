from __future__ import annotations

import html as html_lib
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from utils.activity_log import ActivityLog
from utils.approval_manager import ApprovalManager

router = APIRouter(prefix="/ui", tags=["partials"])
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))

_ROOT_DIR = Path(__file__).resolve().parent.parent.parent
_alog = ActivityLog()
_am = ApprovalManager()


@router.get("/activities", response_class=HTMLResponse)
async def activities_partial(
    request: Request,
    agent: Optional[str] = None,
    domain: Optional[str] = None,
    product: Optional[str] = None,
    requires_human: Optional[str] = None,
):
    rh: Optional[bool] = None
    if requires_human == "true":
        rh = True
    elif requires_human == "false":
        rh = False

    entries = _alog.filter(
        agent=agent or None,
        domain=domain or None,
        product=product or None,
        requires_human=rh,
    )
    return templates.TemplateResponse(request, "partials/activities_rows.html", context={
        "entries": list(reversed(entries))[:200],
    })


@router.get("/docs/content", response_class=HTMLResponse)
async def doc_content(product: str, domain: str, feature: str):
    import markdown
    path = _ROOT_DIR / "examples" / product / "docs" / "test_cases" / domain / f"{feature}.md"
    if not path.exists():
        return HTMLResponse('<p class="text-red-500 text-sm">Document not found.</p>')
    content = markdown.markdown(
        path.read_text(encoding="utf-8"),
        extensions=["fenced_code", "tables", "toc"],
    )
    return HTMLResponse(f'<div class="markdown-content fade-in">{content}</div>')


@router.get("/scripts/content", response_class=HTMLResponse)
async def script_content(product: str, domain: str, feature: str):
    path = _ROOT_DIR / "examples" / product / "tests" / domain / f"test_{feature}.py"
    if not path.exists():
        return HTMLResponse('<p class="text-red-500 text-sm p-4">Script not found.</p>')
    code = html_lib.escape(path.read_text(encoding="utf-8"))
    return HTMLResponse(
        f'<pre class="fade-in"><code class="language-python">{code}</code></pre>'
        "<script>document.querySelectorAll('pre:not(.hljs) code').forEach(el => hljs.highlightElement(el));</script>"
    )


@router.post("/approvals/{approval_id}/approve", response_class=HTMLResponse)
async def approve_partial(approval_id: str, request: Request):
    if not _am.get(approval_id):
        return HTMLResponse(f'<div id="approval-{approval_id}" class="text-red-500 text-sm p-4">Approval not found.</div>')
    _am.resolve(approval_id, decision="approved")
    item = _am.get(approval_id)
    return templates.TemplateResponse(request, "partials/approval_card.html", context={"item": item})


@router.post("/approvals/{approval_id}/reject", response_class=HTMLResponse)
async def reject_partial(approval_id: str, request: Request):
    if not _am.get(approval_id):
        return HTMLResponse(f'<div id="approval-{approval_id}" class="text-red-500 text-sm p-4">Approval not found.</div>')
    _am.resolve(approval_id, decision="rejected")
    item = _am.get(approval_id)
    return templates.TemplateResponse(request, "partials/approval_card.html", context={"item": item})
