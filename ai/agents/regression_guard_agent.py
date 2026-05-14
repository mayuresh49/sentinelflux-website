"""RegressionGuardAgent — compares current test run against a baseline to flag regressions."""
from __future__ import annotations

import json
from pathlib import Path

from ai.agents.base_agent import BaseAgent
from utils.paths import ROOT as _ROOT_DIR
_DEFAULT_BASELINE = _ROOT_DIR / "framework_knowledge" / "baseline_report.json"


class RegressionGuardAgent(BaseAgent):
    """
    Compares two pytest JSON reports (from pytest-json-report) and classifies changes.

    Output buckets:
      regressions   — passed in baseline, failing now  (highest priority)
      new_failures  — not in baseline at all, currently failing
      fixed         — failed in baseline, passing now
      new_tests     — not in baseline, currently passing

    No AI call needed — pure set comparison.
    Domain is used only for logging context; all domains supported.

    Extra params (via ctx.extend()):
      save_as_baseline — if True, copy current_report to baseline path after comparison
    """
    name = "regression_guard"

    def run(
        self,
        *,
        current_report: Path,
        baseline_report: Path = _DEFAULT_BASELINE,
    ) -> dict:
        current = self._load(current_report)

        if not baseline_report.exists():
            self._log.warning(
                "No baseline found at %s — saving current run as baseline", baseline_report
            )
            self._save_baseline(current_report, baseline_report)
            return {
                "regressions": [],
                "new_failures": self._failed_ids(current),
                "fixed": [],
                "new_tests": self._passed_ids(current),
                "baseline_created": True,
            }

        baseline = self._load(baseline_report)

        baseline_outcomes = self._outcome_map(baseline)
        current_outcomes = self._outcome_map(current)

        regressions: list[dict] = []
        new_failures: list[dict] = []
        fixed: list[dict] = []
        new_tests: list[str] = []

        for test_id, outcome in current_outcomes.items():
            baseline_outcome = baseline_outcomes.get(test_id)

            if outcome in ("failed", "error"):
                if baseline_outcome == "passed":
                    regressions.append({"test_id": test_id, "baseline": "passed", "current": outcome})
                elif baseline_outcome is None:
                    new_failures.append({"test_id": test_id, "current": outcome})
            elif outcome == "passed":
                if baseline_outcome in ("failed", "error"):
                    fixed.append({"test_id": test_id, "baseline": baseline_outcome, "current": "passed"})
                elif baseline_outcome is None:
                    new_tests.append(test_id)

        self._log.info(
            "[%s] Regressions: %d | New failures: %d | Fixed: %d | New tests: %d",
            self.ctx.domain,
            len(regressions), len(new_failures), len(fixed), len(new_tests),
        )

        if regressions:
            for r in regressions:
                self._log.warning("REGRESSION: %s", r["test_id"])

        if self.ctx.get("save_as_baseline", False):
            self._save_baseline(current_report, baseline_report)
            self._log.info("Baseline updated: %s", baseline_report)

        return {
            "regressions": regressions,
            "new_failures": new_failures,
            "fixed": fixed,
            "new_tests": new_tests,
            "baseline_created": False,
        }

    # ── internal ──────────────────────────────────────────────────────────

    @staticmethod
    def _load(path: Path) -> dict:
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def _outcome_map(report: dict) -> dict[str, str]:
        return {t["nodeid"]: t["outcome"] for t in report.get("tests", [])}

    @staticmethod
    def _failed_ids(report: dict) -> list[dict]:
        return [
            {"test_id": t["nodeid"], "current": t["outcome"]}
            for t in report.get("tests", [])
            if t["outcome"] in ("failed", "error")
        ]

    @staticmethod
    def _passed_ids(report: dict) -> list[str]:
        return [t["nodeid"] for t in report.get("tests", []) if t["outcome"] == "passed"]

    @staticmethod
    def _save_baseline(src: Path, dest: Path):
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(src.read_bytes())
