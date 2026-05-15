"""Test assignment routes."""
from __future__ import annotations

import csv
import io
from typing import List

from fastapi import APIRouter, File, Query, Request, UploadFile
from fastapi.responses import HTMLResponse, Response

from dashboard.routers.config._helpers import (
    _all_tests,
    _load_assignments,
    _load_config,
    _save_assignments,
    templates,
)

router = APIRouter()


def _apply_filters(tests, assignments, search="", filter_labels=None,
                   filter_priority="", filter_owner="", filter_jira_exists=""):
    if search:
        tests = [t for t in tests if search.lower() in t["name"].lower()]
    if filter_labels:
        tests = [t for t in tests if any(
            lbl in assignments.get(t["name"], {}).get("labels", []) for lbl in filter_labels
        )]
    if filter_priority:
        tests = [t for t in tests if assignments.get(t["name"], {}).get("priority") == filter_priority]
    if filter_owner:
        tests = [t for t in tests if
                 assignments.get(t["name"], {}).get("custom_fields", {}).get("owner", "") == filter_owner]
    if filter_jira_exists == "1":
        tests = [t for t in tests if assignments.get(t["name"], {}).get("custom_fields", {}).get("jira_ticket", "")]
    return tests


def _assignments_ctx(request, tests, assignments, cfg, product, search,
                     filter_labels, filter_priority, filter_owner, filter_jira_exists,
                     saved_test="", bulk_result=None):
    return templates.TemplateResponse(request, "partials/config_assignments.html", context={
        "request": request,
        "tests": tests,
        "assignments": assignments,
        "labels": cfg.get("labels", []),
        "priorities": cfg.get("priorities", []),
        "custom_fields": cfg.get("custom_fields", []),
        "users": cfg.get("users", []),
        "filter_product": product,
        "search": search,
        "filter_labels": filter_labels or [],
        "filter_priority": filter_priority,
        "filter_owner": filter_owner,
        "filter_jira_exists": filter_jira_exists,
        "saved_test": saved_test,
        "bulk_result": bulk_result,
    })


@router.get("/ui/config/assignments", response_class=HTMLResponse)
async def assignments_partial(
    request: Request, product: str = "", search: str = "",
    filter_labels: List[str] = Query(default=[]),
    filter_priority: str = "", filter_owner: str = "", filter_jira_exists: str = "",
):
    assignments = _load_assignments()
    cfg = _load_config()
    tests = _all_tests()
    if product:
        tests = [t for t in tests if t["product"] == product]
    tests = _apply_filters(tests, assignments, search, filter_labels, filter_priority, filter_owner, filter_jira_exists)
    return _assignments_ctx(request, tests, assignments, cfg, product, search,
                            filter_labels, filter_priority, filter_owner, filter_jira_exists)


@router.get("/ui/assignments/export")
async def assignments_export():
    assignments = _load_assignments()
    cfg = _load_config()
    cf_names = [f["name"] for f in cfg.get("custom_fields", [])]
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=["test_name", "labels", "priority"] + cf_names)
    writer.writeheader()
    for test_name, asgn in sorted(assignments.items()):
        row = {"test_name": test_name, "labels": ",".join(asgn.get("labels", [])), "priority": asgn.get("priority", "")}
        for cf in cf_names:
            row[cf] = asgn.get("custom_fields", {}).get(cf, "")
        writer.writerow(row)
    return Response(
        content=out.getvalue(), media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=test_assignments.csv"},
    )


@router.get("/ui/assignments/csv-template")
async def assignments_csv_template_v2():
    cfg = _load_config()
    cf_names = [f["name"] for f in cfg.get("custom_fields", [])]
    header = ",".join(["test_name", "labels", "priority"] + cf_names)
    example = ",".join(["test_example_function", '"sanity,regression"', "P1"] + ["" for _ in cf_names])
    return Response(
        content=header + "\n" + example + "\n", media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=assignments_template.csv"},
    )


@router.get("/ui/assignments/list", response_class=HTMLResponse)
async def assignments_list_partial(
    request: Request, product: str = "", search: str = "",
    filter_labels: List[str] = Query(default=[]),
    filter_priority: str = "", filter_owner: str = "", filter_jira_exists: str = "",
):
    assignments = _load_assignments()
    cfg = _load_config()
    tests = _all_tests()
    if product:
        tests = [t for t in tests if t["product"] == product]
    tests = _apply_filters(tests, assignments, search, filter_labels, filter_priority, filter_owner, filter_jira_exists)
    return templates.TemplateResponse(request, "partials/assignment_list.html", context={
        "request": request, "tests": tests, "assignments": assignments,
        "labels": cfg.get("labels", []), "priorities": cfg.get("priorities", []),
        "search": search, "filter_product": product, "filter_labels": filter_labels,
        "filter_priority": filter_priority, "filter_owner": filter_owner,
        "filter_jira_exists": filter_jira_exists,
    })


