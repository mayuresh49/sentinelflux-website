"""VAPT module API — engagement lifecycle, scan execution, findings, reports, and certificates."""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel

from core.vapt_manager import VaptManager
from dashboard.routers.auth import require_user, user_products
from dashboard.routers.config._helpers import _load_config, _require_admin

router = APIRouter(tags=["vapt"])

_ROOT = Path(__file__).resolve().parent.parent.parent
_vm = VaptManager()

_VAPT_SUBDIRS: dict[str, str] = {
    "web": "vapt",
    "infra": "vapt_infra",
    "infra_int": "vapt_infra_int",
    "mobile": "vapt_mobile",
}

_SCAN_TYPE_LABELS: dict[str, str] = {
    "web": "Web Application",
    "infra": "Infrastructure (External)",
    "infra_int": "Infrastructure (Internal)",
    "mobile": "Mobile Application",
}

_METHODOLOGY_LABELS: dict[str, str] = {
    "web": "OWASP WSTG v4.2",
    "infra": "OWASP Top 10 / CIS Benchmarks",
    "infra_int": "CIS Benchmarks / NIST SP 800-123 / SSH Hardening",
    "mobile": "OWASP MASVS / MASTG",
}


def _scan_ids_for_type(eng: dict, scan_type: str) -> set[str]:
    return {s["scan_id"] for s in eng.get("scans", []) if s.get("scan_type", "web") == scan_type}


def _findings_for_type(eng: dict, scan_type: str) -> list[dict]:
    ids = _scan_ids_for_type(eng, scan_type)
    return [f for f in eng.get("findings", []) if f.get("scan_id") in ids]


# ── OWASP inference ───────────────────────────────────────────────────────────

_OWASP_RULES: list[tuple[list[str], str, str]] = [
    # A07 — auth + session (checked first; session keywords shouldn't bleed into A05)
    (["without_auth", "no_auth", "unauthenticated", "requires_login", "requires_auth",
      "admin_requires", "session_cookie", "httponly", "samesite", "secure_flag",
      "session_token", "cookie_flag", "session_mgmt",
      # Mobile M4 / MASVS-AUTH
      "m4_auth", "m4_login", "m4_weak", "weak_credential", "brute_force_protection"],
     "A07", "Identification and Authentication Failures"),
    # A03 — injection (XSS listed here; clickjack moved to A05)
    (["xss", "script_execute", "cross_site_script", "reflected_unescaped"],
     "A03", "Injection — Cross-Site Scripting"),
    (["sql", "sqli", "nosql", "injection", "ldap", "ssti", "command_inject",
      "path_traversal", "traversal", "directory_traversal"],
     "A03", "Injection"),
    # A01 — access control + open redirect (redirect is an A01 finding)
    (["idor", "bola", "unauthorized_access", "other_user", "another_user", "another_booking"],
     "A01", "Broken Access Control"),
    (["delete_without", "update_without", "write_without", "admin_panel"],
     "A01", "Broken Access Control"),
    (["csrf", "open_redirect", "forged_request",
      # Mobile M1/M6 — platform issues
      "m1_mobile", "m1_error", "m6_cors", "m6_http_method", "method_override"],
     "A01", "Broken Access Control"),
    # A05 — misconfiguration incl. clickjacking, referrer, infra misconfig, mobile storage
    (["cors", "x_frame", "hsts", "csp", "content_type_options", "server_version",
      "expose", "info_disclosure", "server_header", "header", "clickjack",
      "referrer_policy", "html_comment",
      # Infra (external)
      "default_server", "debug_endpoint", "backup_file",
      "spf_record", "dmarc_record", "zone_transfer",
      "sensitive_port", "service_port", "no_telnet", "no_ftp",
      # Infra (internal — SSH grey-box)
      "permit_root_login", "permit_root", "password_auth", "max_auth_tries",
      "allow_users", "suid_sgid", "sensitive_file_perm", "file_perm", "audit_log",
      # Mobile M2 — storage
      "m2_sensitive", "m2_login", "m2_session", "m2_no_sensitive", "cache_control",
      "no_cacheable", "not_cacheable"],
     "A05", "Security Misconfiguration"),
    # A04, A10, A02, A06
    (["rate_limit", "throttle", "flood", "brute_force", "mass_request"],
     "A04", "Unrestricted Resource Consumption"),
    (["ssrf", "server_side_request", "dns_rebinding"],
     "A10", "Server-Side Request Forgery"),
    (["tls", "https_only", "ssl", "cert", "cipher", "encrypt", "plaintext", "cleartext",
      # Infra TLS + Mobile M3 — network
      "m3_https", "m3_tls", "m3_hsts", "m3_api_cert", "certificate_not_expired",
      "certificate_hostname", "tls_1_0", "tls_1_1", "minimum_version"],
     "A02", "Cryptographic Failures"),
    (["outdated", "vulnerable_component", "dependency", "cve", "version_disclosure"],
     "A06", "Vulnerable and Outdated Components"),
]

