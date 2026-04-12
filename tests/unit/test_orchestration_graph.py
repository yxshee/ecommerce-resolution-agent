from __future__ import annotations

from pathlib import Path

from ecom_resolution_agent.actions.caps import ActionCapsService
from ecom_resolution_agent.agents import DeterministicRiskAgent, DeterministicTriageAgent
from ecom_resolution_agent.approvals import ApprovalService
from ecom_resolution_agent.orchestration import CaseState, EcommerceOrchestrator
from ecom_resolution_agent.orchestration.nodes.common import OrchestrationDeps
from ecom_resolution_agent.orchestration.state import END_ROUTE
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


def test_identity_fail_stops_and_requests_verification() -> None:
    orchestrator = build_orchestrator()
    state = CaseState(
        run_id="run_fail_1",
        ticket={
            "ticket_id": "t_fail_1",
            "customer_id": "cus_001",
            "order_id": "ord_001",
            "customer_email": "wrong@example.com",
            "customer_message": "Where is my order?",
        },
        simulation_mode=True,
    )

    result = orchestrator.run(state)

    assert result.status == "needs_verification"
    assert result.requested_verification is True
    assert result.next_state == END_ROUTE
    assert result.verification_passed is False
    assert result.current_state == "verify_identity"


def test_happy_path_reaches_policy_lookup() -> None:
    orchestrator = build_orchestrator()
    state = CaseState(
        run_id="run_happy_1",
        ticket={
            "ticket_id": "t_happy_1",
            "customer_id": "cus_001",
            "order_id": "ord_001",
            "customer_email": "alice@example.com",
            "customer_message": "What is the status of my order?",
        },
        simulation_mode=True,
    )

    result = orchestrator.run(state)

    assert result.status == "risk_assessed"
    assert result.issue_type == "order_status"
    assert result.policy_output is not None
    assert result.risk_output is not None
    assert result.policy_version == "v1_0_0"
    assert result.current_state == "risk_assessment"