@router.post("/ui/assignments/bulk-upload", response_class=HTMLResponse)
async def assignments_bulk_upload_v2(request: Request, file: UploadFile = File(...)):
    content = (await file.read()).decode("utf-8", errors="replace")
    reader = csv.DictReader(io.StringIO(content))
    known_tests = {t["name"] for t in _all_tests()}
    assignments = _load_assignments()
    cfg = _load_config()
    updated = 0
    skipped: list[str] = []
    for row in reader:
        test_name = (row.get("test_name") or "").strip()
        if not test_name or test_name not in known_tests:
            if test_name:
                skipped.append(test_name)
            continue
        existing = assignments.get(test_name, {"labels": [], "priority": "", "custom_fields": {}})
        raw_labels = (row.get("labels") or "").strip()
        if raw_labels:
            new_labels = [lbl.strip() for lbl in raw_labels.split(",") if lbl.strip()]
            existing["labels"] = list(dict.fromkeys(existing.get("labels", []) + new_labels))
        if priority := (row.get("priority") or "").strip():
            existing["priority"] = priority
        cf = existing.get("custom_fields", {})
        for f in cfg.get("custom_fields", []):
            if val := (row.get(f["name"]) or "").strip():
                cf[f["name"]] = val
        existing["custom_fields"] = cf
        assignments[test_name] = existing
        updated += 1
    _save_assignments(assignments)
    tests = _all_tests()
    bulk_result = {"updated": updated, "skipped": len(skipped), "skipped_names": skipped[:10]}
    return templates.TemplateResponse(request, "partials/assignment_list.html", context={
        "request": request, "tests": tests, "assignments": assignments,
        "labels": cfg.get("labels", []), "priorities": cfg.get("priorities", []),
        "search": "", "filter_product": "", "filter_labels": [],
        "filter_priority": "", "filter_owner": "", "filter_jira_exists": "",
        "bulk_result": bulk_result,
    })


@router.get("/ui/assignments/form", response_class=HTMLResponse)
async def assignment_form_partial(request: Request, test_name: str):
    assignments = _load_assignments()
    cfg = _load_config()
    return templates.TemplateResponse(request, "partials/assignment_form.html", context={
        "request": request, "test_name": test_name,
        "asgn": assignments.get(test_name, {}),
        "labels": cfg.get("labels", []), "priorities": cfg.get("priorities", []),
        "custom_fields": cfg.get("custom_fields", []), "users": cfg.get("users", []),
        "saved": False,
    })


@router.post("/ui/assignments/save", response_class=HTMLResponse)
async def assignments_save_v2(request: Request):
    form = await request.form()
    test_name = form.get("test_name", "")
    cfg = _load_config()
    custom_fields = {f["name"]: form.get(f"cf_{f['name']}", "") for f in cfg.get("custom_fields", [])}
    assignments = _load_assignments()
    assignments[test_name] = {"labels": form.getlist("labels"), "priority": form.get("priority", ""), "custom_fields": custom_fields}
    _save_assignments(assignments)
    return templates.TemplateResponse(request, "partials/assignment_form.html", context={
        "request": request, "test_name": test_name,
        "asgn": assignments[test_name],
        "labels": cfg.get("labels", []), "priorities": cfg.get("priorities", []),
        "custom_fields": cfg.get("custom_fields", []), "users": cfg.get("users", []),
        "saved": True,
    })


@router.get("/ui/config/assignments/csv-template")
async def assignments_csv_template():
    return Response(
        content="test_name,labels,priority,owner,jira_ticket\n"
                'test_example_function,"sanity,regression",P1,Jane Smith,PROJ-123\n',
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=assignments_template.csv"},
    )


@router.post("/ui/config/assignments/bulk-upload", response_class=HTMLResponse)
async def assignments_bulk_upload(request: Request, file: UploadFile = File(...)):
    content = (await file.read()).decode("utf-8", errors="replace")
    reader = csv.DictReader(io.StringIO(content))
    known_tests = {t["name"] for t in _all_tests()}
    assignments = _load_assignments()
    cfg = _load_config()
    updated = 0
    skipped: list[str] = []
    for row in reader:
        test_name = (row.get("test_name") or "").strip()
        if not test_name or test_name not in known_tests:
            if test_name:
                skipped.append(test_name)
            continue
        existing = assignments.get(test_name, {"labels": [], "priority": "", "custom_fields": {}})
        raw_labels = (row.get("labels") or "").strip()
        if raw_labels:
            new_labels = [lbl.strip() for lbl in raw_labels.split(",") if lbl.strip()]
            existing["labels"] = list(dict.fromkeys(existing.get("labels", []) + new_labels))
        if priority := (row.get("priority") or "").strip():
            existing["priority"] = priority
        cf = existing.get("custom_fields", {})
        for field_name in ("owner", "jira_ticket"):
            if val := (row.get(field_name) or "").strip():
                cf[field_name] = val
        existing["custom_fields"] = cf
        assignments[test_name] = existing
        updated += 1
    _save_assignments(assignments)
    tests = _all_tests()
    bulk_result = {"updated": updated, "skipped": len(skipped), "skipped_names": skipped[:10]}
    return _assignments_ctx(request, tests, assignments, cfg, "", "", [], "", "", "",
                            bulk_result=bulk_result)


@router.post("/ui/config/assignments/save", response_class=HTMLResponse)
async def assignments_save(request: Request):
    form = await request.form()
    test_name = form.get("test_name", "")
    product = form.get("filter_product", "")
    search = form.get("search", "")
    filter_labels = form.getlist("filter_labels")
    filter_priority = form.get("filter_priority", "")
    filter_owner = form.get("filter_owner", "")
    filter_jira_exists = form.get("filter_jira_exists", "")
    cfg = _load_config()
    custom_fields = {f["name"]: form.get(f"cf_{f['name']}", "") for f in cfg.get("custom_fields", [])}
    assignments = _load_assignments()
    assignments[test_name] = {"labels": form.getlist("labels"), "priority": form.get("priority", ""), "custom_fields": custom_fields}
    _save_assignments(assignments)
    tests = _all_tests()
    if product:
        tests = [t for t in tests if t["product"] == product]
    tests = _apply_filters(tests, assignments, search, filter_labels, filter_priority, filter_owner, filter_jira_exists)
    return _assignments_ctx(request, tests, assignments, cfg, product, search,
                            filter_labels, filter_priority, filter_owner, filter_jira_exists,
                            saved_test=test_name)
