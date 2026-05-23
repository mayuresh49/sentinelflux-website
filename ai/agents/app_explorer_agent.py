"""AppExplorerAgent — crawls a running app to discover real UI elements and flows."""
from __future__ import annotations

import json
import logging
import re
from pathlib import Path

import yaml

from ai.agents.base_agent import BaseAgent
from utils.paths import ROOT as _ROOT_DIR

_log = logging.getLogger(__name__)


def _url_to_slug(url: str) -> str:
    path = re.sub(r"https?://[^/]+", "", url).strip("/")
    slug = re.sub(r"[^\w/]", "_", path).replace("/", "_")
    return re.sub(r"_+", "_", slug).strip("_") or "page"


def _slug_to_class(slug: str) -> str:
    return "".join(p.capitalize() for p in slug.split("_")) + "Page"


class AppExplorerAgent(BaseAgent):
    """
    Uses Playwright to explore a running web application and produce grounded context
    for test generation — real DOM selectors, verified field names, actual UI flows.

    Outputs per explored page:
      1. Exploration context string (injected into doc/script gen prompts)
      2. data/explorations/<product>/<slug>.json   — structured discovery result
      3. locators/web/<slug>.json                  — primary + alternative selectors
      4. pages/web/<slug>.py                       — page object skeleton (not overwritten)

    Extra params (via ctx.extend()):
      base_url            — app root URL, e.g. "http://localhost"
      login_url           — login page path, e.g. "/web/index.php/auth/login"
      credentials         — {"username": "...", "password": "..."}
      pages               — list of URL paths to explore, e.g. ["/pim/addEmployee"]
      update_locators     — write locator JSON files (default True)
      generate_page_objects — write page object .py skeleton (default True)
      headless            — run Playwright headless (default True)
    """
    name = "app_explorer"

    def run(
        self,
        *,
        base_url: str = "",
        pages: list[str] | None = None,
        login_url: str = "",
        credentials: dict | None = None,
        update_locators: bool = True,
        generate_page_objects: bool = True,
        headless: bool = True,
        feature_name: str = "",
        write_kb_doc: bool = False,
        write_increment: bool = False,
    ) -> dict:
        from ai.skills.app_exploration import AppExplorationSkill
        from core.activity_log import ActivityLog

        if not base_url:
            base_url = self.ctx.get("base_url", "")
        if not pages:
            pages = self.ctx.get("pages") or []
        if not login_url:
            login_url = self.ctx.get("login_url", "")
        if not credentials:
            credentials = self.ctx.get("credentials") or {}

        if not base_url:
            raise ValueError("AppExplorerAgent: base_url is required (pass via run() or ctx.extend(base_url=...))")
        if not pages:
            raise ValueError("AppExplorerAgent: pages list is required")

        output_base = self.ctx.output_base or _ROOT_DIR
        product = self.ctx.product or ""
        skill = AppExplorationSkill(headless=headless)

        full_pages = [
            p if p.startswith("http") else f"{base_url.rstrip('/')}{p}"
            for p in pages
        ]

        try:
            if login_url and credentials:
                full_login = (
                    login_url if login_url.startswith("http")
                    else f"{base_url.rstrip('/')}{login_url}"
                )
                discovered = skill.explore_with_auth(
                    pages=full_pages,
                    base_url=base_url,
                    login_url=full_login,
                    credentials=credentials,
                )
            else:
                discovered = [skill.explore_page(url) for url in full_pages]
        except Exception as exc:
            self._log.error("AppExplorer failed: %s", exc)
            return {"success": False, "error": str(exc), "pages_explored": 0}

        exploration_contexts: list[str] = []
        results: list[dict] = []

        for dp in discovered:
            exploration_contexts.append(dp.to_exploration_context())
            slug = _url_to_slug(dp.url)

            # Save structured discovery to data/explorations/<product>/
            expl_dir = _ROOT_DIR / "data" / "explorations" / (product or "default")
            expl_dir.mkdir(parents=True, exist_ok=True)
            expl_file = expl_dir / f"{slug}.json"
            expl_file.write_text(json.dumps(dp.to_dict(), indent=2), encoding="utf-8")

            if update_locators:
                loc_dir = output_base / "locators" / "web"
                loc_dir.mkdir(parents=True, exist_ok=True)
                loc_file = loc_dir / f"{slug}.json"
                loc_file.write_text(json.dumps(dp.to_locator_json(), indent=2), encoding="utf-8")
                self._log.info("Locators → %s (%d entries)", loc_file.name, len(dp.to_locator_json()))

            if generate_page_objects:
                cls = _slug_to_class(slug)
                po_dir = output_base / "pages" / "web"
                po_dir.mkdir(parents=True, exist_ok=True)
                po_file = po_dir / f"{slug}.py"
                if not po_file.exists():
                    po_file.write_text(dp.to_page_object_code(cls, product), encoding="utf-8")
                    self._log.info("Page object → %s", po_file.name)
                else:
                    self._log.info("Page object exists, not overwriting: %s", po_file.name)

            results.append({
                "url": dp.url,
                "title": dp.title,
                "fields_found": len(dp.fields),
                "buttons_found": len(dp.buttons),
                "exploration_file": str(expl_file.relative_to(_ROOT_DIR)),
            })

        combined_context = "\n\n---\n\n".join(exploration_contexts)
        total_fields = sum(r["fields_found"] for r in results)

        kb_doc_path: str | None = None
        increment_path: str | None = None
        increment_filename: str | None = None

        if write_kb_doc and product:
            kb_dir = _ROOT_DIR / "products" / product / "ai" / "knowledge_base"
            kb_dir.mkdir(parents=True, exist_ok=True)
            ui_pages_file = kb_dir / "ui_pages.yaml"
            existing: dict = {}
            if ui_pages_file.exists():
                existing = yaml.safe_load(ui_pages_file.read_text(encoding="utf-8")) or {}
            pages_list: list = existing.get("pages", [])
            existing_urls = {p["url"] for p in pages_list if isinstance(p, dict)}
            for dp in discovered:
                entry = dp.to_kb_yaml_entry()
                if dp.url in existing_urls:
                    pages_list = [p for p in pages_list if p.get("url") != dp.url]
                pages_list.append(entry)
            existing["pages"] = pages_list
            ui_pages_file.write_text(yaml.safe_dump(existing, allow_unicode=True, sort_keys=False), encoding="utf-8")
            kb_doc_path = str(ui_pages_file.relative_to(_ROOT_DIR))
            self._log.info("KB doc updated → %s (%d pages total)", kb_doc_path, len(pages_list))

        if write_increment and product and feature_name:
            inc_dir = _ROOT_DIR / "ai" / "knowledge_base" / "increments"
            inc_dir.mkdir(parents=True, exist_ok=True)
            all_scenarios: list[dict] = []
            ui_changes: list[dict] = []
            for dp in discovered:
                all_scenarios.append({
                    "name": f"page_loads_{_url_to_slug(dp.url)}",
                    "type": "happy_path",
                    "description": f"Verify {dp.title} loads without errors",
                })
                for f in dp.fields:
                    if f.required:
                        all_scenarios.append({
                            "name": f"fill_{f.name}",
                            "type": "happy_path",
                            "description": f"Fill {f.label or f.name} with valid data",
                        })
                if any(f.validation_message for f in dp.fields):
                    all_scenarios.append({
                        "name": f"validation_{_url_to_slug(dp.url)}",
                        "type": "error",
                        "description": f"Submit {dp.title} empty — required-field errors appear",
                    })
                ui_changes.append({
                    "component": dp.title,
                    "url": dp.url,
                    "fields": [f"{f.label or f.name} ({f.primary_selector})" for f in dp.fields],
                    "buttons": [b.label for b in dp.buttons],
                })
            slug = re.sub(r"[^\w]", "_", feature_name.lower()).strip("_")
            slug = re.sub(r"_+", "_", slug)
            inc_filename = f"explore_{slug}_{product}.yaml"
            inc_data = {
                "product": product,
                "feature": feature_name,
                "domain": "web",
                "description": (
                    f"UI exploration of {len(discovered)} page(s): "
                    + ", ".join(dp.title for dp in discovered[:3])
                    + (" ..." if len(discovered) > 3 else "")
                    + "\n"
                ),
                "ui_changes": ui_changes,
                "scenarios": all_scenarios,
            }
            inc_file = inc_dir / inc_filename
            inc_file.write_text(yaml.safe_dump(inc_data, allow_unicode=True, sort_keys=False), encoding="utf-8")
            increment_path = str(inc_file.relative_to(_ROOT_DIR))
            increment_filename = inc_filename
            self._log.info("Increment saved → %s", increment_path)

        self._log.info(
            "AppExplorer complete — %d page(s), %d fields total",
            len(discovered), total_fields,
        )

        ActivityLog().append(
            event_type="app_exploration",
            agent=self.name,
            product=product,
            domain=self.ctx.domain,
            status="success",
            summary=(
                f"Explored {len(discovered)} page(s): "
                f"{', '.join(dp.title for dp in discovered[:3])}"
                f"{' ...' if len(discovered) > 3 else ''}"
                f" — {total_fields} fields discovered"
                + (f"; KB doc updated" if kb_doc_path else "")
                + (f"; increment saved: {increment_filename}" if increment_filename else "")
            ),
        )

        return {
            "success": True,
            "pages_explored": len(discovered),
            "results": results,
            "exploration_context": combined_context,
            "kb_doc_path": kb_doc_path,
            "increment_path": increment_path,
            "increment_filename": increment_filename,
        }
