from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import typer

from ecom_resolution_agent.actions.caps import ActionCapsService
from ecom_resolution_agent.agents import DeterministicRiskAgent, DeterministicTriageAgent
from ecom_resolution_agent.approvals import ApprovalService
from ecom_resolution_agent.config import get_settings
from ecom_resolution_agent.eval import (
    EvaluationHarness,
    EvaluationHarnessConfig,
    enforce_regression_thresholds,
    load_eval_scenarios,
    load_eval_thresholds,
    score_observations,
)
from ecom_resolution_agent.orchestration.nodes import (
    run_classify_issue,
    run_gather_facts,
    run_intake,
    run_policy_lookup,
    run_risk_assessment,
    run_verify_identity,
)
from ecom_resolution_agent.orchestration.nodes.common import OrchestrationDeps
from ecom_resolution_agent.orchestration.pipeline import build_simulation_pipeline
from ecom_resolution_agent.policy import PolicyService
from ecom_resolution_agent.tools import ToolExecutor, build_mock_tool_registry
from ecom_resolution_agent.tools.mock import MockStore

app = typer.Typer(
    name="ecom-resolver",
    help="Ecommerce Resolution Agent CLI (simulation-first, production-oriented scaffold).",
    no_args_is_help=True,
)

DEFAULT_DATASET_PATH = Path("datasets/scenarios_v1.jsonl")
DEFAULT_THRESHOLDS_PATH = Path("datasets/eval_thresholds.json")


def _print_json(payload: dict[str, Any]) -> None:
    typer.echo(json.dumps(payload, indent=2))


