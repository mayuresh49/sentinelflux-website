"""LocatorHealerAgent — proposes updated selectors for persistently failing UI elements."""
from __future__ import annotations

import json
from pathlib import Path

from ai.agents.base_agent import BaseAgent

_HEAL_PROMPT = """\
You are a UI test locator expert. The selector below failed to find an element on the page.
Suggest a better primary selector and up to 3 alternatives.

Domain: {domain}
Element name: {element_name}
Failed selector: {failed_selector}

Page context (HTML excerpt or accessibility snapshot):
{page_context}

Current locator entry:
{current_entry}

Rules:
- Prefer stable attributes: id, name, data-testid, aria-label, role
- Avoid positional selectors like nth-child unless unavoidable
- For web: use CSS or XPath strings compatible with Playwright
- For mobile: use Appium-compatible locators (accessibility id, xpath)
- Do NOT invent elements that may not exist — base suggestions on the page context

Respond in JSON only — no prose, no markdown fences:
{{
  "primary": "<updated selector>",
  "alternatives": ["<alt1>", "<alt2>", "<alt3>"]
}}
"""

_MOBILE_HEAL_PROMPT = """\
You are a mobile UI test locator expert. The locator below failed on an Appium session.
Suggest a better primary locator and up to 3 alternatives.

Element name: {element_name}
Failed locator: {failed_selector}

Page context (accessibility tree or page source excerpt):
{page_context}

Current locator entry:
{current_entry}

Rules:
- Prefer accessibility id > xpath > class name
- accessibility id maps to content-desc (Android) or accessibilityIdentifier (iOS)
- XPath expressions must be valid for Appium (no CSS)

Respond in JSON only — no prose, no markdown fences:
{{
  "primary": "<updated locator>",
  "alternatives": ["<alt1>", "<alt2>"]
}}
"""


class LocatorHealerAgent(BaseAgent):
    """
    Proposes updated locator entries for elements whose selectors persistently fail.

    Reads the locator JSON, sends the failed selector + page context to AI,
    and writes back an updated entry. Does NOT mutate any test code.

    Domain behaviour:
      web    — Playwright CSS/XPath selectors
      mobile — Appium accessibility id / XPath
      api    — no-op (locators don't apply)

    Extra params (via ctx.extend()):
      dry_run — if True, return the proposal without writing to disk (default False)
    """
    name = "locator_healer"

    def run(
        self,
        *,
        locator_file: Path,
        element_name: str,
        failed_selector: str,
        page_context: str = "",
    ) -> dict:
        if self.ctx.domain == "api":
            self._log.info("Locator healing not applicable for API domain — skipping")
            return {"skipped": True, "reason": "api domain has no locators"}

        current = self._load_locator(locator_file)
        current_entry = json.dumps(current.get(element_name, {}), indent=2)

        prompt_template = _MOBILE_HEAL_PROMPT if self.ctx.domain == "mobile" else _HEAL_PROMPT
        prompt = prompt_template.format(
            domain=self.ctx.domain,
            element_name=element_name,
            failed_selector=failed_selector,
            page_context=page_context[:3000] if page_context else "(not available)",
            current_entry=current_entry,
        )

        try:
            raw = self.client.generate(prompt, max_tokens=512, temperature=0.1)
            proposal = self._parse_json(raw)
        except Exception as exc:
            self._log.warning("Locator healing failed for '%s': %s", element_name, exc)
            return {"success": False, "element": element_name, "error": str(exc)}

        if not self.ctx.get("dry_run", False):
            current[element_name] = proposal
            locator_file.write_text(json.dumps(current, indent=2), encoding="utf-8")
            self._log.info(
                "Healed locator '%s' in %s: %s → %s",
                element_name, locator_file.name,
                failed_selector, proposal["primary"],
            )

        return {
            "success": True,
            "element": element_name,
            "old_selector": failed_selector,
            "new_primary": proposal["primary"],
            "alternatives": proposal.get("alternatives", []),
            "locator_file": str(locator_file),
            "dry_run": self.ctx.get("dry_run", False),
        }

    @staticmethod
    def _load_locator(path: Path) -> dict:
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def _parse_json(raw: str) -> dict:
        raw = raw.strip()
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())
