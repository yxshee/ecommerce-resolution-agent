from __future__ import annotations

from pathlib import Path

from ecom_resolution_agent.actions.caps import ActionCapsService
from ecom_resolution_agent.agents import DeterministicRiskAgent, DeterministicTriageAgent
from ecom_resolution_agent.approvals import ApprovalService
from ecom_resolution_agent.orchestration import CaseState, EcommerceOrchestrator
from ecom_resolution_agent.orchestration.nodes.common import OrchestrationDeps
from ecom_resolution_agent.policy import PolicyService
from ecom_resolution_agent.tools import ToolExecutor, build_mock_tool_registry
from ecom_resolution_agent.tools.mock import MockStore

FIXTURE_PATH = Path("tests/fixtures/mock_data/store_fixture.json")


def build_orchestrator(store: MockStore) -> EcommerceOrchestrator:
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


def test_approval_required_flow_creates_approval_task() -> None:
    store = MockStore.from_file(FIXTURE_PATH)
    store.data["orders"]["ord_001"]["total"]["amount_cents"] = 80000

    orchestrator = build_orchestrator(store)
    state = CaseState(
        run_id="run_approval_1",
        ticket={
            "ticket_id": "t_approval_1",
            "customer_id": "cus_001",
            "order_id": "ord_001",
            "customer_email": "alice@example.com",
            "issue_type": "delivered_not_received",
            "customer_message": "Tracking says delivered but I never got it",
        },
        simulation_mode=True,
    )

    result = orchestrator.run(state)

    assert result.current_state == "risk_assessment"
    assert result.status == "approval_required"
    assert result.risk_output is not None
    assert result.risk_output.approval_required is True
    assert result.approval_task_id is not None
    assert result.approval_token is not None


def test_blocked_flow_when_high_risk_blocks_all_auto_actions() -> None:
    store = MockStore.from_file(FIXTURE_PATH)
    store.data["customers"]["cus_001"]["risk_flags"] = ["chargeback_history"]

    orchestrator = build_orchestrator(store)
    state = CaseState(
        run_id="run_blocked_1",
        ticket={
            "ticket_id": "t_blocked_1",
            "customer_id": "cus_001",
            "order_id": "ord_001",
            "customer_email": "alice@example.com",
            "issue_type": "delivered_not_received",
            "customer_message": "Package marked delivered but not received",
        },
        simulation_mode=True,
    )

    result = orchestrator.run(state)

    assert result.current_state == "risk_assessment"
    assert result.status == "blocked_high_risk"
    assert result.risk_output is not None
    assert "refund_full" in result.risk_output.blocked_actions
    assert result.approval_task_id is None