_SEVERITY_BY_OWASP = {
    "A01": "High", "A02": "Critical", "A03": "High",
    "A04": "Medium", "A05": "Medium", "A06": "High",
    "A07": "High", "A08": "High", "A09": "Low", "A10": "High",
}

_OWASP_DESCRIPTIONS = {
    "A01": "Tests that access controls are enforced and users cannot act outside their intended permissions.",
    "A02": "Tests for sensitive data exposure due to weak or missing encryption.",
    "A03": "Tests for SQL injection, XSS, command injection, SSTI, and other injection flaws.",
    "A04": "Tests for missing rate limits and controls that prevent resource exhaustion.",
    "A05": "Tests for misconfigured security headers, CORS, verbose error messages, and default credentials.",
    "A06": "Tests for use of components with known published vulnerabilities.",
    "A07": "Tests for broken authentication, weak passwords, poor session management, and credential exposure.",
    "A08": "Tests for insecure deserialization and software/data integrity failures.",
    "A09": "Tests for insufficient logging that could enable breach concealment.",
    "A10": "Tests for SSRF vulnerabilities allowing server-side requests to internal resources.",
}


def _infer_owasp(nodeid: str) -> tuple[str, str]:
    name = nodeid.lower()
    for keywords, ref, category in _OWASP_RULES:
        if any(k in name for k in keywords):
            return ref, category
    return "A05", "Security Misconfiguration"


def _make_title(nodeid: str) -> str:
    fn = nodeid.split("::")[-1]
    fn = re.sub(r"^test_", "", fn)
    fn = re.sub(r"^(A0[1-9]|A10)_", "", fn, flags=re.IGNORECASE)
    return fn.replace("_", " ").title()


# ── authorization helpers ─────────────────────────────────────────────────────

def _vapt_products(current_user: dict) -> list[str]:
    cfg = _load_config()
    all_prods = [p["name"] for p in cfg.get("products", []) if p.get("active", True)]
    visible = set(user_products(current_user, all_prods))
    if current_user.get("admin"):
        return [p["name"] for p in cfg.get("products", [])
                if p.get("active", True) and p.get("vapt_enabled")]
    return [p["name"] for p in cfg.get("products", [])
            if p.get("vapt_enabled") and p["name"] in visible]


def _check_product_access(product: str, current_user: dict) -> None:
    if product not in _vapt_products(current_user):
        raise HTTPException(403, detail="VAPT not enabled for this product or access denied")


# ── request models ────────────────────────────────────────────────────────────

class CreateEngagementBody(BaseModel):
    product: str
    name: str
    client_name: str
    assessor_org: str = "SentinelFlux"


class UpdateScopeBody(BaseModel):
    objectives: str = ""
    methodology: str = ""
    test_types: list[str] = []
    owasp_categories: list[str] = []
    in_scope: list[str] = []
    out_of_scope: list[str] = []
    infra_targets: list[str] = []
    mobile_app_path: str = ""
    ssh_username: str = ""
    ssh_key_path: str = ""
    environment: str = ""
    start_date: str = ""
    end_date: str = ""


class PatchFindingBody(BaseModel):
    status: str | None = None
    description: str | None = None
    remediation: str | None = None


