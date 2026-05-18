"""Accessibility testing module — Playwright + axe-core per-page WCAG 2.1 scanning."""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from core.a11y_manager import A11yManager
from dashboard.routers.auth import require_user, user_products
from dashboard.routers.config._helpers import _load_config, _require_admin

router = APIRouter(tags=["a11y"])

_ROOT = Path(__file__).resolve().parent.parent.parent
_am = A11yManager()

# axe-core CDN — fixed version for reproducibility
_AXE_CDN = "https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.9.1/axe.min.js"
_WCAG_TAGS = {"A": ["wcag2a"], "AA": ["wcag2a", "wcag2aa"], "AAA": ["wcag2a", "wcag2aa", "wcag2aaa"]}


def _a11y_products(current_user: dict) -> list[str]:
    cfg = _load_config()
    all_prods = [p["name"] for p in cfg.get("products", []) if p.get("a11y_enabled")]
    return user_products(current_user, all_prods)


def _check_product_access(product: str, current_user: dict) -> None:
    if product not in _a11y_products(current_user):
        raise HTTPException(403, detail="Access denied or accessibility testing not enabled for this product")


# ── Pydantic models ───────────────────────────────────────────────────────────

class CreateEngBody(BaseModel):
    product: str
    name: str
    base_url: str
    pages: list[str] = ["/"]
    wcag_level: str = "AA"


class PatchEngBody(BaseModel):
    name: str | None = None
    base_url: str | None = None
    pages: list[str] | None = None
    wcag_level: str | None = None


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
    tpl = env.get_template("a11y_report_pdf.html")
    return tpl.render(eng=eng,
                      generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))


# ── engagement CRUD ───────────────────────────────────────────────────────────

@router.post("/a11y/engagements")
def create_engagement(body: CreateEngBody,
                      current_user: dict = Depends(require_user)) -> dict:
    _check_product_access(body.product, current_user)
    return _am.create(body.product, body.name, body.base_url, body.pages,
                      current_user.get("name", "unknown"))


@router.get("/a11y/engagements")
def list_engagements(product: str,
                     current_user: dict = Depends(require_user)) -> list[dict]:
    _check_product_access(product, current_user)
    return _am.list_engagements(product)


@router.get("/a11y/engagement/{eng_id}")
def get_engagement(eng_id: str, product: str,
                   current_user: dict = Depends(require_user)) -> dict:
    _check_product_access(product, current_user)
    eng = _am.get(product, eng_id)
    if not eng:
        raise HTTPException(404, detail="Engagement not found")
    return eng


@router.patch("/a11y/engagement/{eng_id}")
def patch_engagement(eng_id: str, product: str, body: PatchEngBody,
                     current_user: dict = Depends(require_user)) -> dict:
    _check_product_access(product, current_user)
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    eng = _am.patch(product, eng_id, **updates)
    if not eng:
        raise HTTPException(404, detail="Engagement not found")
    return eng


@router.delete("/a11y/engagement/{eng_id}")
def delete_engagement(eng_id: str, product: str,
                      _: dict = Depends(_require_admin)) -> dict:
    if not _am.delete(product, eng_id):
        raise HTTPException(404, detail="Engagement not found")
    return {"deleted": True}


# ── scan ──────────────────────────────────────────────────────────────────────

@router.post("/a11y/engagement/{eng_id}/scan")
def trigger_scan(eng_id: str, product: str,
                 background_tasks: BackgroundTasks,
                 current_user: dict = Depends(require_user)) -> dict:
    _check_product_access(product, current_user)
    eng = _am.get(product, eng_id)
    if not eng:
        raise HTTPException(404, detail="Engagement not found")
    scan = _am.add_scan(product, eng_id, current_user.get("name", "unknown"))
    if not scan:
        raise HTTPException(500, detail="Failed to create scan record")
    background_tasks.add_task(_execute_a11y_scan, product, eng_id, scan["scan_id"],
                               eng["base_url"], eng.get("pages", ["/"]),
                               eng.get("wcag_level", "AA"))
    return scan


