"""LocatorHealerAgent — proposes updated selectors for persistently failing UI elements."""
from __future__ import annotations

import json
import re
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

STRICT RULES — violating these produces broken test suites:
1. ONLY suggest selectors for elements you can see in the Page context above.
   If the element is not visible in the provided context, respond with:
   {{"error": "element_not_found_in_context"}}
2. Do NOT invent attributes, IDs, or class names that are not present in the page context.
3. Prefer stable attributes in this order: id > name > data-testid > aria-label > role > class
4. Avoid positional selectors (nth-child, nth-of-type) unless no stable attribute exists.
5. For web: use CSS or XPath strings compatible with Playwright.
6. Respond in JSON only — no prose, no markdown fences:
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

STRICT RULES — violating these produces broken test suites:
1. ONLY suggest locators for elements you can see in the Page context above.
   If the element is not visible in the provided context, respond with:
   {{"error": "element_not_found_in_context"}}
2. Do NOT invent accessibility IDs, content-desc values, or XPath paths not present in context.
3. Prefer accessibility id > xpath > class name.
4. accessibility id maps to content-desc (Android) or accessibilityIdentifier (iOS).
5. XPath expressions must be valid for Appium (no CSS).
6. Respond in JSON only — no prose, no markdown fences:
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
        locator_file: Path | None,
        element_name: str,
        failed_selector: str,
        page_context: str = "",
    ) -> dict:
        if self.ctx.domain == "api":
            return {"skipped": True, "reason": "api domain has no locators"}
        if locator_file is None:
            self._log.warning("LocatorHealerAgent: no locator_file for '%s' — skipping", element_name)
            return {"success": False, "element": element_name, "error": "no_locator_file"}

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

        err = proposal.get("error")
        if err:
            self._log.warning("Locator healing refused for '%s': %s", element_name, err)
            return {"success": False, "element": element_name, "error": err}

        validation_error = self._validate_proposal(proposal)
        if validation_error:
            self._log.warning("Invalid proposal for '%s': %s", element_name, validation_error)
            return {"success": False, "element": element_name, "error": validation_error}

        if not self.ctx.get("dry_run", False):
            locator_file.parent.mkdir(parents=True, exist_ok=True)
            # Backup before overwrite so healing can be rolled back
            if locator_file.exists():
                locator_file.with_suffix(".json.bak").write_text(
                    locator_file.read_text(encoding="utf-8"), encoding="utf-8"
                )
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
    def _validate_proposal(proposal: dict) -> str | None:
        """Return an error string if the proposal is malformed, else None."""
        primary = proposal.get("primary", "")
        if not isinstance(primary, str) or not primary.strip():
            return "proposal missing non-empty 'primary' selector"
        alts = proposal.get("alternatives")
        if alts is not None and not isinstance(alts, list):
            return "'alternatives' must be a list"
        return None

    @staticmethod
    def _parse_json(raw: str) -> dict:
        raw = raw.strip()
        # Strip markdown fences robustly via regex
        fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
        if fence_match:
            raw = fence_match.group(1).strip()
        return json.loads(raw)
