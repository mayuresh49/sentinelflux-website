"""FlakyDetectorAgent — reads run history and identifies quarantine/unquarantine candidates."""
from __future__ import annotations

from pathlib import Path

import yaml

from ai.agents.base_agent import BaseAgent

_DEFAULT_WINDOW = 10
_DEFAULT_FAIL_THRESHOLD = 0.3   # >= 30% fail rate → quarantine candidate
_DEFAULT_PASS_STREAK = 5        # >= 5 consecutive passes → unquarantine candidate


class FlakyDetectorAgent(BaseAgent):
    """
    Pure rule-based detection (no AI call needed).

    Reads data/run_history.yaml and emits two lists:
      quarantine_candidates  — tests that fail too often
      unquarantine_candidates — tests that have stabilised

    Does NOT write quarantine.yaml — passes candidates to QuarantineManager.propose().

    Extra params (via ctx.extend()):
      window          — how many recent runs to consider (default 10)
      fail_threshold  — fraction of failures to trigger quarantine (default 0.3)
      pass_streak     — consecutive passes to trigger unquarantine (default 5)
    """
    name = "flaky_detector"

    def run(
        self,
        *,
        history_path: Path,
    ) -> dict:
        window = self.ctx.get("window", _DEFAULT_WINDOW)
        threshold = self.ctx.get("fail_threshold", _DEFAULT_FAIL_THRESHOLD)
        streak = self.ctx.get("pass_streak", _DEFAULT_PASS_STREAK)

        history = self._load(history_path)
        quarantine_candidates: list[dict] = []
        unquarantine_candidates: list[dict] = []

        for test_id, runs in history.get("tests", {}).items():
            recent = runs[-window:]
            if not recent:
                continue

            statuses = [r["status"] for r in recent]
            fail_rate = statuses.count("failed") / len(statuses)
            consecutive_passes = _trailing_passes(statuses)

            if fail_rate >= threshold and statuses[-1] == "failed":
                quarantine_candidates.append({
                    "test_id": test_id,
                    "fail_rate": round(fail_rate, 2),
                    "window": len(recent),
                    "rule": f"fail_rate {fail_rate:.0%} >= {threshold:.0%} over last {len(recent)} runs",
                })
            elif consecutive_passes >= streak:
                unquarantine_candidates.append({
                    "test_id": test_id,
                    "consecutive_passes": consecutive_passes,
                    "rule": f"passed {consecutive_passes} consecutive times",
                })

        self._log.info(
            "Flaky detection: %d quarantine, %d unquarantine candidates",
            len(quarantine_candidates),
            len(unquarantine_candidates),
        )
        return {
            "quarantine_candidates": quarantine_candidates,
            "unquarantine_candidates": unquarantine_candidates,
        }

    @staticmethod
    def _load(path: Path) -> dict:
        if not path.exists():
            return {"tests": {}}
        with path.open(encoding="utf-8") as f:
            return yaml.safe_load(f) or {"tests": {}}


def _trailing_passes(statuses: list[str]) -> int:
    count = 0
    for s in reversed(statuses):
        if s == "passed":
            count += 1
        else:
            break
    return count
