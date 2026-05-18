"""Visual regression testing module — Playwright screenshot capture + Pillow pixel diff."""
from __future__ import annotations

import asyncio
import io
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from core.visual_manager import VisualManager
from dashboard.routers.auth import require_user, user_products
from dashboard.routers.config._helpers import _load_config, _require_admin

router = APIRouter(tags=["visual"])

_ROOT = Path(__file__).resolve().parent.parent.parent
_vm = VisualManager()


def _visual_products(current_user: dict) -> list[str]:
    cfg = _load_config()
    all_prods = [p["name"] for p in cfg.get("products", []) if p.get("visual_enabled")]
    return user_products(current_user, all_prods)


def _check_product_access(product: str, current_user: dict) -> None:
    if product not in _visual_products(current_user):
        raise HTTPException(403, detail="Access denied or visual regression not enabled for this product")


# ── Pydantic models ───────────────────────────────────────────────────────────

class CreateEngBody(BaseModel):
    product: str
    name: str
    base_url: str
    pages: list[str] = ["/"]
    threshold_pct: float = 1.0


class PatchEngBody(BaseModel):
    name: str | None = None
    base_url: str | None = None
    pages: list[str] | None = None
    threshold_pct: float | None = None


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
    tpl = env.get_template("visual_report_pdf.html")
    return tpl.render(eng=eng,
                      generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))


# ── engagement CRUD ───────────────────────────────────────────────────────────

@router.post("/visual/engagements")
def create_engagement(body: CreateEngBody,
                      current_user: dict = Depends(require_user)) -> dict:
    _check_product_access(body.product, current_user)
    return _vm.create(body.product, body.name, body.base_url, body.pages,
                      current_user.get("name", "unknown"), body.threshold_pct)


@router.get("/visual/engagements")
def list_engagements(product: str,
                     current_user: dict = Depends(require_user)) -> list[dict]:
    _check_product_access(product, current_user)
    return _vm.list_engagements(product)


@router.get("/visual/engagement/{eng_id}")
def get_engagement(eng_id: str, product: str,
                   current_user: dict = Depends(require_user)) -> dict:
    _check_product_access(product, current_user)
    eng = _vm.get(product, eng_id)
    if not eng:
        raise HTTPException(404, detail="Engagement not found")
    return eng


@router.patch("/visual/engagement/{eng_id}")
def patch_engagement(eng_id: str, product: str, body: PatchEngBody,
                     current_user: dict = Depends(require_user)) -> dict:
    _check_product_access(product, current_user)
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    eng = _vm.patch(product, eng_id, **updates)
    if not eng:
        raise HTTPException(404, detail="Engagement not found")
    return eng


@router.delete("/visual/engagement/{eng_id}")
def delete_engagement(eng_id: str, product: str,
                      _: dict = Depends(_require_admin)) -> dict:
    if not _vm.delete(product, eng_id):
        raise HTTPException(404, detail="Engagement not found")
    return {"deleted": True}


# ── scan management ───────────────────────────────────────────────────────────

@router.post("/visual/engagement/{eng_id}/capture-baseline")
def capture_baseline(eng_id: str, product: str,
                     background_tasks: BackgroundTasks,
                     current_user: dict = Depends(require_user)) -> dict:
    _check_product_access(product, current_user)
    eng = _vm.get(product, eng_id)
    if not eng:
        raise HTTPException(404, detail="Engagement not found")
    scan = _vm.add_scan(product, eng_id, current_user.get("name", "unknown"), capture_baseline=True)
    if not scan:
        raise HTTPException(500, detail="Failed to create scan record")
    background_tasks.add_task(_execute_visual_scan, product, eng_id, scan["scan_id"],
                               eng["base_url"], eng.get("pages", ["/"]),
                               eng.get("threshold_pct", 1.0), capture_baseline=True)
    return scan


@router.post("/visual/engagement/{eng_id}/scan")
def trigger_scan(eng_id: str, product: str,
                 background_tasks: BackgroundTasks,
                 current_user: dict = Depends(require_user)) -> dict:
    _check_product_access(product, current_user)
    eng = _vm.get(product, eng_id)
    if not eng:
        raise HTTPException(404, detail="Engagement not found")
    if not eng.get("baselines"):
        raise HTTPException(400, detail="Capture a baseline first before running a comparison scan")
    scan = _vm.add_scan(product, eng_id, current_user.get("name", "unknown"), capture_baseline=False)
    if not scan:
        raise HTTPException(500, detail="Failed to create scan record")
    background_tasks.add_task(_execute_visual_scan, product, eng_id, scan["scan_id"],
                               eng["base_url"], eng.get("pages", ["/"]),
                               eng.get("threshold_pct", 1.0), capture_baseline=False)
    return scan


@router.delete("/visual/engagement/{eng_id}/scan/{scan_id}")
def delete_scan(eng_id: str, scan_id: str, product: str,
                current_user: dict = Depends(require_user)) -> dict:
    _check_product_access(product, current_user)
    eng = _vm.get(product, eng_id)
    if not eng:
        raise HTTPException(404, detail="Engagement not found")
    target = next((s for s in eng.get("scans", []) if s["scan_id"] == scan_id), None)
    if target and target.get("status") in ("queued", "running"):
        raise HTTPException(400, detail="Cannot delete a scan that is currently running")
    if not _vm.delete_scan(product, eng_id, scan_id):
        raise HTTPException(404, detail="Scan not found")
    return _vm.get(product, eng_id)


