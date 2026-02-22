from __future__ import annotations

import json
from pathlib import Path

import typer

from ecom_resolution_agent.config import get_settings

app = typer.Typer(
    name="ecom-resolver",
    help="Ecommerce Resolution Agent CLI (simulation-first, production-oriented scaffold).",
    no_args_is_help=True,
)


@app.command("run-case")
def run_case(
    ticket_file: Path = typer.Option(
        ...,
        exists=True,
        readable=True,
        help="Path to ticket JSON file.",
    ),
    simulation: bool = typer.Option(
        True,
        "--simulation/--no-simulation",
        help="Simulation mode.",
    ),
) -> None:
    """Run the full resolution pipeline for a single ticket (placeholder in Phase 0)."""
    typer.echo(
        json.dumps(
            {
                "status": "not_implemented",
                "command": "run-case",
                "ticket_file": str(ticket_file),
                "simulation": simulation,
                "phase": 0,
            },
            indent=2,
        )
    )


@app.command("run-step")
def run_step(
    state: str = typer.Option(..., help="Orchestration state to run."),
    input_file: Path = typer.Option(
        ...,
        "--input",
        exists=True,
        readable=True,
        help="Input JSON file.",
    ),
) -> None:
    """Run a single orchestration step (placeholder in Phase 0)."""
    typer.echo(
        json.dumps(
            {
                "status": "not_implemented",
                "command": "run-step",
                "state": state,
                "input": str(input_file),
                "phase": 0,
            },
            indent=2,
        )
    )


@app.command("eval")
def eval_cmd(
    dataset: Path = typer.Option(
        ...,
        exists=True,
        readable=True,
        help="Scenario dataset path.",
    ),
    output_dir: Path = typer.Option(..., help="Evaluation output directory."),
) -> None:
    """Run the offline evaluation harness (placeholder in Phase 0)."""
    typer.echo(
        json.dumps(
            {
                "status": "not_implemented",
                "command": "eval",
                "dataset": str(dataset),
                "output_dir": str(output_dir),
                "phase": 0,
            },
            indent=2,
        )
    )


@app.command("demo")
def demo(
    scenario: str = typer.Option("delivered_not_received", help="Demo scenario name."),
) -> None:
    """Run a local demo scenario (placeholder in Phase 0)."""
    typer.echo(
        json.dumps(
            {
                "status": "not_implemented",
                "command": "demo",
                "scenario": scenario,
                "phase": 0,
            },
            indent=2,
        )
    )


@app.command("api")
def serve_api(
    host: str = typer.Option(None, help="Host override."),
    port: int = typer.Option(None, help="Port override."),
) -> None:
    """Serve the FastAPI app."""
    settings = get_settings()

    resolved_host = host or settings.api_host
    resolved_port = port or settings.api_port

    import uvicorn

    uvicorn.run(
        "ecom_resolution_agent.api.app:app",
        host=resolved_host,
        port=resolved_port,
        reload=False,
    )


if __name__ == "__main__":
    app()
