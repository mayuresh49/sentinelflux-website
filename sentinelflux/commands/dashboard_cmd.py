"""sentinelflux dashboard — start the monitoring dashboard API server."""
from __future__ import annotations

import typer

_console_msg = "SentinelFlux Dashboard starting at http://{host}:{port} — Ctrl+C to stop"


def run(
    host: str = typer.Option("127.0.0.1", "--host", help="Bind host"),
    port: int = typer.Option(8000, "--port", help="Bind port"),
    reload: bool = typer.Option(False, "--reload", help="Enable auto-reload (dev mode)"),
):
    """Start the SentinelFlux monitoring dashboard API (FastAPI + uvicorn)."""
    try:
        import uvicorn
    except ImportError:
        typer.echo("uvicorn not installed. Run: pip install 'sentinelflux[dashboard]'")
        raise typer.Exit(1)

    typer.echo(_console_msg.format(host=host, port=port))
    typer.echo("API docs: http://{}:{}/docs".format(host, port))
    uvicorn.run("dashboard.app:app", host=host, port=port, reload=reload)
