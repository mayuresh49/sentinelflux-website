"""AppExplorerAgent — crawls a running app to discover real UI elements and flows."""
from __future__ import annotations

import json
import logging
import re
from pathlib import Path

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
            ),
        )

        return {
            "success": True,
            "pages_explored": len(discovered),
            "results": results,
            "exploration_context": combined_context,
        }
