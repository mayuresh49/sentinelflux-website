import subprocess
import sys
from pathlib import Path
from typing import Optional
import typer


def run(
    config: str = typer.Option("config/env_qa.yaml", help="Environment config path"),
    output: Optional[str] = typer.Option(None, help="Output path for generated test case doc"),
    endpoint: Optional[str] = typer.Option(None, help="API endpoint for API test generation"),
    method: str = typer.Option("GET", help="HTTP method for API test generation"),
    script: bool = typer.Option(False, "--script", help="Also generate pytest script from doc"),
):
    """Generate test cases from the knowledge base using AI."""
    if endpoint:
        module = "ai.generate_api_test_doc"
        args = ["--endpoint", endpoint, "--method", method]
    else:
        module = "ai.generate_test_case_doc"
        args = ["--config", config]

    if output:
        args += ["--output", output]

    cmd = [sys.executable, "-m", module] + args
    typer.echo(f"[generate] {' '.join(cmd)}")
    result = subprocess.run(cmd)

    if result.returncode != 0 or not script or not output:
        raise typer.Exit(result.returncode)

    script_path = Path(output).with_suffix(".py")
    script_path = script_path.parent.parent.parent / "tests" / script_path.name
    cmd2 = [sys.executable, "-m", "ai.generate_test_script", "--input", output, "--output", str(script_path)]
    typer.echo(f"[generate] {' '.join(cmd2)}")
    result2 = subprocess.run(cmd2)
    raise typer.Exit(result2.returncode)
