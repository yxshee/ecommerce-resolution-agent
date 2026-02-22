from __future__ import annotations

from typing import Any

from ecom_resolution_agent.orchestration.nodes.common import (
    OrchestrationDeps,
    append_error,
    dump_state,
    load_state,
    record_tool_result,
    tool_context,
)
from ecom_resolution_agent.orchestration.state import END_ROUTE, CaseState


def _invoke_or_stop(
    state: CaseState,
    deps: OrchestrationDeps,
    tool_name: str,
    tool_input: dict[str, Any],
    actor_agent: str = "triage",
) -> dict[str, Any] | None:
    result = deps.tool_executor.invoke(
        tool_name,
        tool_input,
        context=tool_context(state=state, actor_agent=actor_agent),
    )
    record_tool_result(state, tool_name, result.model_dump(mode="json"))
    if not result.ok or result.data is None:
        append_error(state, f"{tool_name}_failed")
        state.status = "fact_gather_failed"
        state.next_state = END_ROUTE
        return None
    return result.data


def run_gather_facts(
    state_payload: dict[str, object],
    deps: OrchestrationDeps,
) -> dict[str, object]:
    state = load_state(state_payload)
    state.current_state = "gather_facts"

    if not state.order_id or not state.customer_id:
        append_error(state, "missing_ids_for_fact_gather")
        state.status = "fact_gather_failed"
        state.next_state = END_ROUTE
        return dump_state(state)

    available_evidence: set[str] = set(state.facts.get("available_evidence", []))

    customer_profile = _invoke_or_stop(
        state,
        deps,
        "get_customer_profile",
        {"customer_id": state.customer_id},
    )
    if customer_profile is None:
        return dump_state(state)
    state.facts["customer_profile"] = customer_profile
    available_evidence.add("customer_profile")

    order = _invoke_or_stop(state, deps, "get_order", {"order_id": state.order_id})
    if order is None:
        return dump_state(state)
    state.facts["order"] = order
    state.facts["order_total_cents"] = order["total"]["amount_cents"]
    shipping_address = order.get("shipping_address") or {}
    state.facts["cross_border"] = shipping_address.get("country", "US") != "US"
    available_evidence.add("order")

    order_items = _invoke_or_stop(state, deps, "get_order_items", {"order_id": state.order_id})
    if order_items is None:
        return dump_state(state)
    state.facts["order_items"] = order_items["items"]
    available_evidence.add("order_items")

    if item_id := state.ticket.get("item_id"):
        state.facts["item_id"] = item_id
        available_evidence.add("item_id")

    fulfillment = _invoke_or_stop(
        state,
        deps,
        "get_fulfillment_status",
        {"order_id": state.order_id},
    )
    if fulfillment is None:
        return dump_state(state)
    state.facts["fulfillment_status"] = fulfillment["status"]
    state.facts["fulfillment"] = fulfillment
    available_evidence.add("fulfillment_status")

    tracking_number = fulfillment.get("tracking_number") or order.get("shipping_tracking_number")
    if tracking_number:
        tracking = _invoke_or_stop(
            state,
            deps,
            "get_tracking_events",
            {"tracking_number": tracking_number},
        )
        if tracking is not None:
            state.facts["tracking_events"] = tracking["events"]
            available_evidence.add("tracking_events")

        proof = _invoke_or_stop(
            state,
            deps,
            "get_delivery_proof",
            {"order_id": state.order_id, "tracking_number": tracking_number},
        )
        if proof is not None:
            state.facts["delivery_proof"] = proof
            state.facts["delivery_proof_available"] = bool(proof.get("available"))
            if proof.get("available"):
                available_evidence.add("delivery_proof")

    state.facts["available_evidence"] = sorted(available_evidence)
    state.status = "facts_gathered"
    state.next_state = "classify_issue"
    return dump_state(state)
