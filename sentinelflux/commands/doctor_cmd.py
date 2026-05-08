import shutil
import subprocess
import sys
from pathlib import Path

import typer

_MIN_PYTHON = (3, 10)


def run():
    """Check that the SentinelFlux environment is correctly set up."""
    ok = True

    def _check(label: str, passed: bool, detail: str = ""):
        nonlocal ok
        icon = "[ok]" if passed else "[fail]"
        msg = f"  {icon}  {label}"
        if detail:
            msg += f" — {detail}"
        typer.echo(msg)
        if not passed:
            ok = False

    typer.echo("\nSentinelFlux environment check\n")

    # Python version
    v = sys.version_info
    _check(
        f"Python >= {_MIN_PYTHON[0]}.{_MIN_PYTHON[1]}",
        v >= _MIN_PYTHON,
        f"{v.major}.{v.minor}.{v.micro}",
    )

    # Core packages
    for pkg in ("pytest", "playwright", "yaml", "requests"):
        try:
            __import__(pkg)
            _check(f"Package: {pkg}", True)
        except ImportError:
            _check(f"Package: {pkg}", False, "not installed — run: pip install sentinelflux")

    # Playwright browsers
    playwright_cli = shutil.which("playwright")
    if playwright_cli:
        result = subprocess.run(
            ["playwright", "install", "--dry-run"],
            capture_output=True, text=True
        )
        browsers_ok = result.returncode == 0
        _check("Playwright browsers", browsers_ok, "run: playwright install" if not browsers_ok else "")
    else:
        _check("Playwright CLI", False, "run: pip install playwright && playwright install")

    # AI / Mistral (optional)
    try:
        import mistralai  # noqa: F401
        _check("AI: mistralai package", True)
    except ImportError:
        _check("AI: mistralai package", False, "optional — pip install sentinelflux[ai]")

    # Config file
    config_path = Path("config") / "env_qa.yaml"
    _check(
        "config/env_qa.yaml",
        config_path.exists(),
        "" if config_path.exists() else "copy from config/env_template.yaml",
    )

    # Locators dir
    _check("locators/ directory", Path("locators").exists())

    typer.echo("")
    if ok:
        typer.echo("All checks passed.")
    else:
        typer.echo("Some checks failed — fix the issues above before running tests.")
        raise typer.Exit(1)
