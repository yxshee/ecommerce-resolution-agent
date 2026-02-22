from __future__ import annotations

import json
import shutil
from pathlib import Path

from typer.testing import CliRunner

from ecom_resolution_agent.cli import app

runner = CliRunner()


def test_cli_run_case_runs_pipeline_and_writes_artifacts(tmp_path: Path) -> None:
    ticket_path = tmp_path / "ticket.json"
    ticket_path.write_text(
        json.dumps(
            {
                "ticket_id": "cli_case_001",
                "customer_id": "cus_001",
                "order_id": "ord_001",
                "customer_email": "alice@example.com",
                "issue_type": "delivered_not_received",
                "customer_message": "Tracking says delivered but I did not receive it.",
            }
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        ["run-case", "--ticket-file", str(ticket_path), "--simulation"],
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "completed"
    report_path = Path(payload["report_path"])
    assert report_path.exists()
    assert "# Customer Message" in report_path.read_text(encoding="utf-8")


def test_cli_run_step_executes_intake_step() -> None:
    input_path = Path("artifacts") / "tmp_run_step_input.json"
    input_path.parent.mkdir(parents=True, exist_ok=True)
    input_path.write_text(
        json.dumps(
            {
                "run_id": "run_step_test",
                "ticket": {
                    "ticket_id": "step_001",
                    "customer_id": "cus_001",
                    "order_id": "ord_001",
                    "customer_message": "Where is my order?",
                },
                "simulation_mode": True,
            }
        ),
        encoding="utf-8",
    )
    try:
        result = runner.invoke(
            app,
            ["run-step", "--state", "intake", "--input", str(input_path)],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        payload = json.loads(result.stdout)
        assert payload["state"] == "intake"
        assert payload["output"]["current_state"] == "intake"
        assert payload["output"]["next_state"] == "verify_identity"
    finally:
        input_path.unlink(missing_ok=True)


def test_cli_demo_delivered_not_received_prints_report_path_and_artifacts() -> None:
    artifact_dir = Path("artifacts/runs/demo_delivered_not_received")
    if artifact_dir.exists():
        shutil.rmtree(artifact_dir)

    result = runner.invoke(
        app,
        ["demo", "--scenario", "delivered_not_received"],
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "completed"
    assert payload["scenario"] == "delivered_not_received"
    assert payload["run"]["selected_action"] in {"replacement_reship", "escalate_human"}

    report_path = Path(payload["report_path"])
    assert report_path.exists()
    run_dir = Path(payload["artifact_dir"])
    assert (run_dir / "run_config.json").exists()
    assert (run_dir / "redacted_audit.jsonl").exists()
    assert (run_dir / "decision.json").exists()
    assert (run_dir / "report.md").exists()

    report_md = (run_dir / "report.md").read_text(encoding="utf-8")
    assert "# Customer Message" in report_md
    assert "# Internal Summary" in report_md
    assert "artifacts/runs/demo_delivered_not_received" in report_md