class CertThresholdBody(BaseModel):
    Critical: int = 0
    High: int = 0


# ── engagement endpoints ──────────────────────────────────────────────────────

@router.get("/vapt/products")
def list_vapt_products(current_user: dict = Depends(require_user)) -> list[str]:
    return _vapt_products(current_user)


@router.post("/vapt/engagements")
def create_engagement(body: CreateEngagementBody,
                      current_user: dict = Depends(require_user)) -> dict:
    _check_product_access(body.product, current_user)
    return _vm.create(body.product, body.name, body.client_name,
                      current_user.get("name", "unknown"), body.assessor_org)


@router.get("/vapt/engagements")
def list_engagements(product: str,
                     current_user: dict = Depends(require_user)) -> list[dict]:
    _check_product_access(product, current_user)
    return _vm.list_engagements(product)


@router.get("/vapt/engagement/{eng_id}")
def get_engagement(eng_id: str, product: str,
                   current_user: dict = Depends(require_user)) -> dict:
    _check_product_access(product, current_user)
    eng = _vm.get(product, eng_id)
    if not eng:
        raise HTTPException(404, detail="Engagement not found")
    return eng


@router.delete("/vapt/engagement/{eng_id}")
def delete_engagement(eng_id: str, product: str,
                      _: dict = Depends(_require_admin)) -> dict:
    if not _vm.delete(product, eng_id):
        raise HTTPException(404, detail="Engagement not found")
    return {"deleted": True}


@router.put("/vapt/engagement/{eng_id}/scope")
def update_scope(eng_id: str, product: str, body: UpdateScopeBody,
                 current_user: dict = Depends(require_user)) -> dict:
    _check_product_access(product, current_user)
    eng = _vm.update_scope(product, eng_id, body.model_dump())
    if not eng:
        raise HTTPException(404, detail="Engagement not found")
    return eng


@router.post("/vapt/engagement/{eng_id}/finalize-scope")
def finalize_scope(eng_id: str, product: str,
                   current_user: dict = Depends(require_user)) -> dict:
    _check_product_access(product, current_user)
    eng = _vm.finalize_scope(product, eng_id)
    if not eng:
        raise HTTPException(404, detail="Engagement not found")
    return eng


@router.patch("/vapt/engagement/{eng_id}/certificate-threshold")
def set_cert_threshold(eng_id: str, product: str, body: CertThresholdBody,
                       _: dict = Depends(_require_admin)) -> dict:
    eng = _vm.patch(product, eng_id,
                    certificate_threshold={"Critical": body.Critical, "High": body.High})
    if not eng:
        raise HTTPException(404, detail="Engagement not found")
    return eng


# ── test-suite management ─────────────────────────────────────────────────────

@router.get("/vapt/products/{product}/test-info")
def get_test_info(product: str, scan_type: str = "web",
                  current_user: dict = Depends(require_user)) -> dict:
    _check_product_access(product, current_user)
    from core.vapt_test_generator import VaptTestGenerator
    return VaptTestGenerator.test_info(product, scan_type)


@router.get("/vapt/products/{product}/test-info-all")
def get_all_test_info(product: str,
                      current_user: dict = Depends(require_user)) -> dict:
    _check_product_access(product, current_user)
    from core.vapt_test_generator import VaptTestGenerator
    return VaptTestGenerator.all_test_info(product)


@router.get("/vapt/products/{product}/test-templates")
def get_test_templates(product: str, scan_type: str = "web",
                       current_user: dict = Depends(require_user)) -> list[dict]:
    _check_product_access(product, current_user)
    from core.vapt_test_generator import VaptTestGenerator
    return VaptTestGenerator.template_contents(product, scan_type)


@router.post("/vapt/products/{product}/generate-tests")
def generate_tests(product: str, scan_type: str = "web", force: bool = False,
                   _: dict = Depends(_require_admin)) -> dict:
    from core.vapt_test_generator import VaptTestGenerator
    return VaptTestGenerator.generate(product, scan_type=scan_type, force=force)


