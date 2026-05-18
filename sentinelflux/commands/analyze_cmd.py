"""sentinelflux analyze — run tests, classify failures, detect flaky tests."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

_console = Console()
_ROOT_DIR = Path(__file__).resolve().parent.parent.parent


def run(
    domain: str = typer.Option("api", "--domain", "-d", help="Test domain: api | web | mobile | security"),
    product: Optional[str] = typer.Option(None, "--product", "-p", help="Product name (e.g. orangehrm)"),
    report: Optional[str] = typer.Option(None, "--report", help="Path to existing pytest-json-report JSON (skips test run)"),
    tests_dir: Optional[str] = typer.Option(None, "--tests-dir", help="Directory to run tests from"),
    artifacts_dir: Optional[str] = typer.Option(None, "--artifacts-dir", help="Directory containing failure artifacts"),
    baseline: Optional[str] = typer.Option(None, "--baseline", help="Baseline report for regression comparison"),
    apply_quarantine: bool = typer.Option(False, "--apply-quarantine", help="Immediately apply quarantine proposals (skip human gate)"),
    save_baseline: bool = typer.Option(False, "--save-baseline", help="Save current report as new baseline after analysis"),
    env: str = typer.Option("qa", "--env", help="Environment profile"),
):
    """
    Run tests, classify failures with AI, detect flaky patterns, and propose quarantine actions.

    Examples:
      sentinelflux analyze --domain api --product restfulbooker
      sentinelflux analyze --domain web --product orangehrm --tests-dir products/orangehrm
      sentinelflux analyze --report .sentinelflux_report.json --domain api
      sentinelflux analyze --domain api --apply-quarantine
    """
    from ai.agents import AgentContext, FlakyDetectorAgent, ResultAnalyzerAgent
    from ai.agents.quarantine_manager import QuarantineManager
    from core.ai_factory import create_ai_client_from_dashboard

    # ── 1. Resolve report ─────────────────────────────────────────────────
    report_path = Path(report) if report else _ROOT_DIR / ".sentinelflux_report.json"

    if not report:
        run_dir = Path(tests_dir) if tests_dir else _resolve_tests_dir(domain, product)
        _console.print(f"\n[bold cyan]Running tests:[/] {run_dir}")
        success = _run_pytest(run_dir, domain, report_path, env)
        if not success and not report_path.exists():
            _console.print("[red]Test run failed and no report was generated.[/]")
            raise typer.Exit(1)

    if not report_path.exists():
        _console.print(f"[red]Report not found: {report_path}[/]")
        raise typer.Exit(1)

    # ── 2. Load AI client ─────────────────────────────────────────────────
    ai_client = create_ai_client_from_dashboard()

    ctx = AgentContext(domain=domain, product=product, env=env)

    # ── 3. Failure classification ─────────────────────────────────────────
    _console.print("\n[bold cyan]Classifying failures...[/]")
    if ai_client:
        analyzer = ResultAnalyzerAgent(ai_client=ai_client, context=ctx)
        artifacts = Path(artifacts_dir) if artifacts_dir else _ROOT_DIR / "reports" / "artifacts"
        analysis = analyzer.run(report_path=report_path, artifacts_dir=artifacts)
        _print_failures(analysis)
    else:
        _console.print("[yellow]AI not configured — skipping failure classification (set sentinelflux.ai.enabled: true)[/]")
        analysis = {"failures": [], "total": 0}

    # ── 4. Regression guard ───────────────────────────────────────────────
    _console.print("\n[bold cyan]Checking for regressions...[/]")
    from ai.agents.regression_guard_agent import RegressionGuardAgent
    baseline_path = Path(baseline) if baseline else None
    guard_ctx = ctx.extend(save_as_baseline=save_baseline)
    guard = RegressionGuardAgent(context=guard_ctx)
    kwargs = {"current_report": report_path}
    if baseline_path:
        kwargs["baseline_report"] = baseline_path
    regression_result = guard.run(**kwargs)
    _print_regressions(regression_result)

    # ── 5. Flaky detection ────────────────────────────────────────────────
    _console.print("\n[bold cyan]Detecting flaky tests...[/]")
    detector = FlakyDetectorAgent(context=ctx)
    flaky_result = detector.run()
    _print_flaky(flaky_result)

    # ── 6. Quarantine proposals ───────────────────────────────────────────
    qm = QuarantineManager()
    proposed = qm.propose(
        flaky_result["quarantine_candidates"],
        flaky_result["unquarantine_candidates"],
    )
    if proposed:
        _console.print(f"\n[yellow]{proposed} quarantine action(s) proposed → dashboard approval queue[/]")
        if apply_quarantine:
            applied = qm.apply_pending()
            _console.print(f"[green]Applied: {len(applied['quarantined'])} quarantined, {len(applied['unquarantined'])} released[/]")
        else:
            _console.print("[dim]Run with --apply-quarantine to activate, or approve via the dashboard.[/]")

    # ── Summary ───────────────────────────────────────────────────────────
    _print_summary(analysis, regression_result, flaky_result)


# ── helpers ───────────────────────────────────────────────────────────────────

def _run_pytest(tests_dir: Path, domain: str, report_path: Path, env: str) -> bool:
    cmd = [
        sys.executable, "-m", "pytest",
        str(tests_dir),
        "-m", domain,
        "--json-report", f"--json-report-file={report_path}",
        "--tb=short", "-q",
        f"--env={env}",
    ]
    result = subprocess.run(cmd, cwd=tests_dir)
    return result.returncode == 0


def _resolve_tests_dir(domain: str, product: Optional[str]) -> Path:
    if product:
        candidate = _ROOT_DIR / "products" / product
        if candidate.exists():
            return candidate
    return _ROOT_DIR / "tests" / domain


def _load_config(env: str) -> dict:
    import yaml
    cfg_file = _ROOT_DIR / "config" / f"env_{env}.yaml"
    if not cfg_file.exists():
        return {}
    with cfg_file.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _print_failures(analysis: dict):
    if not analysis["failures"]:
        _console.print("[green]  No failures to classify.[/]")
        return
    table = Table(title=f"Failure Analysis ({analysis['total']} failures)", show_lines=True)
    table.add_column("Test", style="dim", max_width=60)
    table.add_column("Class", style="bold")
    table.add_column("Conf", justify="right")
    table.add_column("Summary", max_width=50)
    for f in analysis["failures"]:
        cls = f.get("classification", "?")
        color = {"assertion": "yellow", "infra": "red", "flaky": "magenta",
                 "env": "blue", "locator": "cyan"}.get(cls, "white")
        table.add_row(
            f["test_id"].split("::")[-1],
            f"[{color}]{cls}[/{color}]",
            f"{f.get('confidence', 0):.0%}",
            f.get("summary", ""),
        )
    _console.print(table)


def _print_regressions(result: dict):
    regs = result.get("regressions", [])
    if result.get("baseline_created"):
        _console.print("[yellow]  No baseline existed — current run saved as baseline.[/]")
    elif not regs:
        _console.print("[green]  No regressions detected.[/]")
    else:
        _console.print(f"[red bold]  {len(regs)} regression(s):[/]")
        for r in regs:
            _console.print(f"  [red]✗[/] {r['test_id']}")
    fixed = result.get("fixed", [])
    if fixed:
        _console.print(f"[green]  {len(fixed)} test(s) fixed since baseline.[/]")


def _print_flaky(result: dict):
    q = result.get("quarantine_candidates", [])
    u = result.get("unquarantine_candidates", [])
    if not q and not u:
        _console.print("[green]  No flaky patterns detected.[/]")
        return
    if q:
        _console.print(f"[magenta]  {len(q)} quarantine candidate(s):[/]")
        for c in q:
            _console.print(f"  [magenta]~[/] {c['test_id']} ({c['fail_rate']:.0%} fail rate)")
    if u:
        _console.print(f"[green]  {len(u)} ready to unquarantine:[/]")
        for c in u:
            _console.print(f"  [green]✓[/] {c['test_id']} ({c['consecutive_passes']} consecutive passes)")


def _print_summary(analysis: dict, regression: dict, flaky: dict):
    _console.print("\n[bold]──────────────────────────── Summary ────────────────────────────[/]")
    _console.print(f"  Failures classified : {analysis['total']}")
    _console.print(f"  Regressions         : {len(regression.get('regressions', []))}")
    _console.print(f"  Flaky candidates    : {len(flaky.get('quarantine_candidates', []))}")
    _console.print(f"  Ready to release    : {len(flaky.get('unquarantine_candidates', []))}")
    _console.print("")
