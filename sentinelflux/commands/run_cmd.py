import subprocess
import sys
from typing import Optional
import typer


def run(
    suite: Optional[str] = typer.Argument(None, help="Test path or marker (e.g. tests/web, 'web')"),
    env: str = typer.Option("qa", help="Environment profile"),
    browser: str = typer.Option("chromium", help="Playwright browser"),
    workers: int = typer.Option(1, "-n", help="Parallel worker count"),
    session_login: bool = typer.Option(False, "--session-login", help="Reuse one login per worker"),
    extra: Optional[str] = typer.Option(None, "--extra", help="Extra pytest args (quoted string)"),
):
    """Run tests via pytest with SentinelFlux defaults."""
    cmd = [sys.executable, "-m", "pytest"]

    if suite:
        if "/" in suite or suite.startswith("tests"):
            cmd.append(suite)
        else:
            cmd += ["-m", suite]

    cmd += [f"--env={env}", f"--browser={browser}"]

    if workers > 1:
        cmd += ["-n", str(workers)]
    if session_login:
        cmd.append("--session-login")
    if extra:
        cmd += extra.split()

    typer.echo(f"[run] {' '.join(cmd)}")
    result = subprocess.run(cmd)
    raise typer.Exit(result.returncode)