# ── report ────────────────────────────────────────────────────────────────────

@router.get("/visual/engagement/{eng_id}/report")
def download_report(eng_id: str, product: str, format: str = "pdf",
                    current_user: dict = Depends(require_user)) -> Response:
    _check_product_access(product, current_user)
    eng = _vm.get(product, eng_id)
    if not eng:
        raise HTTPException(404, detail="Engagement not found")
    html = _render_report_html(eng)
    if format == "pdf":
        pdf = _to_pdf(html)
        if pdf is None:
            raise HTTPException(500, detail="WeasyPrint not installed")
        return Response(pdf, media_type="application/pdf",
                        headers={"Content-Disposition": f'attachment; filename="visual_report_{product}_{eng_id}.pdf"'})
    return Response(html, media_type="text/html")


# ── execution ─────────────────────────────────────────────────────────────────

def _execute_visual_scan(product: str, eng_id: str, scan_id: str,
                          base_url: str, pages: list[str], threshold_pct: float,
                          capture_baseline: bool) -> None:
    _vm.patch_scan(product, eng_id, scan_id, status="running")
    try:
        pages_results = asyncio.run(_scan_pages(
            product, eng_id, base_url, pages, threshold_pct, capture_baseline
        ))
        passed = sum(1 for r in pages_results if r.get("passed", True))
        failed = sum(1 for r in pages_results if not r.get("passed", True) and r.get("baseline_exists"))
        no_baseline = sum(1 for r in pages_results if not r.get("baseline_exists"))
        _vm.patch_scan(product, eng_id, scan_id,
                       status="completed",
                       finished_at=datetime.now(timezone.utc).isoformat(),
                       total_pages=len(pages),
                       passed=passed,
                       failed=failed,
                       no_baseline=no_baseline,
                       pages_results=pages_results)
    except Exception as exc:
        _vm.patch_scan(product, eng_id, scan_id,
                       status="failed",
                       finished_at=datetime.now(timezone.utc).isoformat(),
                       error=str(exc))


async def _scan_pages(product: str, eng_id: str, base_url: str, pages: list[str],
                      threshold_pct: float, capture_baseline: bool) -> list[dict]:
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        raise RuntimeError("playwright not installed — run: pip install playwright && playwright install chromium")

    results = []
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(args=["--no-sandbox"])
        page = await browser.new_page(viewport={"width": 1280, "height": 800})

        for path in pages:
            url = base_url.rstrip("/") + path
            try:
                await page.goto(url, wait_until="networkidle", timeout=30000)
                screenshot_bytes = await page.screenshot(full_page=True)
            except Exception as exc:
                results.append({
                    "url": path,
                    "baseline_exists": False,
                    "passed": False,
                    "error": str(exc),
                })
                continue

            eng = _vm.get(product, eng_id)
            if eng is None:
                continue
            baselines = eng.get("baselines", {})

            if capture_baseline:
                ss_path = _vm.screenshot_path(product, eng_id, path)
                ss_path.write_bytes(screenshot_bytes)
                _vm.update_baseline(product, eng_id, path, str(ss_path))
                results.append({
                    "url": path,
                    "baseline_exists": True,
                    "baseline_captured": True,
                    "screenshot_path": str(ss_path),
                    "passed": True,
                })
            else:
                baseline_info = baselines.get(path)
                if not baseline_info or not Path(baseline_info["screenshot_path"]).exists():
                    results.append({
                        "url": path,
                        "baseline_exists": False,
                        "passed": True,
                    })
                    continue

                baseline_bytes = Path(baseline_info["screenshot_path"]).read_bytes()
                diff_pct, passed = _compare_images(baseline_bytes, screenshot_bytes, threshold_pct)

                ss_path = _vm.screenshot_path(product, eng_id, path)
                ss_path.write_bytes(screenshot_bytes)

                results.append({
                    "url": path,
                    "baseline_exists": True,
                    "diff_pct": diff_pct,
                    "threshold_pct": threshold_pct,
                    "passed": passed,
                    "screenshot_path": str(ss_path),
                })

        await browser.close()
    return results


def _compare_images(img1_bytes: bytes, img2_bytes: bytes, threshold_pct: float) -> tuple[float, bool]:
    try:
        from PIL import Image, ImageChops
    except ImportError:
        raise RuntimeError("Pillow not installed — run: pip install Pillow")

    img1 = Image.open(io.BytesIO(img1_bytes)).convert("RGB")
    img2 = Image.open(io.BytesIO(img2_bytes)).convert("RGB")
    if img1.size != img2.size:
        img2 = img2.resize(img1.size, Image.LANCZOS)
    diff = ImageChops.difference(img1, img2)
    total_pixels = img1.width * img1.height
    diff_pixels = sum(1 for v in diff.getdata() if max(v) > 10)
    diff_pct = round(diff_pixels / total_pixels * 100, 3)
    return diff_pct, diff_pct <= threshold_pct
