"""CoverageGapAgent — diffs KB scenarios against existing tests to find untested gaps."""
from __future__ import annotations

import json
import re
from pathlib import Path

from ai.agents.base_agent import BaseAgent

_GAP_PROMPT = """\
You are a test coverage analyst.

Domain: {domain}
Product: {product}

Knowledge base scenarios (source of truth for what SHOULD be tested):
{kb_scenarios}

Existing test function names (what IS already tested):
{test_names}

Identify scenarios from the knowledge base that are NOT covered by any existing test.
For each gap, suggest a concise test function name (snake_case, prefixed with "test_").

Respond in JSON only — no prose, no markdown fences:
{{
  "gaps": [
    {{
      "scenario": "<scenario description from KB>",
      "suggested_test_name": "test_...",
      "priority": "<high|medium|low>"
    }}
  ]
}}
"""


class CoverageGapAgent(BaseAgent):
    """
    Diffs KB scenarios against existing test function names per domain.

    Domain determines which test files are scanned (tests/<domain>/**).
    Product determines which KB context is loaded.

    Extra params (via ctx.extend()):
      max_scenarios — cap KB scenarios sent to prompt (default 50)
      scan_dir      — override test directory to scan (Path)
    """
    name = "coverage_gap"

    def run(
        self,
        *,
        tests_dir: Path,
    ) -> dict:
        kb_scenarios = self._extract_kb_scenarios()
        test_names = self._extract_test_names(tests_dir, self.ctx.domain)

        if not kb_scenarios:
            self._log.warning("No KB scenarios found — is kb_loader configured?")
            return {"domain": self.ctx.domain, "gaps": [], "total": 0}

        prompt = _GAP_PROMPT.format(
            domain=self.ctx.domain,
            product=self.ctx.product or "unknown",
            kb_scenarios="\n".join(f"- {s}" for s in kb_scenarios),
            test_names="\n".join(f"- {n}" for n in test_names) or "(none)",
        )

        try:
            raw = self.client.generate(prompt, max_tokens=2000, temperature=0.2)
            gaps = self._parse_gaps(raw)
        except Exception as exc:
            self._log.warning("Gap analysis failed: %s", exc)
            gaps = []

        self._log.info(
            "Coverage gap [%s/%s]: %d untested scenarios",
            self.ctx.product or "?",
            self.ctx.domain,
            len(gaps),
        )
        return {"domain": self.ctx.domain, "gaps": gaps, "total": len(gaps)}

    # ── internal ──────────────────────────────────────────────────────────

    def _extract_kb_scenarios(self) -> list[str]:
        if not self.kb:
            return []
        max_s = self.ctx.get("max_scenarios", 50)
        try:
            context = self.kb.get_all_context()
            lines = [
                line.strip().lstrip("-•* ")
                for line in context.splitlines()
                if line.strip() and line.strip()[0] in "-•*"
                and len(line.strip()) > 10
            ]
            return lines[:max_s]
        except Exception as exc:
            self._log.warning("KB extraction failed: %s", exc)
            return []

    def _extract_test_names(self, tests_dir: Path, domain: str) -> list[str]:
        scan_dir = self.ctx.get("scan_dir")
        root = Path(scan_dir) if scan_dir else tests_dir / domain
        if not root.exists():
            root = tests_dir  # fallback: scan all tests
        names: list[str] = []
        for path in root.rglob("test_*.py"):
            try:
                source = path.read_text(encoding="utf-8", errors="replace")
                names.extend(re.findall(r"^def (test_\w+)", source, re.MULTILINE))
            except Exception:
                pass
        return names

    @staticmethod
    def _parse_gaps(raw: str) -> list[dict]:
        raw = raw.strip()
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip()).get("gaps", [])