# ── scan endpoints ────────────────────────────────────────────────────────────

@router.post("/vapt/engagement/{eng_id}/scan")
def trigger_scan(eng_id: str, product: str,
                 background_tasks: BackgroundTasks,
                 scan_type: str = "web",
                 current_user: dict = Depends(require_user)) -> dict:
    _check_product_access(product, current_user)
    eng = _vm.get(product, eng_id)
    if not eng:
        raise HTTPException(404, detail="Engagement not found")
    if eng["status"] == "scoping":
        raise HTTPException(400, detail="Finalize scope before running a scan")
    if scan_type not in _VAPT_SUBDIRS:
        raise HTTPException(400, detail=f"Invalid scan_type '{scan_type}' — must be one of: {list(_VAPT_SUBDIRS)}")
    scan = _vm.add_scan(product, eng_id, current_user.get("name", "unknown"),
                        is_revalidation=False, scan_type=scan_type)
    if not scan:
        raise HTTPException(500, detail="Failed to create scan record")
    background_tasks.add_task(_execute_vapt_scan, product, eng_id, scan["scan_id"], False, scan_type)
    return scan


@router.post("/vapt/engagement/{eng_id}/revalidate")
def trigger_revalidation(eng_id: str, product: str,
                          background_tasks: BackgroundTasks,
                          scan_type: str = "web",
                          current_user: dict = Depends(require_user)) -> dict:
    _check_product_access(product, current_user)
    eng = _vm.get(product, eng_id)
    if not eng:
        raise HTTPException(404, detail="Engagement not found")
    open_findings = [f for f in eng["findings"] if f["status"] in ("open", "still_open")]
    if not open_findings:
        raise HTTPException(400, detail="No open findings to revalidate")
    if scan_type not in _VAPT_SUBDIRS:
        raise HTTPException(400, detail=f"Invalid scan_type '{scan_type}' — must be one of: {list(_VAPT_SUBDIRS)}")
    scan = _vm.add_scan(product, eng_id, current_user.get("name", "unknown"),
                        is_revalidation=True, scan_type=scan_type)
    if not scan:
        raise HTTPException(500, detail="Failed to create scan record")
    background_tasks.add_task(_execute_vapt_scan, product, eng_id, scan["scan_id"], True, scan_type)
    return scan


# ── findings endpoints ────────────────────────────────────────────────────────

@router.patch("/vapt/engagement/{eng_id}/finding/{finding_id}")
def patch_finding(eng_id: str, finding_id: str, product: str, body: PatchFindingBody,
                  current_user: dict = Depends(require_user)) -> dict:
    _check_product_access(product, current_user)
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    eng = _vm.patch_finding(product, eng_id, finding_id, **updates)
    if not eng:
        raise HTTPException(404, detail="Engagement or finding not found")
    return eng


@router.delete("/vapt/engagement/{eng_id}/scan/{scan_id}")
def delete_scan(eng_id: str, scan_id: str, product: str,
                current_user: dict = Depends(require_user)) -> dict:
    _check_product_access(product, current_user)
    eng = _vm.get(product, eng_id)
    if not eng:
        raise HTTPException(404, detail="Engagement not found")
    target = next((s for s in eng.get("scans", []) if s["scan_id"] == scan_id), None)
    if not target:
        raise HTTPException(404, detail="Scan not found")
    if target.get("status") in ("queued", "running"):
        raise HTTPException(400, detail="Cannot delete a scan that is currently running")
    _vm.delete_scan(product, eng_id, scan_id)
    return _vm.get(product, eng_id)


# ── plan document ─────────────────────────────────────────────────────────────

@router.get("/vapt/engagement/{eng_id}/plan")
def get_plan(eng_id: str, product: str, format: str = "html",
             current_user: dict = Depends(require_user)) -> Response:
    _check_product_access(product, current_user)
    eng = _vm.get(product, eng_id)
    if not eng:
        raise HTTPException(404, detail="Engagement not found")
    if eng["status"] == "scoping":
        raise HTTPException(400, detail="Finalize scope before generating a plan")

    html = _render_plan_html(eng)
    if format == "pdf":
        pdf = _to_pdf(html)
        if pdf is None:
            raise HTTPException(500, detail="WeasyPrint not installed. Run: pip install weasyprint")
        filename = f"vapt_plan_{product}_{eng_id}.pdf"
        return Response(pdf, media_type="application/pdf",
                        headers={"Content-Disposition": f'attachment; filename="{filename}"'})
    return Response(html, media_type="text/html")


