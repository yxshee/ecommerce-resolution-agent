from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from ecom_resolution_agent.actions.caps import ActionCapsService
from ecom_resolution_agent.actions.executor import ActionExecutor
from ecom_resolution_agent.agents.actions import DeterministicActionsAgent
from ecom_resolution_agent.approvals import ApprovalService
from ecom_resolution_agent.audit import (
    AuditInvariantViolation,
    RunArtifactWriter,
    assert_action_success_claim_backed_by_audit,
)
from ecom_resolution_agent.reporting import DeterministicReportAgent
from ecom_resolution_agent.schemas.actions import ActionExecutionResult
from ecom_resolution_agent.schemas.agent_outputs import ResolutionDecision
from ecom_resolution_agent.schemas.audit import AuditEventRecord
from ecom_resolution_agent.tools import InMemoryAuditSink, ToolExecutor, build_mock_tool_registry
from ecom_resolution_agent.tools.mock import MockStore

FIXTURE_PATH = Path("tests/fixtures/mock_data/store_fixture.json")


def _build_components() -> tuple[
    MockStore, InMemoryAuditSink, DeterministicActionsAgent, ToolExecutor
]:
    store = MockStore.from_file(FIXTURE_PATH)
    registry = build_mock_tool_registry(store)
    audit_sink = InMemoryAuditSink()
    tool_executor = ToolExecutor(registry, audit_sink=audit_sink)
    action_executor = ActionExecutor(
        tool_executor,
        caps_service=ActionCapsService(),
        approval_service=ApprovalService(),
    )
    return store, audit_sink, DeterministicActionsAgent(action_executor), tool_executor


def _seed_refund_action(
    *,
    agent: DeterministicActionsAgent,
) -> ActionExecutionResult:
    return agent.execute_resolution(
        run_id="run_report_phase8_1",
        action_type="refund_partial",
        customer_id="cus_001",
        order_id="ord_001",
        policy_version="v1_0_0",
        amount_cents=1200,
        currency="USD",
        order_total_cents=12999,
        simulation_mode=True,
    )


def _decision_with_pii_internal_note() -> ResolutionDecision:
    return ResolutionDecision(
        selected_action="refund_partial",
        rationale=(
            "Package was marked delivered but customer dispute is low risk and "
            "policy allows refund."
        ),
        evidence_refs=["order:ord_001", "tracking:trk_001", "policy:v1_0_0"],
        customer_message_draft=(
            "We have issued a refund for the disputed item amount. "
            "Please allow 3-5 business days for posting."
        ),
        internal_note_draft=(
            "Customer follow-up requested at alice@example.com or 415-555-1212 after refund posts."
        ),
    )


def test_report_markdown_generation_is_deterministic_and_structured() -> None:
    store, audit_sink, actions_agent, tool_executor = _build_components()
    action_result = _seed_refund_action(agent=actions_agent)
    report_agent = DeterministicReportAgent(tool_executor)

    ticket = {
        "ticket_id": "tkt_1001",
        "customer_id": "cus_001",
        "order_id": "ord_001",
        "issue_type": "delivered_not_received",
        "status": "open",
        "customer_message": "My package says delivered but I did not receive it.",
    }
    report_output = report_agent.build_report_output(
        ticket=ticket,
        decision=_decision_with_pii_internal_note(),
        action_result=action_result,
        facts={"refund_amount_cents": 1200, "currency": "USD"},
        audit_events=audit_sink.events,
        audit_bundle_refs=["artifacts/runs/run_report_phase8_1"],
        run_id="run_report_phase8_1",
    )

    assert report_output.customer_message_markdown.startswith("# Resolution Update")
    assert "`refund_partial`" in report_output.customer_message_markdown
    assert "3-5 business days" in report_output.customer_message_markdown
    assert report_output.internal_summary_markdown.startswith("# Internal Resolution Summary")
    assert "## Audit Bundle References" in report_output.internal_summary_markdown
    assert "artifacts/runs/run_report_phase8_1" in report_output.internal_summary_markdown
    assert report_output.audit_bundle_refs == ["artifacts/runs/run_report_phase8_1"]


