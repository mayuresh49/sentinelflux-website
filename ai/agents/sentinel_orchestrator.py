"""
SentinelOrchestrator — coordinates all monitoring agents after a test suite run.

Sequence:
  1. ResultAnalyzerAgent  — classify failures with AI
  2. FlakyDetectorAgent   — detect flaky patterns from run history
  3. QuarantineManager    — propose quarantine/unquarantine (feeds ApprovalManager)
  4. RegressionGuardAgent — detect regressions vs baseline
  5. CoverageGapAgent     — find KB scenarios not covered by existing tests
  6. LocatorHealerAgent   — propose healed selectors (web/mobile only, when failures provided)

Each step is fault-tolerant: a failed agent logs an error but does not abort the sequence.
All outputs are written to ActivityLog. Human-gated actions go to ApprovalManager.
Returns a structured summary with blockers list for the UI.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from ai.agents.base_agent import AgentContext
from ai.agents.quarantine_manager import _HISTORY_PATH, QuarantineManager
from core.activity_log import ActivityLog
from core.approval_manager import ApprovalManager
from utils.paths import ROOT as _ROOT_DIR

_log = logging.getLogger("sentinelflux.sentinel_orchestrator")


class SentinelOrchestrator:
    """
    Post-suite monitoring pipeline coordinator.

    Usage:
        orch = SentinelOrchestrator(ai_client=client, kb_loader=kb)
        summary = orch.run_post_suite(
            current_report=Path(".sentinelflux_report.json"),
            domain="api",
            product="restfulbooker",
        )
        print(summary["blockers"])
    """

    def __init__(
        self,
        ai_client=None,
        kb_loader=None,
        activity_log: ActivityLog | None = None,
        approval_manager: ApprovalManager | None = None,
    ):
        self.ai_client = ai_client
        self.kb_loader = kb_loader
        self._alog = activity_log or ActivityLog()
        self._approvals = approval_manager or ApprovalManager()

    def run_post_suite(
        self,
        current_report: Path,
        domain: str,
        product: str | None = None,
        env: str = "qa",
        artifacts_dir: Path | None = None,
        baseline_report: Path | None = None,
        save_as_baseline: bool = False,
        tests_dir: Path | None = None,
        locator_failures: list[dict] | None = None,
    ) -> dict[str, Any]:
        """
        Run all monitoring agents and return a unified summary.

        locator_failures: list of dicts with keys:
          element_name, failed_selector, page_context, locator_file (optional)

        Returns:
          {
            product, domain, blockers, blockers_count, requires_human,
            failure_count, regression_count, flaky_candidates,
            coverage_gaps, locator_heals, steps
          }
        """
        ctx = AgentContext(domain=domain, product=product, env=env)
        blockers: list[dict] = []
        steps: list[dict] = []

        failure_result = self._run_result_analyzer(ctx, current_report, artifacts_dir, steps)
        flaky_result = self._run_flaky_detector(ctx, blockers, steps)
        regression_result = self._run_regression_guard(ctx, current_report, baseline_report, save_as_baseline, blockers, steps)
        gap_result = self._run_coverage_gap(ctx, tests_dir, blockers, steps)
        heal_result = self._run_locator_healer(ctx, locator_failures or [], blockers, steps)

        summary: dict[str, Any] = {
            "product": product,
            "domain": domain,
            "blockers": blockers,
            "blockers_count": len(blockers),
            "requires_human": len(blockers) > 0,
            "failure_count": failure_result.get("total", 0),
            "regression_count": len(regression_result.get("regressions", [])),
            "flaky_candidates": len(flaky_result.get("quarantine_candidates", [])),
            "coverage_gaps": len(gap_result.get("gaps", [])),
            "locator_heals": len(heal_result),
            "steps": steps,
        }

        blocker_msg = (
            f"{len(blockers)} blocker(s) require human review"
            if blockers else "No blockers — pipeline clean"
        )
        self._alog.append(
            event_type="orchestrator_run",
            agent="sentinel_orchestrator",
            domain=domain,
            product=product,
            status="pending" if blockers else "success",
            summary=blocker_msg,
            output=summary,
            requires_human=len(blockers) > 0,
        )
        _log.info("SentinelOrchestrator complete — %s", blocker_msg)
        return summary

    # ── steps ──────────────────────────────────────────────────────────────

    def _run_result_analyzer(self, ctx, report_path, artifacts_dir, steps):
        if not self.ai_client:
            _log.info("No AI client — skipping ResultAnalyzerAgent")
            steps.append({"agent": "result_analyzer", "status": "skipped", "reason": "no_ai_client"})
            return {"total": 0, "failures": []}
        try:
            from ai.agents.result_analyzer_agent import ResultAnalyzerAgent
            agent = ResultAnalyzerAgent(ai_client=self.ai_client, context=ctx)
            arts = artifacts_dir or (_ROOT_DIR / "reports" / "artifacts")
            result = agent.run(report_path=report_path, artifacts_dir=arts)
            self._alog.append(
                event_type="agent_run", agent="result_analyzer",
                domain=ctx.domain, product=ctx.product,
                status="success",
                summary=f"{result['total']} failure(s) classified",
                output=result,
            )
            steps.append({"agent": "result_analyzer", "status": "success"})
            return result
        except Exception as exc:
            _log.error("ResultAnalyzerAgent error: %s", exc)
            steps.append({"agent": "result_analyzer", "status": "error", "error": str(exc)})
            return {"total": 0, "failures": []}

    def _run_flaky_detector(self, ctx, blockers, steps):
        try:
            from ai.agents.flaky_detector_agent import FlakyDetectorAgent
            agent = FlakyDetectorAgent(context=ctx)
            result = agent.run(history_path=_HISTORY_PATH)

            qm = QuarantineManager()
            qm.propose(result["quarantine_candidates"], result["unquarantine_candidates"])

            approval_ids = []
            for c in result["quarantine_candidates"]:
                aid = self._approvals.submit(
                    approval_type="quarantine",
                    title=f"Quarantine: {c['test_id']}",
                    domain=ctx.domain, product=ctx.product,
                    details=c,
                )
                approval_ids.append(aid)
            for c in result["unquarantine_candidates"]:
                aid = self._approvals.submit(
                    approval_type="unquarantine",
                    title=f"Unquarantine: {c['test_id']}",
                    domain=ctx.domain, product=ctx.product,
                    details=c,
                )
                approval_ids.append(aid)

            q = len(result["quarantine_candidates"])
            u = len(result["unquarantine_candidates"])
            entry_id = self._alog.append(
                event_type="agent_run", agent="flaky_detector",
                domain=ctx.domain, product=ctx.product,
                status="success",
                summary=f"{q} quarantine, {u} unquarantine candidate(s)",
                output=result,
                requires_human=bool(approval_ids),
            )
            if approval_ids:
                blockers.append({
                    "type": "quarantine",
                    "count": len(approval_ids),
                    "approval_ids": approval_ids,
                    "activity_id": entry_id,
                })
            steps.append({"agent": "flaky_detector", "status": "success"})
            return result
        except Exception as exc:
            _log.error("FlakyDetectorAgent error: %s", exc)
            steps.append({"agent": "flaky_detector", "status": "error", "error": str(exc)})
            return {"quarantine_candidates": [], "unquarantine_candidates": []}

    def _run_regression_guard(self, ctx, current_report, baseline_report, save_as_baseline, blockers, steps):
        try:
            from ai.agents.regression_guard_agent import RegressionGuardAgent
            guard_ctx = ctx.extend(save_as_baseline=save_as_baseline)
            agent = RegressionGuardAgent(context=guard_ctx)
            kwargs: dict[str, Any] = {"current_report": current_report}
            if baseline_report:
                kwargs["baseline_report"] = baseline_report
            result = agent.run(**kwargs)

            regs = result.get("regressions", [])
            approval_ids = []
            for r in regs:
                aid = self._approvals.submit(
                    approval_type="regression_review",
                    title=f"Regression: {r['test_id']}",
                    domain=ctx.domain, product=ctx.product,
                    details=r,
                )
                approval_ids.append(aid)

            entry_id = self._alog.append(
                event_type="agent_run", agent="regression_guard",
                domain=ctx.domain, product=ctx.product,
                status="success",
                summary=f"{len(regs)} regression(s) detected" if regs else "No regressions",
                output=result,
                requires_human=bool(regs),
            )
            if regs:
                blockers.append({
                    "type": "regression",
                    "count": len(regs),
                    "approval_ids": approval_ids,
                    "activity_id": entry_id,
                })
            steps.append({"agent": "regression_guard", "status": "success"})
            return result
        except Exception as exc:
            _log.error("RegressionGuardAgent error: %s", exc)
            steps.append({"agent": "regression_guard", "status": "error", "error": str(exc)})
            return {"regressions": [], "fixed": [], "new_failures": [], "new_tests": []}

    def _run_coverage_gap(self, ctx, tests_dir, blockers, steps):
        if not self.ai_client or not self.kb_loader:
            _log.info("No AI client or KB loader — skipping CoverageGapAgent")
            steps.append({"agent": "coverage_gap", "status": "skipped", "reason": "no_ai_or_kb"})
            return {"gaps": []}
        try:
            from ai.agents.coverage_gap_agent import CoverageGapAgent
            agent = CoverageGapAgent(ai_client=self.ai_client, kb_loader=self.kb_loader, context=ctx)
            scan_dir = tests_dir or (
                _ROOT_DIR / "products" / ctx.product if ctx.product
                else _ROOT_DIR / "tests" / ctx.domain
            )
            result = agent.run(tests_dir=scan_dir)

            gaps = result.get("gaps", [])
            approval_ids = []
            if gaps:
                aid = self._approvals.submit(
                    approval_type="coverage_gap",
                    title=f"{len(gaps)} coverage gap(s) in {ctx.domain}",
                    domain=ctx.domain, product=ctx.product,
                    details=result,
                )
                approval_ids.append(aid)

            entry_id = self._alog.append(
                event_type="agent_run", agent="coverage_gap",
                domain=ctx.domain, product=ctx.product,
                status="success",
                summary=f"{len(gaps)} untested scenario(s)" if gaps else "Full KB coverage",
                output=result,
                requires_human=bool(gaps),
            )
            if approval_ids:
                blockers.append({
                    "type": "coverage_gap",
                    "count": len(gaps),
                    "approval_ids": approval_ids,
                    "activity_id": entry_id,
                })
            steps.append({"agent": "coverage_gap", "status": "success"})
            return result
        except Exception as exc:
            _log.error("CoverageGapAgent error: %s", exc)
            steps.append({"agent": "coverage_gap", "status": "error", "error": str(exc)})
            return {"gaps": []}

    def _run_locator_healer(self, ctx, locator_failures, blockers, steps):
        if ctx.domain not in ("web", "mobile") or not locator_failures:
            steps.append({"agent": "locator_healer", "status": "skipped", "reason": "no_failures_or_wrong_domain"})
            return []
        if not self.ai_client:
            steps.append({"agent": "locator_healer", "status": "skipped", "reason": "no_ai_client"})
            return []
        try:
            from ai.agents.locator_healer_agent import LocatorHealerAgent
            # dry_run=True: propose only — approval_dispatch writes on approval
            agent = LocatorHealerAgent(ai_client=self.ai_client, context=ctx.extend(dry_run=True))
            heals = []
            for lf in locator_failures:
                result = agent.run(
                    element_name=lf["element_name"],
                    failed_selector=lf["failed_selector"],
                    page_context=lf.get("page_context", ""),
                    locator_file=Path(lf["locator_file"]) if lf.get("locator_file") else None,
                )
                if result:
                    heals.append(result)
                    aid = self._approvals.submit(
                        approval_type="locator_heal",
                        title=f"Heal locator: {lf['element_name']}",
                        domain=ctx.domain, product=ctx.product,
                        details={**lf, "proposal": result},
                    )
                    blockers.append({
                        "type": "locator_heal",
                        "count": 1,
                        "approval_ids": [aid],
                        "element": lf["element_name"],
                    })

            if heals:
                self._alog.append(
                    event_type="agent_run", agent="locator_healer",
                    domain=ctx.domain, product=ctx.product,
                    status="success",
                    summary=f"{len(heals)} locator heal(s) proposed",
                    output={"heals": heals},
                    requires_human=True,
                )
            steps.append({"agent": "locator_healer", "status": "success", "heal_count": len(heals)})
            return heals
        except Exception as exc:
            _log.error("LocatorHealerAgent error: %s", exc)
            steps.append({"agent": "locator_healer", "status": "error", "error": str(exc)})
            return []