# ── report ────────────────────────────────────────────────────────────────────

@router.post("/vapt/engagement/{eng_id}/report")
def generate_report(eng_id: str, product: str, scan_type: str = "web",
                    current_user: dict = Depends(require_user)) -> dict:
    _check_product_access(product, current_user)
    eng = _vm.get(product, eng_id)
    if not eng:
        raise HTTPException(404, detail="Engagement not found")
    now = datetime.now(timezone.utc).isoformat()
    updated = _vm.patch(product, eng_id, report_generated_at=now,
                        status="reported" if eng["status"] == "in_progress" else eng["status"])
    return updated


@router.get("/vapt/engagement/{eng_id}/report")
def download_report(eng_id: str, product: str, format: str = "pdf",
                    scan_type: str = "web",
                    current_user: dict = Depends(require_user)) -> Response:
    _check_product_access(product, current_user)
    eng = _vm.get(product, eng_id)
    if not eng:
        raise HTTPException(404, detail="Engagement not found")
    if not eng.get("report_generated_at"):
        raise HTTPException(400, detail="Generate the report first")

    html = _render_report_html(eng, scan_type)
    if format == "pdf":
        pdf = _to_pdf(html)
        if pdf is None:
            raise HTTPException(500, detail="WeasyPrint not installed. Run: pip install weasyprint")
        filename = f"vapt_report_{product}_{eng_id}_{scan_type}.pdf"
        return Response(pdf, media_type="application/pdf",
                        headers={"Content-Disposition": f'attachment; filename="{filename}"'})
    return Response(html, media_type="text/html")


# ── certificate ───────────────────────────────────────────────────────────────

@router.get("/vapt/engagement/{eng_id}/certifiable")
def check_certifiable(eng_id: str, product: str, scan_type: str = "web",
                      current_user: dict = Depends(require_user)) -> dict:
    _check_product_access(product, current_user)
    can, reason = _vm.check_certifiable(product, eng_id, scan_type)
    return {"can_certify": can, "reason": reason}


@router.post("/vapt/engagement/{eng_id}/certificate")
def issue_certificate(eng_id: str, product: str, scan_type: str = "web",
                      current_user: dict = Depends(_require_admin)) -> dict:
    eng = _vm.issue_certificate(product, eng_id, current_user.get("name", "unknown"), scan_type)
    if not eng:
        can, reason = _vm.check_certifiable(product, eng_id, scan_type)
        raise HTTPException(400, detail=reason)
    return eng


@router.get("/vapt/engagement/{eng_id}/certificate")
def download_certificate(eng_id: str, product: str, format: str = "pdf",
                          scan_type: str = "web",
                          current_user: dict = Depends(require_user)) -> Response:
    _check_product_access(product, current_user)
    eng = _vm.get(product, eng_id)
    if not eng:
        raise HTTPException(404, detail="Engagement not found")
    certs = eng.get("certificates", {})
    has_cert = scan_type in certs or (scan_type == "web" and eng.get("certificate_id"))
    if not has_cert:
        raise HTTPException(400, detail=f"No {scan_type} certificate has been issued for this engagement")

    html = _render_certificate_html(eng, scan_type)
    if format == "pdf":
        pdf = _to_pdf(html)
        if pdf is None:
            raise HTTPException(500, detail="WeasyPrint not installed. Run: pip install weasyprint")
        cert_info = certs.get(scan_type) or {}
        cert_id = cert_info.get("cert_id") or eng.get("certificate_id", "cert")
        filename = f"vapt_certificate_{cert_id}.pdf"
        return Response(pdf, media_type="application/pdf",
                        headers={"Content-Disposition": f'attachment; filename="{filename}"'})
    return Response(html, media_type="text/html")


