"""CTOAgent — synthesises all 4 expert insights into a strategic top-5 roadmap."""
from __future__ import annotations

import json
import re

from ai.agents.base_agent import BaseAgent


class CTOAgent(BaseAgent):
    """
    Reads all active insights from the 4 product review agents and asks the LLM
    to select the top 4-5 most strategically important items with rationale.
    Returns {items: [{insight: dict, rationale: str}]}.
    """
    name = "cto"

    def run(self, **kwargs) -> dict:
        if not self.client:
            return {"items": [], "error": "No AI client configured"}

        from core.insights_manager import InsightsManager
        all_insights = InsightsManager().list_insights(status="active")
        if not all_insights:
            return {"items": [], "error": "No active insights to review — run the 4 expert agents first"}

        numbered = []
        for i, ins in enumerate(all_insights):
            label = ins["agent_type"].replace("_", " ").title()
            numbered.append(
                f"[{i + 1}] [{label}] {ins['title']}\n"
                f"    Category: {ins['category']} | Priority: {ins['priority']}\n"
                f"    {ins['description'][:200]}\n"
                f"    Recommendation: {ins['recommendation'][:150]}"
            )

        prompt = (
            f"You are the CEO/CTO of SentinelFlux reviewing {len(all_insights)} expert insights.\n\n"
            f"Insights:\n" + "\n\n".join(numbered) + "\n\n"
            "Select the top 4-5 most strategically important items to execute now. Consider:\n"
            "- Cross-cutting concerns that unlock multiple other improvements\n"
            "- High-risk items that could block adoption or cause failures\n"
            "- Quick wins with disproportionate leverage\n"
            "- Balance across product, engineering, quality, and UX\n\n"
            "Return JSON only — no markdown fences:\n"
            '{"selections": [{"index": <1-based>, "rationale": "<1-2 sentences why this is top priority now>"}]}\n'
            "Select exactly 4-5 items."
        )

        raw = self.client.generate(prompt, max_tokens=1200, temperature=0.3)
        selections = self._parse(raw)

        items = []
        for sel in selections:
            idx = sel.get("index", 0) - 1
            if 0 <= idx < len(all_insights):
                items.append({
                    "insight": all_insights[idx],
                    "rationale": sel.get("rationale", ""),
                })

        self._log.info("CTOAgent: selected %d roadmap items", len(items))
        return {"items": items}

    @staticmethod
    def _parse(raw: str) -> list[dict]:
        raw = raw.strip()
        fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
        if fence:
            raw = fence.group(1).strip()
        try:
            data = json.loads(raw)
            sels = data.get("selections", data) if isinstance(data, dict) else data
        except (json.JSONDecodeError, TypeError):
            return []
        out = []
        for s in (sels if isinstance(sels, list) else []):
            if isinstance(s, dict) and s.get("index"):
                s.setdefault("rationale", "")
                out.append(s)
        return out[:5]
