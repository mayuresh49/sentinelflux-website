"""API contract validation module — OpenAPI spec-driven request/response validation."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import requests as _requests
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from core.contract_manager import ContractManager
from dashboard.routers.auth import require_user, user_products
from dashboard.routers.config._helpers import _load_config, _require_admin

router = APIRouter(tags=["contract"])

_ROOT = Path(__file__).resolve().parent.parent.parent
_cm = ContractManager()


def _contract_products(current_user: dict) -> list[str]:
    cfg = _load_config()
    all_prods = [p["name"] for p in cfg.get("products", []) if p.get("contract_enabled")]
    return user_products(current_user, all_prods)


def _check_product_access(product: str, current_user: dict) -> None:
    if product not in _contract_products(current_user):
        raise HTTPException(403, detail="Access denied or contract validation not enabled for this product")


# ── Pydantic models ───────────────────────────────────────────────────────────

class CreateEngBody(BaseModel):
    product: str
    name: str
    spec_source: str
    base_url: str
    auth_header: str = ""


class PatchEngBody(BaseModel):
    name: str | None = None
    spec_source: str | None = None
    base_url: str | None = None
    auth_header: str | None = None


# ── PDF helper ────────────────────────────────────────────────────────────────

def _to_pdf(html: str) -> bytes | None:
    try:
        from weasyprint import HTML
        return HTML(string=html).write_pdf()
    except Exception:
        return None


def _render_report_html(eng: dict) -> str:
    from jinja2 import Environment, FileSystemLoader
    env = Environment(autoescape=True,
                      loader=FileSystemLoader(str(_ROOT / "dashboard" / "templates")))
    tpl = env.get_template("contract_report_pdf.html")
    return tpl.render(eng=eng,
                      generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))


# ── engagement CRUD ───────────────────────────────────────────────────────────

@router.post("/contract/engagements")
def create_engagement(body: CreateEngBody,
                      current_user: dict = Depends(require_user)) -> dict:
    _check_product_access(body.product, current_user)
    return _cm.create(body.product, body.name, body.spec_source, body.base_url,
                      body.auth_header, current_user.get("name", "unknown"))


@router.get("/contract/engagements")
def list_engagements(product: str,
                     current_user: dict = Depends(require_user)) -> list[dict]:
    _check_product_access(product, current_user)
    return _cm.list_engagements(product)


@router.get("/contract/engagement/{eng_id}")
def get_engagement(eng_id: str, product: str,
                   current_user: dict = Depends(require_user)) -> dict:
    _check_product_access(product, current_user)
    eng = _cm.get(product, eng_id)
    if not eng:
        raise HTTPException(404, detail="Engagement not found")
    return eng


@router.patch("/contract/engagement/{eng_id}")
def patch_engagement(eng_id: str, product: str, body: PatchEngBody,
                     current_user: dict = Depends(require_user)) -> dict:
    _check_product_access(product, current_user)
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    eng = _cm.patch(product, eng_id, **updates)
    if not eng:
        raise HTTPException(404, detail="Engagement not found")
    return eng


@router.delete("/contract/engagement/{eng_id}")
def delete_engagement(eng_id: str, product: str,
                      _: dict = Depends(_require_admin)) -> dict:
    if not _cm.delete(product, eng_id):
        raise HTTPException(404, detail="Engagement not found")
    return {"deleted": True}


# ── run management ────────────────────────────────────────────────────────────

@router.post("/contract/engagement/{eng_id}/run")
def trigger_run(eng_id: str, product: str,
                background_tasks: BackgroundTasks,
                current_user: dict = Depends(require_user)) -> dict:
    _check_product_access(product, current_user)
    eng = _cm.get(product, eng_id)
    if not eng:
        raise HTTPException(404, detail="Engagement not found")
    run = _cm.add_run(product, eng_id, current_user.get("name", "unknown"))
    if not run:
        raise HTTPException(500, detail="Failed to create run record")
    background_tasks.add_task(_execute_contract_run, product, eng_id, run["run_id"],
                               eng["spec_source"], eng["base_url"], eng.get("auth_header", ""))
    return run


@router.delete("/contract/engagement/{eng_id}/run/{run_id}")
def delete_run(eng_id: str, run_id: str, product: str,
               current_user: dict = Depends(require_user)) -> dict:
    _check_product_access(product, current_user)
    eng = _cm.get(product, eng_id)
    if not eng:
        raise HTTPException(404, detail="Engagement not found")
    target = next((r for r in eng.get("runs", []) if r["run_id"] == run_id), None)
    if target and target.get("status") in ("queued", "running"):
        raise HTTPException(400, detail="Cannot delete a run that is currently active")
    if not _cm.delete_run(product, eng_id, run_id):
        raise HTTPException(404, detail="Run not found")
    return _cm.get(product, eng_id)


# ── report ────────────────────────────────────────────────────────────────────

@router.get("/contract/engagement/{eng_id}/report")
def download_report(eng_id: str, product: str, format: str = "pdf",
                    current_user: dict = Depends(require_user)) -> Response:
    _check_product_access(product, current_user)
    eng = _cm.get(product, eng_id)
    if not eng:
        raise HTTPException(404, detail="Engagement not found")
    html = _render_report_html(eng)
    if format == "pdf":
        pdf = _to_pdf(html)
        if pdf is None:
            raise HTTPException(500, detail="WeasyPrint not installed")
        return Response(pdf, media_type="application/pdf",
                        headers={"Content-Disposition": f'attachment; filename="contract_report_{product}_{eng_id}.pdf"'})
    return Response(html, media_type="text/html")


# ── execution ─────────────────────────────────────────────────────────────────

def _execute_contract_run(product: str, eng_id: str, run_id: str,
                          spec_source: str, base_url: str, auth_header: str) -> None:
    _cm.patch_run(product, eng_id, run_id, status="running")
    try:
        spec = _load_spec(spec_source)
        results = _validate_endpoints(spec, base_url, auth_header)
        passed = sum(1 for r in results if r["passed"])
        failed = len(results) - passed
        _cm.patch_run(product, eng_id, run_id,
                      status="completed",
                      finished_at=datetime.now(timezone.utc).isoformat(),
                      endpoints_tested=len(results),
                      passed=passed,
                      failed=failed,
                      results=results)
    except Exception as exc:
        _cm.patch_run(product, eng_id, run_id,
                      status="failed",
                      finished_at=datetime.now(timezone.utc).isoformat(),
                      error=str(exc))


def _load_spec(spec_source: str) -> dict:
    if spec_source.startswith("http://") or spec_source.startswith("https://"):
        resp = _requests.get(spec_source, timeout=30)
        resp.raise_for_status()
        ct = resp.headers.get("content-type", "")
        if "yaml" in ct or spec_source.endswith(".yaml") or spec_source.endswith(".yml"):
            import yaml
            return yaml.safe_load(resp.text)
        return resp.json()
    p = Path(spec_source)
    if not p.exists():
        raise FileNotFoundError(f"Spec file not found: {spec_source}")
    if p.suffix in (".yaml", ".yml"):
        import yaml
        return yaml.safe_load(p.read_text())
    return json.loads(p.read_text())


def _validate_endpoints(spec: dict, base_url: str, auth_header: str) -> list[dict]:
    base = base_url.rstrip("/")
    headers: dict[str, str] = {}
    if auth_header:
        headers["Authorization"] = auth_header

    # resolve servers base path from spec if present
    servers = spec.get("servers", [])
    spec_base_path = ""
    if servers:
        server_url = servers[0].get("url", "")
        if server_url.startswith("/"):
            spec_base_path = server_url.rstrip("/")

    results = []
    paths = spec.get("paths", {})
    for path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue
        for method, op in path_item.items():
            if method not in ("get", "post", "put", "delete", "patch", "head", "options"):
                continue
            if not isinstance(op, dict):
                continue

            # resolve expected success status codes
            response_codes = op.get("responses", {})
            expected_statuses = [int(c) for c in response_codes if c.isdigit() and int(c) < 400]
            if not expected_statuses:
                expected_statuses = [200]

            # skip paths with required path params that we can't fill
            has_required_path_param = any(
                p.get("in") == "path" and p.get("required", True)
                for p in op.get("parameters", []) + path_item.get("parameters", [])
                if isinstance(p, dict)
            )
            if has_required_path_param:
                results.append({
                    "method": method.upper(),
                    "path": path,
                    "skipped": True,
                    "skip_reason": "Required path parameters not provided",
                    "passed": True,
                    "issues": [],
                })
                continue

            url = base + spec_base_path + path
            issues: list[str] = []
            actual_status = None
            schema_valid = True
            schema_issues: list[str] = []

            try:
                resp = _requests.request(method.upper(), url, headers=headers, timeout=15)
                actual_status = resp.status_code

                if actual_status not in expected_statuses:
                    issues.append(f"Status {actual_status} not in expected {expected_statuses}")

                # schema validation for success responses
                if actual_status < 400:
                    resp_schema = (response_codes.get(str(actual_status)) or {}).get("content", {})
                    json_schema = (resp_schema.get("application/json") or {}).get("schema")
                    if json_schema and resp.headers.get("content-type", "").startswith("application/json"):
                        try:
                            import jsonschema
                            jsonschema.validate(resp.json(), json_schema)
                        except jsonschema.ValidationError as ve:
                            schema_valid = False
                            schema_issues.append(ve.message[:200])
                        except Exception:
                            pass

            except _requests.ConnectionError:
                issues.append(f"Connection refused to {url}")
                schema_valid = False
            except _requests.Timeout:
                issues.append("Request timed out")
                schema_valid = False
            except Exception as exc:
                issues.append(str(exc)[:150])
                schema_valid = False

            all_issues = issues + schema_issues
            results.append({
                "method": method.upper(),
                "path": path,
                "skipped": False,
                "expected_status": expected_statuses[0],
                "actual_status": actual_status,
                "schema_valid": schema_valid,
                "issues": all_issues,
                "passed": not all_issues,
            })
    return results
