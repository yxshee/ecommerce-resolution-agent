from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from ecom_resolution_agent.schemas import (
    ActionExecutionRequest,
    AuditEventRecord,
    PolicyOutput,
    ResolutionDecision,
    RiskOutput,
    ToolCallContext,
    ToolCallResult,
    ToolError,
    TriageOutput,
)


def test_triage_output_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        TriageOutput(
            issue_type="order_status",
            missing_info_list=[],
            required_tools_list=["get_order"],
            confidence=0.9,
            unexpected="nope",
        )


def test_policy_and_risk_outputs_validate() -> None:
    policy = PolicyOutput(
        policy_version="v1_0_0",
        allowed_actions=["refund_partial"],
        constraints={"refund_partial": {"max_percent": 50}},
        required_evidence=["tracking_events"],
        approval_required=False,
    )
    risk = RiskOutput(
        risk_score=0.2,
        risk_reasons=["trusted_customer"],
        approval_required=False,
        blocked_actions=[],
    )

    assert policy.policy_version == "v1_0_0"
    assert risk.risk_score == 0.2


def test_resolution_decision_requires_expected_fields() -> None:
    decision = ResolutionDecision(
        selected_action="replacement_reship",
        rationale="Delivery proof exists but risk low and stock available.",
        evidence_refs=["tracking:evt_1", "proof:img_1"],
        customer_message_draft="We can send a replacement.",
        internal_note_draft="Policy and risk checks passed.",
    )
    assert decision.selected_action == "replacement_reship"


def test_tool_call_result_enforces_error_shape() -> None:
    with pytest.raises(ValidationError):
        ToolCallResult[dict](
            tool_name="get_order",
            ok=False,
            data=None,
            error=None,
            latency_ms=5,
            simulated=True,
        )

    result = ToolCallResult[dict](
        tool_name="get_order",
        ok=False,
        data=None,
        error=ToolError(code="timeout", message="timed out", retryable=True),
        latency_ms=5,
        simulated=True,
    )
    assert result.error is not None
    assert result.error.retryable is True


def test_action_and_audit_schemas_validate() -> None:
    _ = ToolCallContext(run_id="run_1", actor_agent="triage", simulation_mode=True)
    action = ActionExecutionRequest(
        run_id="run_1",
        action_type="refund_partial",
        customer_id="cus_1",
        order_id="ord_1",
        amount_cents=1200,
        currency="USD",
        idempotency_key="idem_abc123",
        simulation_mode=True,
    )
    audit = AuditEventRecord(
        event_id="evt_1",
        run_id="run_1",
        timestamp=datetime.now(UTC),
        actor_agent="triage",
        tool_name="get_order",
        tool_input_redacted_json={"order_id": "ord_1"},
        tool_output_redacted_json={"order_id": "ord_1", "email": "[REDACTED]"},
        decision_note=None,
    )

    assert action.amount_cents == 1200
    assert audit.tool_name == "get_order"