def _demo_ticket(scenario: str) -> dict[str, Any]:
    if scenario != "delivered_not_received":
        raise typer.BadParameter("Only `delivered_not_received` is supported in the local demo.")
    return {
        "ticket_id": "demo_dnr_001",
        "customer_id": "cus_001",
        "order_id": "ord_001",
        "customer_email": "alice@example.com",
        "issue_type": "delivered_not_received",
        "customer_message": "Tracking says delivered but I did not receive the package.",
    }


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
    """Run the full resolution pipeline for a single ticket."""
    ticket = json.loads(ticket_file.read_text(encoding="utf-8"))
    if not isinstance(ticket, dict):
        raise typer.BadParameter("ticket file must contain a JSON object")

    pipeline = build_simulation_pipeline()
    result = pipeline.run_case(ticket=ticket, simulation_mode=simulation)
    report_path = result.artifact_dir / "report.md"
    _print_json(
        {
            "status": "completed",
            "run": result.summary(),
            "artifact_dir": str(result.artifact_dir),
            "report_path": str(report_path),
        }
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
    """Run a single orchestration step (graph states only) or simulate later steps via full run."""
    payload = json.loads(input_file.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise typer.BadParameter("input file must contain a JSON object")

    step_handlers = {
        "intake": _run_step_intake,
        "verify_identity": _run_step_with_deps(run_verify_identity),
        "gather_facts": _run_step_with_deps(run_gather_facts),
        "classify_issue": _run_step_with_deps(run_classify_issue),
        "policy_lookup": _run_step_with_deps(run_policy_lookup),
        "risk_assessment": _run_step_with_deps(run_risk_assessment),
    }
    if state in step_handlers:
        output = step_handlers[state](payload)
        _print_json({"state": state, "output": output})
        return

    if state in {
        "propose_resolution",
        "verify_resolution",
        "execute_or_escalate",
        "finalize_report",
        "persist_audit",
    }:
        ticket = payload.get("ticket")
        if not isinstance(ticket, dict):
            raise typer.BadParameter(
                f"`run-step --state {state}` expects an input JSON with a `ticket` object"
            )
        pipeline = build_simulation_pipeline()
        result = pipeline.run_case(
            ticket=ticket,
            run_id=str(payload.get("run_id") or "run_step_demo"),
        )
        _print_json(
            {
                "state": state,
                "status": "simulated_via_full_pipeline",
                "run": result.summary(),
                "decision": result.decision.model_dump(mode="json"),
                "qa_result": result.qa_result.model_dump(mode="json"),
                "action_result": (
                    result.action_result.model_dump(mode="json")
                    if result.action_result is not None
                    else None
                ),
                "artifact_dir": str(result.artifact_dir),
            }
        )
        return

    raise typer.BadParameter(f"Unsupported state: {state}")


@app.command("eval")
def eval_cmd(
    dataset: Path = typer.Option(
        DEFAULT_DATASET_PATH,
        exists=True,
        readable=True,
        help="Scenario dataset path.",
    ),
    output_dir: Path = typer.Option(..., help="Evaluation output directory."),
    thresholds: Path = typer.Option(
        DEFAULT_THRESHOLDS_PATH,
        exists=True,
        readable=True,
        help="Thresholds JSON path.",
    ),
    limit: int | None = typer.Option(
        None,
        min=1,
        help="Optional scenario limit for quick local iteration.",
    ),
    write_artifacts: bool = typer.Option(
        False,
        help="Write per-run eval artifacts for each scenario.",
    ),
) -> None:
    """Run the offline evaluation harness and write a summary JSON."""
    scenarios = load_eval_scenarios(dataset)
    if limit is not None:
        scenarios = scenarios[:limit]
    harness = EvaluationHarness(
        EvaluationHarnessConfig(
            artifact_base_dir=(output_dir / "runs") if write_artifacts else None
        )
    )
    observations = [harness.run_scenario(scenario) for scenario in scenarios]
    summary = score_observations(observations)
    threshold_model = load_eval_thresholds(thresholds)
    failures = enforce_regression_thresholds(summary=summary, thresholds=threshold_model)

    output_dir.mkdir(parents=True, exist_ok=True)
    results_path = output_dir / "evaluation_results.json"
    payload = summary.to_json()
    payload["gate"] = {"passed": not failures, "failures": failures}
    payload["dataset"] = str(dataset)
    payload["thresholds"] = str(thresholds)
    results_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    _print_json(
        {
            "status": "completed" if not failures else "failed_gate",
            "scenario_count": summary.scenario_count,
            "metrics": summary.metrics,
            "gate": payload["gate"],
            "results_path": str(results_path),
        }
    )


@app.command("demo")
def demo(
    scenario: str = typer.Option("delivered_not_received", help="Demo scenario name."),
) -> None:
    """Run a local delivered-not-received demo in simulation mode."""
    ticket = _demo_ticket(scenario)
    pipeline = build_simulation_pipeline()
    result = pipeline.run_case(ticket=ticket, run_id=f"demo_{scenario}")
    report_path = result.artifact_dir / "report.md"
    _print_json(
        {
            "status": "completed",
            "scenario": scenario,
            "run": result.summary(),
            "report_path": str(report_path),
            "artifact_dir": str(result.artifact_dir),
        }
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


def _build_step_deps() -> OrchestrationDeps:
    store = MockStore.from_file("tests/fixtures/mock_data/store_fixture.json")
    registry = build_mock_tool_registry(store)
    return OrchestrationDeps(
        tool_executor=ToolExecutor(registry),
        policy_service=PolicyService(),
        triage_agent=DeterministicTriageAgent(),
        risk_agent=DeterministicRiskAgent(),
        approval_service=ApprovalService(),
        caps_service=ActionCapsService(),
    )


def _run_step_intake(payload: dict[str, Any]) -> dict[str, Any]:
    return run_intake(payload)


def _run_step_with_deps(
    fn: Any,
) -> Any:
    def _runner(payload: dict[str, Any]) -> dict[str, Any]:
        deps = _build_step_deps()
        if "run_id" not in payload:
            payload = {**payload, "run_id": "run_step_local"}
        if "ticket" not in payload:
            payload = {
                **payload,
                "ticket": {
                    "ticket_id": "run_step_ticket",
                    "customer_id": "cus_001",
                    "order_id": "ord_001",
                    "customer_email": "alice@example.com",
                    "customer_message": "Where is my order?",
                },
            }
        return fn(payload, deps)

    return _runner


if __name__ == "__main__":
    app()