def test_report_agent_updates_ticket_and_audit_redacts_ticket_tool_calls() -> None:
    store, audit_sink, actions_agent, tool_executor = _build_components()
    action_result = _seed_refund_action(agent=actions_agent)
    report_agent = DeterministicReportAgent(tool_executor)

    ticket = {
        "ticket_id": "tkt_2002",
        "customer_id": "cus_001",
        "order_id": "ord_001",
        "issue_type": "delivered_not_received",
        "status": "open",
        "customer_message": "Please help, I still need this order.",
    }
    publication = report_agent.generate_and_publish(
        run_id="run_report_phase8_1",
        ticket=ticket,
        decision=_decision_with_pii_internal_note(),
        action_result=action_result,
        facts={"customer_email": "alice@example.com", "callback_phone": "415-555-1212"},
        audit_events=audit_sink.events,
        audit_bundle_refs=["artifacts/runs/run_report_phase8_1"],
        simulation_mode=True,
    )

    assert publication.report_output.customer_message_markdown
    assert store.data["tickets"]["tkt_2002"]["status"] == "resolved"
    notes = store.data["ticket_notes"]["tkt_2002"]
    assert len(notes) == 1
    assert "alice@example.com" in notes[0]["note_markdown"]

    report_events = [e for e in audit_sink.events if e.actor_agent == "report"]
    tool_names = [e.tool_name for e in report_events]
    assert tool_names == ["add_internal_note", "update_ticket"]

    add_note_event = report_events[0]
    redacted_input = add_note_event.tool_input_redacted_json or {}
    note_markdown = str(redacted_input.get("note_markdown", ""))
    assert "[REDACTED]" in note_markdown
    assert "alice@example.com" not in note_markdown
    assert "415-555-1212" not in note_markdown


def test_run_artifact_writer_generates_audit_bundle_with_optional_evaluation_results(
    tmp_path: Path,
) -> None:
    store, audit_sink, actions_agent, tool_executor = _build_components()
    action_result = _seed_refund_action(agent=actions_agent)
    report_agent = DeterministicReportAgent(tool_executor)

    ticket = {
        "ticket_id": "tkt_3003",
        "customer_id": "cus_001",
        "order_id": "ord_001",
        "issue_type": "delivered_not_received",
        "status": "open",
        "customer_message": "Refund requested.",
    }
    publication = report_agent.generate_and_publish(
        run_id="run_report_phase8_1",
        ticket=ticket,
        decision=_decision_with_pii_internal_note(),
        action_result=action_result,
        facts={"risk_score": 0.2},
        audit_events=audit_sink.events,
        audit_bundle_refs=["local://bundle/run_report_phase8_1"],
        simulation_mode=True,
    )

    writer = RunArtifactWriter(base_dir=tmp_path / "artifacts" / "runs")
    run_dir = writer.write_bundle(
        run_id="run_report_phase8_1",
        run_config={"run_id": "run_report_phase8_1", "simulation_mode": True},
        audit_events=audit_sink.events,
        decision={
            "selected_action": "refund_partial",
            "action_result": action_result.model_dump(mode="json"),
        },
        report_output=publication.report_output,
        evaluation_results={"score": 1.0, "checks": ["report_markdown", "audit_bundle"]},
    )

    assert run_dir == tmp_path / "artifacts" / "runs" / "run_report_phase8_1"
    assert (run_dir / "run_config.json").exists()
    assert (run_dir / "redacted_audit.jsonl").exists()
    assert (run_dir / "decision.json").exists()
    assert (run_dir / "report.md").exists()
    assert (run_dir / "evaluation_results.json").exists()

    run_config = json.loads((run_dir / "run_config.json").read_text())
    assert run_config["simulation_mode"] is True

    audit_lines = (run_dir / "redacted_audit.jsonl").read_text().strip().splitlines()
    assert len(audit_lines) == len(audit_sink.events)
    first_event = json.loads(audit_lines[0])
    assert "tool_input_redacted_json" in first_event

    report_md = (run_dir / "report.md").read_text()
    assert "# Customer Message" in report_md
    assert "# Internal Summary" in report_md
    assert "local://bundle/run_report_phase8_1" in report_md

    evaluation = json.loads((run_dir / "evaluation_results.json").read_text())
    assert evaluation["score"] == 1.0


def test_invariant_rejects_success_claim_without_matching_action_audit_event() -> None:
    action_result = ActionExecutionResult(
        action_id="act_1234",
        run_id="run_missing_audit",
        action_type="refund_partial",
        status="simulated_success",
        external_reference="rfd_9999",
        simulated=True,
        error_code=None,
    )
    unrelated_event = AuditEventRecord(
        event_id="evt_1",
        run_id="run_missing_audit",
        timestamp=datetime.now(UTC),
        actor_agent="report",
        tool_name="update_ticket",
        tool_input_redacted_json={"ticket_id": "tkt_9", "status": "resolved"},
        tool_output_redacted_json={"ticket_id": "tkt_9", "status": "resolved"},
        decision_note="success",
    )

    with pytest.raises(AuditInvariantViolation):
        assert_action_success_claim_backed_by_audit(
            action_result=action_result,
            audit_events=[unrelated_event],
        )


@pytest.mark.parametrize("run_id", ["", ".", "..", "../escaped", "a/b", "a\\b"])
def test_artifact_writer_rejects_run_ids_that_are_not_one_name(tmp_path: Path, run_id: str) -> None:
    writer = RunArtifactWriter(base_dir=tmp_path / "runs")
    with pytest.raises(ValueError, match="invalid run_id"):
        writer.run_dir(run_id)
