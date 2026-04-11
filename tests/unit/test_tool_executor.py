from __future__ import annotations

from pathlib import Path

from ecom_resolution_agent.schemas.tool_envelopes import ToolCallContext
from ecom_resolution_agent.tools.executor import InMemoryAuditSink, ToolExecutor
from ecom_resolution_agent.tools.mock import MockStore
from ecom_resolution_agent.tools.registry import build_mock_tool_registry

FIXTURE_PATH = Path("tests/fixtures/mock_data/store_fixture.json")


def build_executor() -> tuple[ToolExecutor, InMemoryAuditSink]:
    store = MockStore.from_file(FIXTURE_PATH)
    registry = build_mock_tool_registry(store)
    sink = InMemoryAuditSink()
    return ToolExecutor(registry, audit_sink=sink), sink


def test_capability_denial_for_triage_action_tool() -> None:
    executor, sink = build_executor()
    context = ToolCallContext(run_id="run_1", actor_agent="triage", simulation_mode=True)

    result = executor.invoke(
        "issue_refund",
        {
            "order_id": "ord_001",
            "amount_cents": 500,
            "currency": "USD",
            "reason": "missing item",
            "idempotency_key": "idem_test_1",
        },
        context=context,
    )

    assert result.ok is False
    assert result.error is not None
    assert result.error.code == "permission_denied"
    assert len(sink.events) == 1
    assert sink.events[0].decision_note == "permission_denied"


def test_audit_redaction_for_tool_calls() -> None:
    executor, sink = build_executor()
    context = ToolCallContext(run_id="run_2", actor_agent="triage", simulation_mode=True)

    result = executor.invoke(
        "verify_customer",
        {
            "customer_id": "cus_001",
            "order_id": "ord_001",
            "email": "alice@example.com",
        },
        context=context,
    )

    assert result.ok is True
    event = sink.events[-1]
    assert event.tool_input_redacted_json is not None
    assert event.tool_output_redacted_json is not None
    assert event.tool_input_redacted_json["email"] == "[REDACTED]"


def test_real_actions_disabled_when_not_simulation() -> None:
    executor, _ = build_executor()
    context = ToolCallContext(run_id="run_3", actor_agent="actions", simulation_mode=False)

    result = executor.invoke(
        "issue_refund",
        {
            "order_id": "ord_001",
            "amount_cents": 1000,
            "currency": "USD",
            "reason": "test",
            "idempotency_key": "idem_test_2",
        },
        context=context,
    )

    assert result.ok is False
    assert result.error is not None
    assert result.error.code == "real_actions_disabled"
