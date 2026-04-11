from __future__ import annotations

from pathlib import Path

from ecom_resolution_agent.schemas.tool_envelopes import ToolCallContext
from ecom_resolution_agent.tools.executor import InMemoryAuditSink, ToolExecutor
from ecom_resolution_agent.tools.mock import MockStore
from ecom_resolution_agent.tools.registry import build_mock_tool_registry

FIXTURE_PATH = Path("tests/fixtures/mock_data/store_fixture.json")


def test_offline_fact_gathering_with_mocks() -> None:
    store = MockStore.from_file(FIXTURE_PATH)
    registry = build_mock_tool_registry(store)
    audit_sink = InMemoryAuditSink()
    executor = ToolExecutor(registry, audit_sink=audit_sink)
    ctx = ToolCallContext(run_id="run_fact_1", actor_agent="triage", simulation_mode=True)

    verify = executor.invoke(
        "verify_customer",
        {"customer_id": "cus_001", "order_id": "ord_001", "email": "alice@example.com"},
        context=ctx,
    )
    assert verify.ok is True
    assert verify.data is not None
    assert verify.data["verified"] is True

    order = executor.invoke("get_order", {"order_id": "ord_001"}, context=ctx)
    items = executor.invoke("get_order_items", {"order_id": "ord_001"}, context=ctx)
    fulfill = executor.invoke("get_fulfillment_status", {"order_id": "ord_001"}, context=ctx)
    track = executor.invoke(
        "get_tracking_events",
        {"tracking_number": "1ZMOCK1234567890"},
        context=ctx,
    )
    proof = executor.invoke(
        "get_delivery_proof",
        {"order_id": "ord_001", "tracking_number": "1ZMOCK1234567890"},
        context=ctx,
    )
    policy_version = executor.invoke(
        "get_policy_version",
        {"issue_type": "delivered_not_received", "country": "US"},
        context=ctx,
    )
    policy_rules = executor.invoke(
        "get_policy_rules",
        {"policy_version": "v1_0_0"},
        context=ctx,
    )
    kb = executor.invoke(
        "search_kb_articles",
        {"query": "delivered not received", "limit": 2},
        context=ctx,
    )

    for result in [order, items, fulfill, track, proof, policy_version, policy_rules, kb]:
        assert result.ok is True
        assert result.data is not None

    assert fulfill.data["delivered"] is True
    assert len(track.data["events"]) >= 1
    assert proof.data["available"] is True
    assert policy_version.data["policy_version"] == "v1_0_0"
    assert len(kb.data["results"]) >= 1

    assert len(audit_sink.events) == 9
    assert all(event.run_id == "run_fact_1" for event in audit_sink.events)
