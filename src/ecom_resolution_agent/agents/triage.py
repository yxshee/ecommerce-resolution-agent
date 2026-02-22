from __future__ import annotations

from typing import Any

from ecom_resolution_agent.schemas.agent_outputs import TriageOutput

ISSUE_TOOL_MAP: dict[str, list[str]] = {
    "order_status": ["get_order", "get_fulfillment_status"],
    "cancel_order": ["get_order", "get_fulfillment_status"],
    "return_initiation": ["get_order", "get_order_items"],
    "delivered_not_received": [
        "get_order",
        "get_fulfillment_status",
        "get_tracking_events",
        "get_delivery_proof",
    ],
}


class DeterministicTriageAgent:
    """Rule-based triage classifier with strict JSON output validation."""

    def classify(
        self,
        *,
        ticket: dict[str, Any],
        customer_message: str,
        known_customer_id: str | None,
        known_order_id: str | None,
    ) -> TriageOutput:
        text = (customer_message or "").lower()
        explicit_issue = str(ticket.get("issue_type", "") or "").strip().lower()

        issue_type: str
        confidence: float
        if explicit_issue in ISSUE_TOOL_MAP:
            issue_type = explicit_issue
            confidence = 0.99
        elif "cancel" in text:
            issue_type = "cancel_order"
            confidence = 0.92
        elif "return" in text or "send back" in text:
            issue_type = "return_initiation"
            confidence = 0.9
        elif "not received" in text or "delivered" in text and "not" in text:
            issue_type = "delivered_not_received"
            confidence = 0.85
        elif "where" in text or "status" in text or "tracking" in text:
            issue_type = "order_status"
            confidence = 0.88
        else:
            issue_type = "order_status"
            confidence = 0.5

        missing_info_list: list[str] = []
        if not known_customer_id:
            missing_info_list.append("customer_id")
        if not known_order_id:
            missing_info_list.append("order_id")
        if issue_type == "return_initiation" and not ticket.get("item_id"):
            missing_info_list.append("item_id")

        required_tools_list = ISSUE_TOOL_MAP.get(issue_type, ["get_order"])
        return TriageOutput(
            issue_type=issue_type,
            missing_info_list=missing_info_list,
            required_tools_list=required_tools_list,
            confidence=confidence,
        )
