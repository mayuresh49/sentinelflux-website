import shutil
from pathlib import Path

import typer

_TEMPLATES = Path(__file__).resolve().parent.parent / "templates"


def run(
    project: str = typer.Argument(..., help="Project directory name to scaffold"),
):
    """Scaffold a new SentinelFlux project."""
    dest = Path(project)
    if dest.exists():
        typer.echo(f"[error] '{project}' already exists.", err=True)
        raise typer.Exit(1)

    dest.mkdir(parents=True)
    dirs = [
        "tests/web", "tests/api", "tests/mobile",
        "pages/web", "pages/mobile",
        "api", "locators", "config", "docs", "reports", "logs",
    ]
    for d in dirs:
        (dest / d).mkdir(parents=True, exist_ok=True)

    for src in _TEMPLATES.rglob("*"):
        if src.is_file():
            rel = src.relative_to(_TEMPLATES)
            target = dest / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(src, target)

    typer.echo(f"[ok] Project '{project}' created.")
    typer.echo(f"     1. cd {project}")
    typer.echo("     2. pip install sentinelflux[ai]")
    typer.echo("     3. playwright install")
    typer.echo("     4. Edit config/env_qa.yaml, then: sentinelflux run")
