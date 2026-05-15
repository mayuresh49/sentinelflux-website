import typer

from sentinelflux.commands import (
    analyze_cmd,
    dashboard_cmd,
    doctor_cmd,
    generate_cmd,
    init_cmd,
    run_cmd,
)

app = typer.Typer(
    name="sentinelflux",
    help="SentinelFlux — production-grade test automation framework CLI",
    add_completion=False,
)

app.command("init")(init_cmd.run)
app.command("run")(run_cmd.run)
app.command("generate")(generate_cmd.run)
app.command("doctor")(doctor_cmd.run)
app.command("analyze")(analyze_cmd.run)
app.command("dashboard")(dashboard_cmd.run)

if __name__ == "__main__":
    app()
