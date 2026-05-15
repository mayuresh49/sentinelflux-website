"""sentinelflux runner — remote test execution daemon.

Polls the SentinelFlux dashboard for queued runs, executes them locally via pytest,
and posts results back. Designed to run on any machine that has the test code and
the right environment (browsers, Appium, etc.) without needing the dashboard co-located.

Usage:
    sentinelflux runner \\
        --api-url https://sentinelflux.example.com \\
        --token sfr_<your_token> \\
        --product orangehrm \\
        --work-dir /path/to/sentinelflux-framework
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

import typer


def run(
    api_url: str = typer.Option(..., help="SentinelFlux dashboard base URL (no trailing slash)"),
    token: str = typer.Option(..., envvar="SF_RUNNER_TOKEN", help="Runner bearer token"),
    product: Optional[str] = typer.Option(None, help="Filter to a specific product; leave empty for all allowed products"),
    poll_interval: int = typer.Option(30, help="Seconds between polls when idle"),
    work_dir: str = typer.Option(".", help="Working directory containing the test codebase"),
    timeout: int = typer.Option(600, help="Max seconds a single pytest run may take"),
):
    """Poll the SentinelFlux dashboard for queued runs and execute them locally."""
    try:
        import httpx
    except ImportError:
        typer.echo("httpx is required: pip install httpx", err=True)
        raise typer.Exit(1)

    api_url = api_url.rstrip("/")
    headers = {"Authorization": f"Bearer {token}"}
    claim_url = f"{api_url}/api/runner/claim"
    work_path = Path(work_dir).resolve()

    typer.echo(f"[runner] Starting. Dashboard: {api_url}  Product filter: {product or 'all'}")
    typer.echo(f"[runner] Work dir: {work_path}  Poll interval: {poll_interval}s")

    while True:
        try:
            params = {"product": product} if product else {}
            resp = httpx.get(claim_url, headers=headers, params=params, timeout=15)
            if resp.status_code == 401:
                typer.echo("[runner] Authentication failed — check your token.", err=True)
                raise typer.Exit(1)
            if resp.status_code != 200:
                typer.echo(f"[runner] Claim error {resp.status_code}: {resp.text}", err=True)
                time.sleep(poll_interval)
                continue

            run_record = resp.json().get("run")
            if not run_record:
                time.sleep(poll_interval)
                continue

            _execute(run_record, api_url, headers, work_path, timeout)

        except typer.Exit:
            raise
        except KeyboardInterrupt:
            typer.echo("\n[runner] Stopped.")
            break
        except Exception as exc:
            typer.echo(f"[runner] Unexpected error: {exc}", err=True)
            time.sleep(poll_interval)


def _execute(run: dict, api_url: str, headers: dict, work_path: Path, timeout: int) -> None:
    import httpx

    run_id = run["id"]
    prod = run.get("product", "")
    domain = run.get("domain", "all")
    module = run.get("module", "")
    typer.echo(f"[runner] Claimed {run_id} — {prod}/{domain}" + (f"/{module}" if module else ""))

    # Resolve test path
    test_base = work_path / "products" / prod / "tests"
    if domain and domain != "all":
        test_dir = test_base / domain
        if not test_dir.exists():
            test_dir = test_base
    else:
        test_dir = test_base

    if module:
        stem = module if module.endswith(".py") else f"{module}.py"
        test_path = test_dir / stem
    else:
        test_path = test_dir

    if not test_path.exists():
        _post_result(api_url, headers, run_id, {}, returncode=2)
        typer.echo(f"[runner] Test path not found: {test_path}", err=True)
        return

    # Build env from run_config_snapshot
    snapshot = run.get("run_config_snapshot", {})
    env_overrides: dict[str, str] = {}
    if snapshot.get("environment"):
        env_overrides["SF_ENV"] = snapshot["environment"]
    if snapshot.get("base_url"):
        env_overrides["SF_BASE_URL"] = snapshot["base_url"]
    if snapshot.get("api_url"):
        env_overrides["SF_API_URL"] = snapshot["api_url"]
    if snapshot.get("browser_type"):
        env_overrides["SF_BROWSER"] = snapshot["browser_type"]
    env_overrides["SF_HEADLESS"] = "1" if snapshot.get("headless", True) else "0"
    if snapshot.get("appium_url"):
        env_overrides["SF_APPIUM_URL"] = snapshot["appium_url"]
    if snapshot.get("device_platform"):
        env_overrides["SF_DEVICE_PLATFORM"] = snapshot["device_platform"]
    if snapshot.get("device_capabilities"):
        env_overrides["SF_DEVICE_CAPABILITIES"] = json.dumps(snapshot["device_capabilities"])

    report_path = work_path / "data" / "runs" / f"{run_id}_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable, "-m", "pytest",
        str(test_path),
        "--json-report", f"--json-report-file={report_path}",
        "-v", "--tb=short", "--no-header",
        "--override-ini=addopts=",
    ]

    progress_url = f"{api_url}/api/runner/{run_id}/progress"
    progress_total = 0
    progress_done = 0

    import re
    _collected_re = re.compile(r"collected (\d+) item")
    _result_re = re.compile(r"\s(PASSED|FAILED|ERROR|SKIPPED)\s")

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, cwd=str(work_path),
        env={**os.environ, **env_overrides},
    )

    last_progress_push = 0.0
    for line in proc.stdout:
        typer.echo(line, nl=False)
        m = _collected_re.search(line)
        if m:
            progress_total = int(m.group(1))
        elif _result_re.search(line):
            progress_done += 1
        now = time.monotonic()
        if now - last_progress_push >= 5.0:
            try:
                httpx.post(progress_url, headers=headers,
                           json={"total": progress_total, "done": progress_done}, timeout=5)
                last_progress_push = now
            except Exception:
                pass

    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
        typer.echo(f"[runner] Run {run_id} timed out after {timeout}s", err=True)
        _post_result(api_url, headers, run_id, {}, returncode=2)
        return

    report = {}
    if report_path.exists():
        try:
            report = json.loads(report_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    _post_result(api_url, headers, run_id, report, returncode=proc.returncode)
    typer.echo(f"[runner] {run_id} finished — returncode {proc.returncode}")


def _post_result(api_url: str, headers: dict, run_id: str, report: dict, returncode: int) -> None:
    import httpx
    try:
        httpx.post(
            f"{api_url}/api/runner/{run_id}/result",
            headers=headers,
            json={"report": report, "returncode": returncode},
            timeout=30,
        )
    except Exception as exc:
        typer.echo(f"[runner] Failed to post result for {run_id}: {exc}", err=True)
