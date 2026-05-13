"""ResultAnalyzerAgent — classifies test failures using AI + domain-specific artifacts."""
from __future__ import annotations

import json
import logging
from pathlib import Path

from ai.agents.base_agent import BaseAgent
from ai.agents.registry import FAILURE_CLASSIFICATIONS

_CLASSIFY_PROMPT = """\
You are a test failure analyst. Classify the failure and provide a concise diagnosis.

Domain: {domain}
Analysis guidance: {hint}

Test ID: {test_id}
Error:
{error}

{artifacts_section}

Respond in JSON only — no prose, no markdown fences:
{{
  "classification": "<{classifications}>",
  "confidence": <0.0-1.0>,
  "summary": "<one-sentence diagnosis>",
  "suggestion": "<one-sentence fix recommendation>"
}}
"""


class ResultAnalyzerAgent(BaseAgent):
    """
    Reads a pytest JSON report (from pytest-json-report) and classifies each failure.

    Domain controls which artifact files are read for each failed test:
      api      → api_calls.log
      web      → screenshot_full_page.png (skipped, binary), console.log, trace.zip (skipped)
      mobile   → screenshot.png (skipped), logcat.txt
      security → api_calls.log

    Extra params (via ctx.extend()):
      max_error_chars   — truncate error text (default 3000)
      max_artifact_chars — truncate each artifact file (default 2000)
    """
    name = "result_analyzer"

    def run(
        self,
        *,
        report_path: Path,
        artifacts_dir: Path | None = None,
    ) -> dict:
        report = self._load_report(report_path)
        results = []

        for test in report.get("tests", []):
            if test.get("outcome") not in ("failed", "error"):
                continue
            result = self._analyze(test, artifacts_dir)
            results.append(result)
            self._log.info(
                "[%s] %s (%.0f%%) — %s",
                result["classification"].upper(),
                result["test_id"],
                result["confidence"] * 100,
                result["summary"],
            )

        return {
            "domain": self.ctx.domain,
            "failures": results,
            "total": len(results),
            "by_classification": self._tally(results),
        }

    # ── internal ──────────────────────────────────────────────────────────

    def _analyze(self, test: dict, artifacts_dir: Path | None) -> dict:
        test_id = test.get("nodeid", "unknown")
        max_err = self.ctx.get("max_error_chars", 3000)
        error = (
            test.get("call", {}).get("longrepr", "")
            or test.get("longrepr", "")
            or ""
        )

        artifacts_text = ""
        if artifacts_dir:
            safe_id = (
                test_id.replace("/", "_")
                       .replace("::", "__")
                       .replace("[", "_")
                       .replace("]", "")
            )
            artifacts_text = self._read_artifacts(artifacts_dir / safe_id)

        prompt = _CLASSIFY_PROMPT.format(
            domain=self.ctx.domain,
            hint=self._failure_hint(),
            test_id=test_id,
            error=str(error)[:max_err],
            artifacts_section=f"Artifacts:\n{artifacts_text}" if artifacts_text else "No artifacts available.",
            classifications="|".join(FAILURE_CLASSIFICATIONS),
        )

        try:
            raw = self.client.generate(prompt, max_tokens=512, temperature=0.1)
            parsed = self._parse_json(raw)
        except Exception as exc:
            self._log.warning("AI classification failed for %s: %s", test_id, exc)
            parsed = {
                "classification": "unknown",
                "confidence": 0.0,
                "summary": str(error)[:200],
                "suggestion": "Manual investigation required.",
            }

        return {"test_id": test_id, **parsed}

    def _read_artifacts(self, artifact_dir: Path) -> str:
        max_chars = self.ctx.get("max_artifact_chars", 2000)
        parts = []
        for name in self._artifact_names():
            path = artifact_dir / name
            if not path.exists():
                continue
            if path.suffix in (".png", ".zip", ".webm"):
                parts.append(f"--- {name} --- [binary, not included]")
                continue
            content = path.read_text(encoding="utf-8", errors="replace")
            parts.append(f"--- {name} ---\n{content[:max_chars]}")
        return "\n".join(parts)

    @staticmethod
    def _load_report(path: Path) -> dict:
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def _parse_json(raw: str) -> dict:
        raw = raw.strip()
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())

    @staticmethod
    def _tally(results: list[dict]) -> dict[str, int]:
        counts: dict[str, int] = {}
        for r in results:
            c = r.get("classification", "unknown")
            counts[c] = counts.get(c, 0) + 1
        return counts
