from __future__ import annotations

from pathlib import Path

from ecom_resolution_agent.actions.caps import ActionCapsService
from ecom_resolution_agent.actions.executor import ActionExecutor
from ecom_resolution_agent.agents.actions import DeterministicActionsAgent
from ecom_resolution_agent.approvals import ApprovalService
from ecom_resolution_agent.schemas.actions import ActionExecutionRequest
from ecom_resolution_agent.tools import InMemoryAuditSink, ToolExecutor, build_mock_tool_registry
from ecom_resolution_agent.tools.mock import MockStore

FIXTURE_PATH = Path("tests/fixtures/mock_data/store_fixture.json")


def build_actions_components() -> tuple[
    MockStore, ActionExecutor, DeterministicActionsAgent, InMemoryAuditSink
]:
    store = MockStore.from_file(FIXTURE_PATH)
    registry = build_mock_tool_registry(store)
    audit_sink = InMemoryAuditSink()
    tool_executor = ToolExecutor(registry, audit_sink=audit_sink)
    executor = ActionExecutor(
        tool_executor,
        caps_service=ActionCapsService(),
        approval_service=ApprovalService(),
    )
    agent = DeterministicActionsAgent(executor)
    return store, executor, agent, audit_sink


def test_refund_simulation_succeeds_and_records_refund() -> None:
    store, _executor, agent, audit_sink = build_actions_components()

    result = agent.execute_resolution(
        run_id="run_action_refund_1",
        action_type="refund_partial",
        customer_id="cus_001",
        order_id="ord_001",
        policy_version="v1_0_0",
        amount_cents=1000,
        currency="USD",
        order_total_cents=12999,
        simulation_mode=True,
    )

    assert result.status == "simulated_success"
    assert result.error_code is None
    assert result.simulated is True
    assert store.data["refunds"]
    assert any(event.tool_name == "issue_refund" for event in audit_sink.events)


def test_replacement_reship_simulation_reserves_stock() -> None:
    store, _executor, agent, audit_sink = build_actions_components()
    before_qty = store.data["inventory"]["SKU-RED-SHOE-8"]["available_quantity"]

    result = agent.execute_resolution(
        run_id="run_action_reship_1",
        action_type="replacement_reship",
        customer_id="cus_001",
        order_id="ord_001",
        policy_version="v1_0_0",
        item_id="item_001",
        item_sku="SKU-RED-SHOE-8",
        simulation_mode=True,
    )

    after_qty = store.data["inventory"]["SKU-RED-SHOE-8"]["available_quantity"]
    assert result.status == "simulated_reship_reserved"
    assert result.error_code is None
    assert after_qty == before_qty - 1
    called_tools = [event.tool_name for event in audit_sink.events]
    assert "check_stock" in called_tools
    assert "reserve_stock" in called_tools


def test_duplicate_idempotency_replays_without_second_tool_execution() -> None:
    store, _executor, agent, audit_sink = build_actions_components()

    first = agent.execute_resolution(
        run_id="run_action_dupe_1",
        action_type="refund_partial",
        customer_id="cus_001",
        order_id="ord_001",
        policy_version="v1_0_0",
        amount_cents=500,
        currency="USD",
        order_total_cents=12999,
        simulation_mode=True,
    )
    second = agent.execute_resolution(
        run_id="run_action_dupe_1",
        action_type="refund_partial",
        customer_id="cus_001",
        order_id="ord_001",
        policy_version="v1_0_0",
        amount_cents=500,
        currency="USD",
        order_total_cents=12999,
        simulation_mode=True,
    )

    issue_refund_calls = [event for event in audit_sink.events if event.tool_name == "issue_refund"]
    assert first.status == "simulated_success"
    assert second.status == "duplicate_replay"
    assert second.external_reference == first.external_reference
    assert len(issue_refund_calls) == 1
    assert len(store.data["refunds"]) == 1


def test_refund_timeout_reconciles_via_get_refund_status() -> None:
    store, executor, _agent, audit_sink = build_actions_components()
    request = ActionExecutionRequest(
        run_id="run_action_timeout_1",
        action_type="refund_partial",
        customer_id="cus_001",
        order_id="ord_001",
        amount_cents=750,
        currency="USD",
        idempotency_key="idem_timeout_reconcile_case",
        simulation_mode=True,
    )

    result = executor.execute(request, order_total_cents=12999)

    called_tools = [event.tool_name for event in audit_sink.events]
    assert result.status == "simulated_success"
    assert result.error_code is None
    assert result.external_reference is not None
    assert "issue_refund" in called_tools
    assert "get_refund_status" in called_tools
    assert len(store.data["refunds"]) == 1
