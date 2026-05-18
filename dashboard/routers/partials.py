from __future__ import annotations

import html as html_lib
import uuid
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Optional

import yaml
from fastapi import APIRouter, BackgroundTasks, Depends, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from core.activity_log import ActivityLog
from core.approval_manager import ApprovalManager
from core.db import get_conn
from dashboard.routers.approval_dispatch import dispatch as _dispatch
from dashboard.routers.auth import require_user, user_products
from dashboard.routers.kb import _list_products
from utils.paths import ROOT as _ROOT_DIR

router = APIRouter(prefix="/ui", tags=["partials"])
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))

_alog = ActivityLog()
_am = ApprovalManager()


_ACT_PAGE_SIZE = 50

@router.get("/activities", response_class=HTMLResponse)
async def activities_partial(
    request: Request,
    agent: Optional[str] = None,
    domain: Optional[str] = None,
    product: Optional[str] = None,
    requires_human: Optional[str] = None,
    page: int = 1,
    current_user: dict = Depends(require_user),
):
    rh: Optional[bool] = None
    if requires_human == "true":
        rh = True
    elif requires_human == "false":
        rh = False

    visible = user_products(current_user, _list_products())
    if product and product not in visible:
        product = None

    all_filtered = list(reversed(_alog.filter(
        agent=agent or None,
        domain=domain or None,
        product=product or None,
        requires_human=rh,
    )))
    if not current_user.get("admin"):
        all_filtered = [e for e in all_filtered if e.get("product") in visible]
    total = len(all_filtered)
    total_pages = max(1, (total + _ACT_PAGE_SIZE - 1) // _ACT_PAGE_SIZE)
    page = max(1, min(page, total_pages))
    return templates.TemplateResponse(request, "partials/activities_rows.html", context={
        "request": request,
        "entries": all_filtered[(page - 1) * _ACT_PAGE_SIZE: page * _ACT_PAGE_SIZE],
        "page": page,
        "total_pages": total_pages,
        "total": total,
        "filter_agent": agent or "",
        "filter_domain": domain or "",
        "filter_product": product or "",
        "filter_requires_human": requires_human or "",
    })


@router.get("/docs/content", response_class=HTMLResponse)
async def doc_content(product: str, domain: str, feature: str):
    import markdown
    path = _ROOT_DIR / "products" / product / "docs" / "test_cases" / domain / f"{feature}.md"
    if not path.exists():
        return HTMLResponse('<p class="text-red-500 text-sm">Document not found.</p>')
    content = markdown.markdown(
        path.read_text(encoding="utf-8"),
        extensions=["fenced_code", "tables", "toc"],
    )
    return HTMLResponse(f'<div class="markdown-content fade-in">{content}</div>')


def _tc_view_ctx(request: Request, product: str, domain: str, feature: str, tc_id: str) -> dict | HTMLResponse:
    import re as _re
    import markdown as _md
    from dashboard.routers.docs import _parse_tc_block, _parse_tc_index
    path = _ROOT_DIR / "products" / product / "docs" / "test_cases" / domain / f"{feature}.md"
    if not path.exists():
        return HTMLResponse('<p class="text-red-500 text-sm p-4">Document not found.</p>')
    content = path.read_text(encoding="utf-8")
    meta = next((t for t in _parse_tc_index(content) if t["id"] == tc_id), {})
    block = _parse_tc_block(content, tc_id)
    if not block:
        return HTMLResponse(f'<p class="text-slate-400 text-sm p-4">{tc_id} not found in document.</p>')

    def _extract(field: str) -> str:
        m = _re.search(rf'\*\*{field}:\*\*\s*([^\n]+)', block, _re.IGNORECASE)
        return m.group(1).strip() if m else ""

    body_md = _re.sub(r'^###[^\n]+\n', '', block).strip()
    return {
        "request": request, "tc_id": tc_id, "meta": meta,
        "product": product, "domain": domain, "feature": feature,
        "priority": _extract("Priority"),
        "test_type": _extract("Test Type"),
        "owner": _extract("Owner"),
        "body_md": body_md,
        "html": _md.markdown(body_md, extensions=["fenced_code", "tables"]),
    }


@router.get("/docs/test-case", response_class=HTMLResponse)
async def tc_view(request: Request, product: str, domain: str, feature: str, tc_id: str):
    ctx = _tc_view_ctx(request, product, domain, feature, tc_id)
    if isinstance(ctx, HTMLResponse):
        return ctx
    return templates.TemplateResponse(request, "partials/doc_tc_view.html", context=ctx)


@router.get("/docs/test-case/edit", response_class=HTMLResponse)
async def tc_edit(request: Request, product: str, domain: str, feature: str, tc_id: str):
    ctx = _tc_view_ctx(request, product, domain, feature, tc_id)
    if isinstance(ctx, HTMLResponse):
        return ctx
    return templates.TemplateResponse(request, "partials/doc_tc_edit.html", context=ctx)


@router.post("/docs/test-case/save", response_class=HTMLResponse)
async def tc_save(
    request: Request,
    product: str = Form(...), domain: str = Form(...),
    feature: str = Form(...), tc_id: str = Form(...),
    body_md: str = Form(...),
):
    import re as _re
    from dashboard.routers.docs import _parse_tc_block
    path = _ROOT_DIR / "products" / product / "docs" / "test_cases" / domain / f"{feature}.md"
    if not path.exists():
        return HTMLResponse('<p class="text-red-500 text-sm p-4">File not found.</p>')
    content = path.read_text(encoding="utf-8")
    detail_match = _re.search(r'^##\s+(Detailed\s+)?Test Cases', content, _re.MULTILINE | _re.IGNORECASE)
    before = content[:detail_match.end()] if detail_match else ""
    section = content[detail_match.end():] if detail_match else content
    pattern = rf'^(###\s+{_re.escape(tc_id)}\b[^\n]*\n)((?:(?!^###)[\s\S])*)'
    new_body = body_md.strip() + "\n\n"
    new_section, n = _re.subn(pattern, lambda m: m.group(1) + new_body, section, flags=_re.MULTILINE)
    if not n:
        return HTMLResponse(f'<p class="text-red-500 text-sm p-4">Block not found for {tc_id}.</p>')
    path.write_text(before + new_section, encoding="utf-8")
    ctx = _tc_view_ctx(request, product, domain, feature, tc_id)
    if isinstance(ctx, HTMLResponse):
        return ctx
    return templates.TemplateResponse(request, "partials/doc_tc_view.html", context=ctx)


@router.post("/docs/test-case/delete", response_class=HTMLResponse)
async def tc_delete(
    product: str = Form(...), domain: str = Form(...),
    feature: str = Form(...), tc_id: str = Form(...),
):
    import re as _re
    path = _ROOT_DIR / "products" / product / "docs" / "test_cases" / domain / f"{feature}.md"
    if not path.exists():
        return HTMLResponse("", headers={"HX-Redirect": "/docs"})
    content = path.read_text(encoding="utf-8")
    # Remove index table row
    content = "\n".join(
        l for l in content.splitlines()
        if not _re.match(rf'\|\s*{_re.escape(tc_id)}\s*\|', l.strip())
    ) + "\n"
    # Remove detailed block
    detail_match = _re.search(r'^##\s+(Detailed\s+)?Test Cases', content, _re.MULTILINE | _re.IGNORECASE)
    if detail_match:
        before = content[:detail_match.end()]
        section = content[detail_match.end():]
        pattern = rf'^###\s+{_re.escape(tc_id)}\b[^\n]*\n(?:(?!^###)[\s\S])*'
        section = _re.sub(pattern, '', section, flags=_re.MULTILINE)
        content = before + section
    path.write_text(content, encoding="utf-8")
    prod_param = f"?product={product}" if product else ""
    return HTMLResponse("", headers={"HX-Redirect": f"/docs{prod_param}"})


@router.get("/docs/test-case/placeholder", response_class=HTMLResponse)
async def tc_placeholder():
    return HTMLResponse("""
        <div class="h-full flex flex-col items-center justify-center text-center gap-3">
          <svg class="w-10 h-10 text-slate-200" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
          </svg>
          <p class="text-slate-400 text-sm">Select a test case from the list to view its details.</p>
        </div>
    """)


@router.get("/docs/test-case/new", response_class=HTMLResponse)
async def tc_new(request: Request):
    import json as _json
    import yaml as _yaml
    from dashboard.routers.docs import _find_docs, _parse_tc_index

    products = _list_products()

    # Users from config
    cfg_path = _ROOT_DIR / "data" / "config.yaml"
    users: list[str] = []
    if cfg_path.exists():
        cfg = _yaml.safe_load(cfg_path.read_text()) or {}
        users = sorted(u["name"] for u in cfg.get("users", []) if u.get("name"))

    # All docs for visible products (one scan)
    all_docs = [d for d in _find_docs() if d["product"] in products]

    # Features per product/domain
    features_by_pd: dict = {p: {} for p in products}
    for d in all_docs:
        features_by_pd[d["product"]].setdefault(d["domain"], [])
        if d["feature"] not in features_by_pd[d["product"]][d["domain"]]:
            features_by_pd[d["product"]][d["domain"]].append(d["feature"])
    for p in features_by_pd:
        for dom in features_by_pd[p]:
            features_by_pd[p][dom].sort()

    # Product abbreviations from first existing TC ID
    prod_abbrs: dict[str, str] = {}
    for prod in products:
        abbr = prod[:2].upper()
        for d in (x for x in all_docs if x["product"] == prod):
            path = _ROOT_DIR / "products" / prod / "docs" / "test_cases" / d["domain"] / f"{d['feature']}.md"
            if not path.exists():
                continue
            for tc in _parse_tc_index(path.read_text()):
                parts = tc["id"].split("-")
                if len(parts) >= 3:
                    abbr = parts[0]
                    break
            else:
                continue
            break
        prod_abbrs[prod] = abbr

    # Next TC ID per product/domain (scans all IDs across all features)
    dom_abbr = {"web": "WEB", "api": "API", "mobile": "MOB"}
    next_ids: dict = {}
    for prod in products:
        pa = prod_abbrs[prod]
        next_ids[prod] = {}
        for dom, da in dom_abbr.items():
            prefix = f"{pa}-{da}-"
            max_num = 0
            for d in (x for x in all_docs if x["product"] == prod and x["domain"] == dom):
                path = _ROOT_DIR / "products" / prod / "docs" / "test_cases" / dom / f"{d['feature']}.md"
                if not path.exists():
                    continue
                for tc in _parse_tc_index(path.read_text()):
                    if tc["id"].startswith(prefix):
                        num = tc["id"][len(prefix):]
                        if num.isdigit():
                            max_num = max(max_num, int(num))
            next_ids[prod][dom] = f"{prefix}{str(max_num + 1).zfill(3)}"

    # Scripts per product/domain (actual test files only)
    scripts_by_pd: dict = {}
    for prod in products:
        scripts_by_pd[prod] = {}
        for dom in dom_abbr:
            test_dir = _ROOT_DIR / "products" / prod / "tests" / dom
            scripts_by_pd[prod][dom] = sorted(
                f.name for f in test_dir.iterdir()
                if f.name.startswith("test_") and f.suffix == ".py"
            ) if test_dir.is_dir() else []

    # Script usage: which TCs already reference each script
    script_usage: dict = {}
    for d in all_docs:
        prod, dom = d["product"], d["domain"]
        path = _ROOT_DIR / "products" / prod / "docs" / "test_cases" / dom / f"{d['feature']}.md"
        if not path.exists():
            continue
        for tc in _parse_tc_index(path.read_text()):
            s = tc.get("script", "").strip()
            if s and s not in ("—", "-"):
                script_usage.setdefault(f"{prod}/{dom}/{s}", []).append(tc["id"])

    return templates.TemplateResponse(request, "partials/doc_tc_create.html", context={
        "request": request,
        "form_data_json": _json.dumps({
            "products": products,
            "users": users,
            "featuresByProdDomain": features_by_pd,
            "scriptsByProdDomain": scripts_by_pd,
            "nextIds": next_ids,
            "scriptUsage": script_usage,
        }),
    })


@router.post("/docs/test-case/create", response_class=HTMLResponse)
async def tc_create(
    product: str = Form(...), domain: str = Form(...),
    feature: str = Form(...), tc_id: str = Form(...),
    title: str = Form(...), heuristic: str = Form(...),
    test_type: str = Form(""), status: str = Form(...),
    script: str = Form(""), priority: str = Form(""),
    owner: str = Form(""), body_md: str = Form(""),
):
    import re as _re
    from dashboard.routers.docs import _parse_tc_index

    feature = feature.strip().lower().replace(" ", "_")
    tc_id = tc_id.strip().upper()
    script = script.strip() or "—"

    path = _ROOT_DIR / "products" / product / "docs" / "test_cases" / domain / f"{feature}.md"
    path.parent.mkdir(parents=True, exist_ok=True)

    # Build detail block: metadata header + user-supplied body
    meta_lines: list[str] = []
    if priority:  meta_lines.append(f"**Priority:** {priority}")
    if test_type: meta_lines.append(f"**Test Type:** {test_type}")
    if owner:     meta_lines.append(f"**Owner:** {owner}")
    full_body = ("\n".join(meta_lines) + "\n\n" if meta_lines else "") + body_md.strip()
    detail_block = f"### {tc_id} — {title}\n\n{full_body}\n\n"

    if not path.exists():
        if test_type:
            header_row = "| ID | Scenario | Type | Test Type | Status | Script |"
            sep_row    = "|---|---|---|---|---|---|"
            index_row  = f"| {tc_id} | {title} | {heuristic} | {test_type} | {status} | {script} |"
        else:
            header_row = "| ID | Scenario | Type | Status | Script |"
            sep_row    = "|---|---|---|---|---|"
            index_row  = f"| {tc_id} | {title} | {heuristic} | {status} | {script} |"

        feature_title = feature.replace("_", " ").title()
        content = (
            f"# Test Case Document — {feature_title}\n\n"
            f"**Product:** {product}\n"
            f"**Layer:** {domain.upper()}\n"
            f"**Module:** {feature_title}\n\n"
            "---\n\n"
            "## Test Case Index\n\n"
            f"{header_row}\n{sep_row}\n{index_row}\n\n"
            "---\n\n"
            f"## Detailed Test Cases\n\n{detail_block}"
        )
        path.write_text(content, encoding="utf-8")
    else:
        content = path.read_text(encoding="utf-8")

        # Reject duplicate IDs
        existing_ids = {tc["id"] for tc in _parse_tc_index(content)}
        if tc_id in existing_ids:
            return HTMLResponse(
                f'<p class="text-red-500 text-sm p-4">TC ID <strong>{tc_id}</strong> already exists in {feature}.md — choose a different ID.</p>'
            )

        # Detect column count from the separator line that follows the ID header
        lines = content.splitlines()
        in_header = False
        ncols = 5
        for ln in lines:
            s = ln.strip()
            if _re.match(r'\|\s*ID\s*\|', s, _re.IGNORECASE):
                in_header = True
                continue
            if in_header and (s.startswith("|---") or s.startswith("| ---")):
                ncols = s.count("|") - 1
                break

        if ncols >= 6:
            new_row = f"| {tc_id} | {title} | {heuristic} | {test_type} | {status} | {script} |"
        else:
            new_row = f"| {tc_id} | {title} | {heuristic} | {status} | {script} |"

        # Insert row after the last table row in the index
        in_table = False
        last_row_idx = -1
        for i, ln in enumerate(lines):
            s = ln.strip()
            if _re.match(r'\|\s*ID\s*\|', s, _re.IGNORECASE):
                in_table = True
                continue
            if not in_table:
                continue
            if s.startswith("|---") or s.startswith("| ---"):
                continue
            if s.startswith("|"):
                last_row_idx = i
            else:
                break

        if last_row_idx >= 0:
            lines.insert(last_row_idx + 1, new_row)
        content = "\n".join(lines) + "\n"

        # Append detail block (create section if missing)
        if _re.search(r'^##\s+(Detailed\s+)?Test Cases', content, _re.MULTILINE | _re.IGNORECASE):
            content = content.rstrip() + "\n\n" + detail_block
        else:
            content += "\n\n## Detailed Test Cases\n\n" + detail_block

        path.write_text(content, encoding="utf-8")

    prod_param = f"?product={product}" if product else ""
    return HTMLResponse("", headers={"HX-Redirect": f"/docs{prod_param}"})


@router.get("/docs/export")
async def docs_export(
    product: str | None = None, domain: str | None = None,
    feature: str | None = None, format: str = "csv",
):
    import csv, io, re as _re
    from fastapi.responses import StreamingResponse
    from dashboard.routers.docs import _find_docs, _parse_tc_block, _parse_tc_index

    docs = _find_docs(product=product, domain=domain)
    if feature:
        docs = [d for d in docs if d["feature"] == feature]

    headers = ["Product", "Domain", "Module", "TC ID", "Title", "Heuristic",
               "Status", "Priority", "Test Type", "Owner", "Script"]
    rows: list[dict] = []
    for d in docs:
        path = _ROOT_DIR / "products" / d["product"] / "docs" / "test_cases" / d["domain"] / f"{d['feature']}.md"
        if not path.exists():
            continue
        content = path.read_text(encoding="utf-8")
        for tc in _parse_tc_index(content):
            block = _parse_tc_block(content, tc["id"]) or ""
            def _ext(f: str) -> str:
                m = _re.search(rf'\*\*{f}:\*\*\s*([^\n]+)', block, _re.IGNORECASE)
                return m.group(1).strip() if m else ""
            rows.append({
                "Product": d["product"], "Domain": d["domain"],
                "Module": d["feature"].replace("_", " ").title(),
                "TC ID": tc["id"], "Title": tc["title"],
                "Heuristic": tc["heuristic"], "Status": tc["status"],
                "Priority": _ext("Priority"), "Test Type": _ext("Test Type"),
                "Owner": _ext("Owner"), "Script": tc["script"],
            })

    if format == "xlsx":
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Test Cases"
        ws.append(headers)
        for r in rows:
            ws.append([r.get(h, "") for h in headers])
        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        return StreamingResponse(buf,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=test_cases.xlsx"})

    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=headers)
    w.writeheader()
    w.writerows(rows)
    return StreamingResponse(iter([buf.getvalue()]), media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=test_cases.csv"})


@router.get("/scripts/content", response_class=HTMLResponse)
async def script_content(product: str, domain: str, feature: str):
    path = _ROOT_DIR / "products" / product / "tests" / domain / f"test_{feature}.py"
    if not path.exists():
        return HTMLResponse('<p class="text-red-500 text-sm p-4">Script not found.</p>')
    code = html_lib.escape(path.read_text(encoding="utf-8"))
    return HTMLResponse(
        f'<pre class="fade-in"><code class="language-python">{code}</code></pre>'
        "<script>document.querySelectorAll('pre:not(.hljs) code').forEach(el => hljs.highlightElement(el));</script>"
    )


@router.post("/approvals/{approval_id}/approve", response_class=HTMLResponse)
async def approve_partial(approval_id: str, request: Request):
    item = _am.get(approval_id)
    if not item:
        return HTMLResponse(f'<div id="approval-{approval_id}" class="text-red-500 text-sm p-4">Approval not found.</div>')
    _am.resolve(approval_id, decision="approved")
    item = _am.get(approval_id)
    action_result = _dispatch(item, "approved")
    return templates.TemplateResponse(request, "partials/approval_card.html", context={
        "item": item, "action_result": action_result,
    })


@router.post("/approvals/{approval_id}/reject", response_class=HTMLResponse)
async def reject_partial(approval_id: str, request: Request):
    item = _am.get(approval_id)
    if not item:
        return HTMLResponse(f'<div id="approval-{approval_id}" class="text-red-500 text-sm p-4">Approval not found.</div>')
    _am.resolve(approval_id, decision="rejected")
    item = _am.get(approval_id)
    action_result = _dispatch(item, "rejected")
    return templates.TemplateResponse(request, "partials/approval_card.html", context={
        "item": item, "action_result": action_result,
    })


@router.get("/kb/content", response_class=HTMLResponse)
async def kb_content(request: Request, product: str, file: str):
    from dashboard.routers.kb import _product_kb_dir
    path = _product_kb_dir(product) / file
    if not path.exists():
        return HTMLResponse('<p class="text-red-500 text-sm p-4">File not found.</p>')
    content = path.read_text(encoding="utf-8")
    return templates.TemplateResponse(request, "partials/kb_file_editor.html", context={
        "product": product, "filename": file, "content": content,
    })


@router.post("/kb/save", response_class=HTMLResponse)
async def kb_save(
    product: str = Form(...),
    filename: str = Form(...),
    content: str = Form(...),
):
    from dashboard.routers.kb import _product_kb_dir
    path = _product_kb_dir(product) / filename
    if not path.exists():
        return HTMLResponse('<span class="text-red-500 text-xs">File not found</span>')
    path.write_text(content, encoding="utf-8")
    return HTMLResponse('<span class="text-emerald-600 text-xs font-medium">Saved ✓</span>')


@router.post("/pipeline/trigger", response_class=HTMLResponse)
async def pipeline_trigger_partial(request: Request, background_tasks: BackgroundTasks):
    from dashboard.routers.pipeline import TriggerBody, _run, _write_job
    body_data = await request.json()
    body = TriggerBody(**body_data)
    job_id = str(uuid.uuid4())
    job: dict = {
        "id": job_id,
        "started": datetime.now(timezone.utc).isoformat(),
        "product": body.product,
        "feature": body.feature,
        "domain": body.domain,
        "increment_file": body.increment_file,
        "status": "running",
        "output": "",
        "finished": None,
    }
    _write_job(job)
    background_tasks.add_task(_run, job_id, body)
    return templates.TemplateResponse(request, "partials/pipeline_job.html", context={"job": job})


@router.get("/pipeline/job/{job_id}", response_class=HTMLResponse)
async def pipeline_job_partial(request: Request, job_id: str):
    from dashboard.routers.pipeline import _load_jobs
    job = next((j for j in _load_jobs() if j["id"] == job_id), None)
    if not job:
        return HTMLResponse(f'<div id="pipeline-job-{job_id}" class="text-red-500 text-sm p-3">Job not found.</div>')
    return templates.TemplateResponse(request, "partials/pipeline_job.html", context={"job": job})


def _quarantine_groups(filter_product: str | None) -> dict:
    if filter_product:
        rows = get_conn().execute(
            "SELECT * FROM quarantine WHERE product = ?", (filter_product,)
        ).fetchall()
    else:
        rows = get_conn().execute("SELECT * FROM quarantine").fetchall()
    items = [dict(r) for r in rows]
    groups: dict = defaultdict(list)
    for q in sorted(items, key=lambda x: (x.get("product") or "", x.get("domain") or "")):
        groups[(q.get("product") or "—", q.get("domain") or "—")].append(q)
    return dict(groups)


def _quar_ctx(filter_product: str) -> dict:
    return {
        "quarantine_groups": _quarantine_groups(filter_product or None),
        "filter_product": filter_product,
        "all_products": _list_products(),
    }


@router.get("/quarantine/list", response_class=HTMLResponse)
async def quarantine_list_partial(request: Request, product: str | None = None):
    return templates.TemplateResponse(request, "partials/quarantine_list.html",
                                      context=_quar_ctx(product or ""))


@router.post("/quarantine/add", response_class=HTMLResponse)
async def quarantine_add(
    request: Request,
    test_id: str = Form(...),
    product: str = Form(""),
    domain: str = Form(""),
    reason: str = Form("manual"),
    filter_product: str = Form(""),
):
    tid = test_id.strip()
    if tid:
        conn = get_conn()
        existing = conn.execute(
            "SELECT test_id FROM quarantine WHERE test_id = ?", (tid,)
        ).fetchone()
        if not existing:
            conn.execute(
                """INSERT INTO quarantine
                   (test_id, product, domain, reason, quarantined_date, consecutive_passes)
                   VALUES (?, ?, ?, ?, ?, 0)""",
                (tid, product or None, domain or None, reason or "manual", str(date.today())),
            )
            conn.commit()
            _alog.append(
                event_type="approval_action", agent="human",
                product=product or None, domain=domain or None,
                status="success", summary=f"Manually quarantined: {tid}",
            )
    return templates.TemplateResponse(request, "partials/quarantine_list.html",
                                      context=_quar_ctx(filter_product))


@router.post("/quarantine/remove", response_class=HTMLResponse)
async def quarantine_remove(
    request: Request,
    test_id: str = Form(...),
    filter_product: str = Form(""),
):
    tid = test_id.strip()
    if tid:
        conn = get_conn()
        conn.execute("DELETE FROM quarantine WHERE test_id = ?", (tid,))
        conn.commit()
        _alog.append(
            event_type="approval_action", agent="human",
            status="success", summary=f"Manually removed from quarantine: {tid}",
        )
    return templates.TemplateResponse(request, "partials/quarantine_list.html",
                                      context=_quar_ctx(filter_product))


@router.post("/agents/{name}/config", response_class=HTMLResponse)
async def save_agent_config(name: str, request: Request):
    from dashboard.agent_meta import AGENT_META
    _CONFIG_PATH = _ROOT_DIR / "ai" / "context" / "agent_config.yaml"
    meta = AGENT_META.get(name, {})
    if not meta.get("config_params"):
        return HTMLResponse('<span class="text-slate-400 text-xs">No configurable params</span>')
    form = await request.form()
    data: dict = {}
    if _CONFIG_PATH.exists():
        data = yaml.safe_load(_CONFIG_PATH.read_text(encoding="utf-8")) or {}
    agents_cfg = data.get("agents", {})
    agent_cfg = dict(agents_cfg.get(name, {}))
    for param in meta["config_params"]:
        val = form.get(param["name"])
        if val is None:
            continue
        ptype = param["type"]
        if ptype == "bool":
            agent_cfg[param["name"]] = str(val).lower() in ("true", "1", "on", "yes")
        elif ptype == "int":
            try:
                agent_cfg[param["name"]] = int(val)
            except ValueError:
                pass
        elif ptype == "float":
            try:
                agent_cfg[param["name"]] = float(val)
            except ValueError:
                pass
        else:
            agent_cfg[param["name"]] = str(val)
    agents_cfg[name] = agent_cfg
    data["agents"] = agents_cfg
    _CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    _CONFIG_PATH.write_text(yaml.dump(data, default_flow_style=False), encoding="utf-8")
    return HTMLResponse('<span class="text-emerald-600 text-xs font-medium">Saved ✓</span>')
