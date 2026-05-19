"""sentinelflux explore — discover real UI structure from a running application."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

import typer


def run(
    base_url: str = typer.Argument(..., help="App root URL, e.g. http://localhost:8080"),
    pages: str = typer.Option(..., "--pages", help="Comma-separated page paths, e.g. /auth/login,/pim/addEmployee"),
    login_url: Optional[str] = typer.Option(None, "--login-url", help="Login page path for auth before exploring"),
    username: Optional[str] = typer.Option(None, "--username", help="Login username (or set SF_EXPLORE_USER)"),
    password: Optional[str] = typer.Option(None, "--password", help="Login password (or set SF_EXPLORE_PASS)"),
    product: Optional[str] = typer.Option(None, "--project", help="Product name for output paths (e.g. orangehrm)"),
    output_base: Optional[str] = typer.Option(None, "--output-base", help="Root dir for locators + page objects"),
    no_page_objects: bool = typer.Option(False, "--no-page-objects", help="Skip page object generation"),
    no_locators: bool = typer.Option(False, "--no-locators", help="Skip locator JSON output"),
    headless: bool = typer.Option(True, "--headless/--no-headless", help="Run browser headless"),
    show_context: bool = typer.Option(False, "--show-context", help="Print exploration context to stdout"),
):
    """
    Explore a running application to discover real UI elements and flows.

    Generates locator JSON files and page object skeletons grounded in the actual DOM.
    The exploration context can be injected into doc/script generation to prevent hallucination.

    Examples:
        sentinelflux explore http://localhost --pages /auth/login,/pim/addEmployee \\
            --login-url /auth/login --project orangehrm
        sentinelflux explore http://localhost:8080 --pages /booking --show-context
    """
    from ai.agents.app_explorer_agent import AppExplorerAgent
    from ai.agents.base_agent import AgentContext
    from utils.paths import ROOT

    page_list = [p.strip() for p in pages.split(",") if p.strip()]
    if not page_list:
        typer.echo("Error: --pages must contain at least one path", err=True)
        raise typer.Exit(1)

    u = username or os.environ.get("SF_EXPLORE_USER", "")
    p = password or os.environ.get("SF_EXPLORE_PASS", "")
    credentials = {"username": u, "password": p} if u and p else {}

    out_base = Path(output_base).resolve() if output_base else (
        ROOT / "products" / product if product else ROOT
    )

    ctx = AgentContext(domain="web", product=product, output_base=out_base)
    agent = AppExplorerAgent(context=ctx)

    typer.echo(f"Exploring {len(page_list)} page(s) on {base_url} ...")

    result = agent.run(
        base_url=base_url,
        pages=page_list,
        login_url=login_url or "",
        credentials=credentials,
        update_locators=not no_locators,
        generate_page_objects=not no_page_objects,
        headless=headless,
    )

    if not result.get("success"):
        typer.echo(f"Exploration failed: {result.get('error')}", err=True)
        raise typer.Exit(1)

    typer.echo(f"\nExploration complete — {result['pages_explored']} page(s)")
    for r in result.get("results", []):
        typer.echo(
            f"  {r['title']:30s}  {r['fields_found']} fields  {r['buttons_found']} buttons  "
            f"→ {r['exploration_file']}"
        )

    if show_context:
        typer.echo("\n" + result.get("exploration_context", ""))
