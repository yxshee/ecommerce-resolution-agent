from __future__ import annotations

from pathlib import Path

import pytest

from ecom_resolution_agent.tools.mock import MockStore
from ecom_resolution_agent.tools.registry import ToolRegistry, build_mock_tool_registry

FIXTURE_PATH = Path("tests/fixtures/mock_data/store_fixture.json")

SAMPLE_REQUESTS: dict[str, dict[str, object]] = {
    "verify_customer": {
        "customer_id": "cus_001",
        "order_id": "ord_001",
        "email": "alice@example.com",
    },
    "get_customer_profile": {"customer_id": "cus_001"},
    "get_order": {"order_id": "ord_001"},
    "get_order_items": {"order_id": "ord_001"},
    "get_fulfillment_status": {"order_id": "ord_001"},
    "get_tracking_events": {"tracking_number": "1ZMOCK1234567890"},
    "get_delivery_proof": {
        "order_id": "ord_001",
        "tracking_number": "1ZMOCK1234567890",
    },
    "create_return": {
        "order_id": "ord_001",
        "item_id": "item_001",
        "reason": "damaged",
        "idempotency_key": "idem_ret_1",
    },
    "create_label": {"return_id": "ret_0001"},
    "schedule_pickup": {
        "return_id": "ret_0001",
        "pickup_date": "2026-02-23",
        "window": "9-12",
    },
    "issue_refund": {
        "order_id": "ord_001",
        "amount_cents": 1200,
        "currency": "USD",
        "reason": "delay",
        "idempotency_key": "idem_ref_1",
    },
    "get_refund_status": {"refund_id": "rfd_missing"},
    "check_stock": {"sku": "SKU-RED-SHOE-8", "quantity": 1},
    "reserve_stock": {
        "sku": "SKU-RED-SHOE-8",
        "quantity": 1,
        "reservation_key": "res_key_1",
    },
    "create_ticket": {
        "ticket_id": "t_001",
        "customer_id": "cus_001",
        "order_id": "ord_001",
        "issue_type": "delivered_not_received",
        "status": "open",
        "customer_message": "Where is my package?",
    },
    "update_ticket": {"ticket_id": "t_001", "status": "in_progress"},
    "add_internal_note": {
        "ticket_id": "t_001",
        "note_markdown": "Reviewed tracking.",
    },
    "get_policy_version": {"issue_type": "delivered_not_received", "country": "US"},
    "get_policy_rules": {"policy_version": "v1_0_0"},
    "search_kb_articles": {"query": "delivered not received", "limit": 3},
}


def build_registry() -> ToolRegistry:
    return build_mock_tool_registry(MockStore.from_file(FIXTURE_PATH))


@pytest.mark.parametrize("tool_name", sorted(SAMPLE_REQUESTS))
def test_mock_tool_contract_for_method(tool_name: str) -> None:
    registry = build_registry()
    spec = registry.get(tool_name)
    request_obj = spec.request_model.model_validate(SAMPLE_REQUESTS[tool_name])
    response_obj = spec.response_model.model_validate(spec.handler(request_obj))

    assert response_obj is not None
    assert spec.name == tool_name