# ── scan execution ────────────────────────────────────────────────────────────

def _execute_vapt_scan(product: str, eng_id: str, scan_id: str,
                       is_revalidation: bool, scan_type: str = "web") -> None:
    _vm.patch_scan(product, eng_id, scan_id, status="running")

    tmp_report = _ROOT / "data" / "vapt_findings" / product / f"{scan_id}_pytest.json"
    tmp_report.parent.mkdir(parents=True, exist_ok=True)

    subdir = _VAPT_SUBDIRS.get(scan_type, "vapt")
    test_path = _ROOT / "products" / product / "tests" / subdir
    if not test_path.exists():
        _vm.patch_scan(product, eng_id, scan_id,
                       status="failed",
                       finished_at=datetime.now(timezone.utc).isoformat(),
                       summary_error=f"No {scan_type} test suite for '{product}' — generate tests first")
        return

    # Pre-flight: infra_int requires SSH credentials in scope
    if scan_type == "infra_int":
        _pre_eng = _vm.get(product, eng_id)
        _scope = (_pre_eng or {}).get("scope", {})
        if not _scope.get("ssh_username", "").strip() or not _scope.get("ssh_key_path", "").strip():
            _vm.patch_scan(product, eng_id, scan_id,
                           status="failed",
                           finished_at=datetime.now(timezone.utc).isoformat(),
                           summary_error=(
                               "SSH credentials not configured — set SSH Username and SSH Key Path "
                               "in the Scope tab before running an Internal Infrastructure scan"
                           ))
            return

    cmd = [
        sys.executable, "-m", "pytest",
        str(test_path),
        "-m", "security",
        "--json-report",
        f"--json-report-file={tmp_report}",
        "-v", "--tb=short", "--no-header",
        "--override-ini=addopts=",
    ]
    # Screenshot capture only makes sense for browser-based web scans
    if scan_type == "web":
        cmd.append("--screenshot=only-on-failure")

    run_env = {**os.environ}
    if scan_type in ("infra", "infra_int", "mobile"):
        eng = _vm.get(product, eng_id)
        scope = (eng or {}).get("scope", {})
        if scan_type in ("infra", "infra_int"):
            targets = scope.get("infra_targets", [])
            if targets:
                run_env["VAPT_INFRA_TARGETS"] = ",".join(str(t) for t in targets)
        if scan_type == "infra_int":
            ssh_user = scope.get("ssh_username", "")
            ssh_key = scope.get("ssh_key_path", "")
            if ssh_user:
                run_env["VAPT_SSH_USER"] = ssh_user
            if ssh_key:
                run_env["VAPT_SSH_KEY_PATH"] = ssh_key
        elif scan_type == "mobile":
            app_path = scope.get("mobile_app_path", "")
            if app_path:
                run_env["VAPT_MOBILE_APP_PATH"] = app_path

    _collected_re = re.compile(r"collected (\d+) item")
    _result_re = re.compile(r"\s(PASSED|FAILED|ERROR|SKIPPED)\s")

    try:
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, cwd=str(_ROOT), env=run_env,
        )
        progress_total = 0
        progress_done = 0
        last_patch = 0.0
        for line in proc.stdout:
            m = _collected_re.search(line)
            if m:
                progress_total = int(m.group(1))
            elif _result_re.search(line):
                progress_done += 1
                now = time.monotonic()
                if now - last_patch >= 2.0:
                    _vm.patch_scan(product, eng_id, scan_id,
                                   progress_total=progress_total, progress_done=progress_done)
                    last_patch = now

        try:
            proc.wait(timeout=300)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
            _vm.patch_scan(product, eng_id, scan_id,
                           status="failed",
                           finished_at=datetime.now(timezone.utc).isoformat(),
                           summary_error="Scan timed out after 300s")
            return

        duration = 0.0
        try:
            rdata = json.loads(tmp_report.read_text(encoding="utf-8"))
            duration = round(rdata.get("duration", 0.0), 2)
        except Exception:
            pass

        findings = _parse_scan_findings(tmp_report, product)
        # Slim test log stored on the scan — only fields needed for the report
        test_log = [
            {"test_id": f["test_id"], "title": f["title"],
             "owasp_ref": f["owasp_ref"], "owasp_category": f["owasp_category"],
             "severity": f["severity"], "status": f["status"]}
            for f in findings
        ]
        stats = {
            "total": len(findings),
            "passed": sum(1 for f in findings if f["status"] == "confirmed_secure"),
            "failed": sum(1 for f in findings if f["status"] == "finding"),
            "skipped": sum(1 for f in findings if f["status"] == "skipped"),
            "duration": duration,
            "status": "completed",
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "test_log": test_log,
        }
        _vm.patch_scan(product, eng_id, scan_id, **stats)
        _vm.upsert_findings(product, eng_id, scan_id, findings, is_revalidation)

        try:
            tmp_report.unlink()
        except Exception:
            pass

    except Exception as exc:
        _vm.patch_scan(product, eng_id, scan_id,
                       status="failed",
                       finished_at=datetime.now(timezone.utc).isoformat(),
                       summary_error=str(exc))