@router.delete("/a11y/engagement/{eng_id}/scan/{scan_id}")
def delete_scan(eng_id: str, scan_id: str, product: str,
                current_user: dict = Depends(require_user)) -> dict:
    _check_product_access(product, current_user)
    eng = _am.get(product, eng_id)
    if not eng:
        raise HTTPException(404, detail="Engagement not found")
    target = next((s for s in eng.get("scans", []) if s["scan_id"] == scan_id), None)
    if target and target.get("status") in ("queued", "running"):
        raise HTTPException(400, detail="Cannot delete a scan that is currently running")
    if not _am.delete_scan(product, eng_id, scan_id):
        raise HTTPException(404, detail="Scan not found")
    return _am.get(product, eng_id)


# ── report ────────────────────────────────────────────────────────────────────

@router.get("/a11y/engagement/{eng_id}/report")
def download_report(eng_id: str, product: str, format: str = "pdf",
                    current_user: dict = Depends(require_user)) -> Response:
    _check_product_access(product, current_user)
    eng = _am.get(product, eng_id)
    if not eng:
        raise HTTPException(404, detail="Engagement not found")
    html = _render_report_html(eng)
    if format == "pdf":
        pdf = _to_pdf(html)
        if pdf is None:
            raise HTTPException(500, detail="WeasyPrint not installed")
        return Response(pdf, media_type="application/pdf",
                        headers={"Content-Disposition": f'attachment; filename="a11y_report_{product}_{eng_id}.pdf"'})
    return Response(html, media_type="text/html")


# ── execution ─────────────────────────────────────────────────────────────────

def _execute_a11y_scan(product: str, eng_id: str, scan_id: str,
                       base_url: str, pages: list[str], wcag_level: str) -> None:
    _am.patch_scan(product, eng_id, scan_id, status="running")
    try:
        pages_results = asyncio.run(_scan_pages(base_url, pages, wcag_level))
        total_violations = sum(len(pr["violations"]) for pr in pages_results)
        by_impact: dict[str, int] = {"critical": 0, "serious": 0, "moderate": 0, "minor": 0}
        for pr in pages_results:
            for v in pr["violations"]:
                impact = v.get("impact", "minor") or "minor"
                by_impact[impact] = by_impact.get(impact, 0) + 1
        _am.patch_scan(product, eng_id, scan_id,
                       status="completed",
                       finished_at=datetime.now(timezone.utc).isoformat(),
                       total_violations=total_violations,
                       violations_by_impact=by_impact,
                       pages_results=pages_results)
    except Exception as exc:
        _am.patch_scan(product, eng_id, scan_id,
                       status="failed",
                       finished_at=datetime.now(timezone.utc).isoformat(),
                       error=str(exc))


async def _scan_pages(base_url: str, pages: list[str], wcag_level: str) -> list[dict]:
    tags = _WCAG_TAGS.get(wcag_level, _WCAG_TAGS["AA"])
    results = []
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        raise RuntimeError("playwright not installed — run: pip install playwright && playwright install chromium")

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(args=["--no-sandbox"])
        page = await browser.new_page()
        for path in pages:
            url = base_url.rstrip("/") + path
            violations = []
            try:
                await page.goto(url, wait_until="networkidle", timeout=30000)
                await page.add_script_tag(url=_AXE_CDN)
                tags_js = str(tags).replace("'", '"')
                violations = await page.evaluate(f"""
                    async () => {{
                        const result = await axe.run(document, {{
                            runOnly: {{ type: 'tag', values: {tags_js} }}
                        }});
                        return result.violations.map(v => ({{
                            id: v.id,
                            impact: v.impact,
                            description: v.description,
                            nodes_affected: v.nodes.length,
                            help_url: v.helpUrl
                        }}));
                    }}
                """)
            except Exception as exc:
                violations = [{"id": "scan_error", "impact": "critical",
                                "description": str(exc), "nodes_affected": 0, "help_url": ""}]
            results.append({"url": path, "violations": violations})
        await browser.close()
    return results
