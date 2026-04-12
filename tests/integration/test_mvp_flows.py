from __future__ import annotations

from pathlib import Path

import pytest

from ecom_resolution_agent.actions.caps import ActionCapsService
from ecom_resolution_agent.agents import DeterministicRiskAgent, DeterministicTriageAgent
from ecom_resolution_agent.approvals import ApprovalService
from ecom_resolution_agent.orchestration import CaseState, EcommerceOrchestrator
from ecom_resolution_agent.orchestration.nodes.common import OrchestrationDeps
from ecom_resolution_agent.policy import PolicyService
from ecom_resolution_agent.tools import ToolExecutor, build_mock_tool_registry
from ecom_resolution_agent.tools.mock import MockStore

FIXTURE_PATH = Path("tests/fixtures/mock_data/store_fixture.json")


def build_orchestrator() -> EcommerceOrchestrator:
    store = MockStore.from_file(FIXTURE_PATH)
    registry = build_mock_tool_registry(store)
    deps = OrchestrationDeps(
        tool_executor=ToolExecutor(registry),
        policy_service=PolicyService(),
        triage_agent=DeterministicTriageAgent(),
        risk_agent=DeterministicRiskAgent(),
        approval_service=ApprovalService(),
        caps_service=ActionCapsService(),
    )
    return EcommerceOrchestrator(deps)


@pytest.mark.parametrize(
    ("name", "ticket", "expected_issue_type", "expected_allowed_action"),
    [
        (
            "order_status",
            {
                "ticket_id": "t_mvp_1",
                "customer_id": "cus_001",
                "order_id": "ord_001",
                "customer_email": "alice@example.com",
                "customer_message": "Where is my order?",
            },
            "order_status",
            "escalate_human",
        ),
        (
            "cancel_pre_shipment",
            {
                "ticket_id": "t_mvp_2",
                "customer_id": "cus_001",
                "order_id": "ord_002",
                "customer_email": "alice@example.com",
                "customer_message": "Please cancel this order before it ships",
            },
            "cancel_order",
            "cancel_order",
        ),
        (
            "return_initiation",
            {
                "ticket_id": "t_mvp_3",
                "customer_id": "cus_001",
                "order_id": "ord_003",
                "item_id": "item_003",
                "customer_email": "alice@example.com",
                "customer_message": "I want to return this shirt",
            },
            "return_initiation",
            "return_initiation",
        ),
    ],
)
def test_phase4_mvp_flows(
    name: str,
    ticket: dict[str, str],
    expected_issue_type: str,
    expected_allowed_action: str,
) -> None:
    orchestrator = build_orchestrator()
    state = CaseState(run_id=f"run_{name}", ticket=ticket, simulation_mode=True)

    result = orchestrator.run(state)

    assert result.status == "risk_assessed"
    assert result.issue_type == expected_issue_type
    assert result.policy_output is not None
    assert result.risk_output is not None
    assert expected_allowed_action in result.policy_output.allowed_actions
    assert result.verification_passed is True
    assert "get_order" in result.tool_results
    assert "verify_customer" in result.tool_results