def _parse_scan_findings(report_path: Path, product: str) -> list[dict]:
    if not report_path.exists():
        return []
    try:
        data = json.loads(report_path.read_text(encoding="utf-8"))
    except Exception:
        return []

    findings = []
    for t in data.get("tests", []):
        nodeid = t.get("nodeid", "")
        outcome = t.get("outcome", "skipped")
        owasp_ref, owasp_category = _infer_owasp(nodeid)

        if outcome == "passed":
            status = "confirmed_secure"
            evidence = ""
        elif outcome in ("failed", "error"):
            status = "finding"
            evidence = str(
                t.get("call", {}).get("longrepr", "")
                or t.get("longrepr", "")
                or ""
            )[:800]
        else:
            status = "skipped"
            evidence = ""

        screenshot_path = _find_screenshot(nodeid, product) if status == "finding" else None

        findings.append({
            "test_id": nodeid,
            "title": _make_title(nodeid),
            "owasp_ref": owasp_ref,
            "owasp_category": owasp_category,
            "severity": _SEVERITY_BY_OWASP.get(owasp_ref, "Medium"),
            "status": status,
            "evidence": evidence,
            "screenshot_path": screenshot_path,
        })
    return findings


def _find_screenshot(nodeid: str, product: str) -> str | None:
    slug = re.sub(r"[^a-z0-9]+", "-", nodeid.lower()).strip("-")
    product_dir = _ROOT / "products" / product / "test-results"
    if not product_dir.exists():
        return None
    prefix = slug[:40]
    for d in product_dir.iterdir():
        if d.is_dir() and prefix[:20] in d.name.lower():
            candidate = d / "test-finished-1.png"
            if candidate.exists():
                return str(candidate.relative_to(_ROOT))
    return None


# ── PDF rendering ─────────────────────────────────────────────────────────────

def _to_pdf(html: str) -> bytes | None:
    try:
        from weasyprint import HTML
        return HTML(string=html, base_url=str(_ROOT)).write_pdf()
    except ImportError:
        return None


def _render_template(tpl_name: str, **ctx: Any) -> str:
    tpl_path = Path(__file__).resolve().parent.parent / "templates" / tpl_name
    if not tpl_path.exists():
        return f"<html><body>Template {tpl_name} not found</body></html>"
    from jinja2 import Environment, FileSystemLoader
    env = Environment(
        loader=FileSystemLoader(str(tpl_path.parent)),
        autoescape=True,
    )
    return env.get_template(tpl_name).render(**ctx)


_OWASP_EMBEDDED = re.compile(r"(?:^|_)(A0[1-9]|A10)(?:_|$)", re.IGNORECASE)
_OWASP_CAT_MAP = {r: cat for _, r, cat in _OWASP_RULES}  # built once at import

