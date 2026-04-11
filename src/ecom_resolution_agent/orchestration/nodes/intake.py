from __future__ import annotations

from typing import Any

from ecom_resolution_agent.orchestration.nodes.common import dump_state, load_state


def run_intake(state_payload: dict[str, Any]) -> dict[str, Any]:
    state = load_state(state_payload)
    state.current_state = "intake"

    if not state.customer_message:
        state.customer_message = str(state.ticket.get("customer_message", "") or "")
    if state.customer_id is None:
        state.customer_id = state.ticket.get("customer_id")
    if state.order_id is None:
        state.order_id = state.ticket.get("order_id")

    state.status = "intake_complete"
    state.next_state = "verify_identity"
    return dump_state(state)