def _infer_test_log_from_files(product: str, scan_id: str, findings: list[dict],
                               scan_type: str = "web") -> list[dict]:
    """Reconstruct a test log from vapt test files for scans that predate test_log persistence."""
    subdir = _VAPT_SUBDIRS.get(scan_type, "vapt")
    vapt_dir = _ROOT / "products" / product / "tests" / subdir
    if not vapt_dir.exists():
        return []
    finding_ids = {f["test_id"] for f in findings if f.get("scan_id") == scan_id}
    rows = []
    for tf in sorted(vapt_dir.glob("test_*.py")):
        rel = str(tf.relative_to(_ROOT))
        for line in tf.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line.startswith("def test_"):
                continue
            fn = line[4:].split("(")[0]
            nodeid = f"{rel}::{fn}"
            # prefer OWASP ref embedded in function name (e.g. test_A01_...)
            m = _OWASP_EMBEDDED.search(fn)
            if m:
                owasp_ref = m.group(1).upper()
                owasp_category = _OWASP_CAT_MAP.get(owasp_ref, "Unknown")
            else:
                owasp_ref, owasp_category = _infer_owasp(nodeid)
            status = "finding" if nodeid in finding_ids else "confirmed_secure"
            rows.append({
                "test_id": nodeid,
                "title": _make_title(nodeid),
                "owasp_ref": owasp_ref,
                "owasp_category": owasp_category,
                "severity": _SEVERITY_BY_OWASP.get(owasp_ref, "Medium"),
                "status": status,
            })
    return rows


def _render_plan_html(eng: dict) -> str:
    return _render_template("vapt_plan_pdf.html", eng=eng,
                             owasp_desc=_OWASP_DESCRIPTIONS,
                             now=datetime.now(timezone.utc))


def _render_report_html(eng: dict, scan_type: str = "web") -> str:
    from collections import defaultdict
    scan_type_label = _SCAN_TYPE_LABELS.get(scan_type, scan_type.title())
    findings = _findings_for_type(eng, scan_type)
    scans = [s for s in eng.get("scans", []) if s.get("scan_type", "web") == scan_type]
    by_sev: dict[str, int] = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
    by_owasp: dict[str, list] = defaultdict(list)
    for f in findings:
        if f["status"] in ("open", "still_open"):
            by_sev[f["severity"]] = by_sev.get(f["severity"], 0) + 1
        cat = f"{f['owasp_ref']} — {f['owasp_category']}"
        by_owasp[cat].append(f)
    scan_test_logs = []
    for s in scans:
        if s.get("status") != "completed":
            continue
        tests = s.get("test_log") or _infer_test_log_from_files(
            eng["product"], s["scan_id"], findings, scan_type
        )
        scan_test_logs.append({"scan": s, "tests": tests})
    eng_view = dict(eng)
    eng_view["findings"] = findings
    eng_view["scans"] = scans
    return _render_template("vapt_report_pdf.html", eng=eng_view,
                             by_sev=by_sev, by_owasp=dict(by_owasp),
                             scan_test_logs=scan_test_logs,
                             scan_type_label=scan_type_label,
                             now=datetime.now(timezone.utc))


def _render_certificate_html(eng: dict, scan_type: str = "web") -> str:
    scan_type_label = _SCAN_TYPE_LABELS.get(scan_type, scan_type.title())
    methodology_label = _METHODOLOGY_LABELS.get(scan_type, "OWASP")
    certs = eng.get("certificates", {})
    cert_info = certs.get(scan_type)
    if cert_info is None and scan_type == "web" and eng.get("certificate_id"):
        cert_info = {
            "cert_id": eng["certificate_id"],
            "issued_at": eng.get("certificate_issued_at"),
            "issued_by": eng.get("certificate_issued_by"),
        }
    findings = _findings_for_type(eng, scan_type)
    total = len(findings)
    fixed = sum(1 for f in findings if f["status"] == "fixed")
    open_c = sum(1 for f in findings if f["status"] in ("open", "still_open"))
    return _render_template("vapt_certificate_pdf.html", eng=eng,
                             cert_info=cert_info,
                             total_findings=total, fixed=fixed, open_count=open_c,
                             scan_type_label=scan_type_label,
                             methodology_label=methodology_label,
                             now=datetime.now(timezone.utc))
