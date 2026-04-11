from __future__ import annotations

from ecom_resolution_agent.orchestration.nodes.common import (
    OrchestrationDeps,
    append_error,
    dump_state,
    load_state,
    record_tool_result,
    tool_context,
)
from ecom_resolution_agent.orchestration.state import END_ROUTE


def run_verify_identity(
    state_payload: dict[str, object], deps: OrchestrationDeps
) -> dict[str, object]:
    state = load_state(state_payload)
    state.current_state = "verify_identity"

    if not state.customer_id or not state.order_id:
        state.requested_verification = True
        state.status = "needs_verification"
        state.next_state = END_ROUTE
        append_error(state, "missing_customer_or_order_id")
        return dump_state(state)

    verify_input = {
        "customer_id": state.customer_id,
        "order_id": state.order_id,
        "email": state.ticket.get("customer_email") or state.ticket.get("email"),
        "phone_last4": state.ticket.get("phone_last4"),
    }
    result = deps.tool_executor.invoke(
        "verify_customer",
        verify_input,
        context=tool_context(state=state, actor_agent="triage"),
    )
    record_tool_result(state, "verify_customer", result.model_dump(mode="json"))

    if not result.ok or result.data is None or result.data.get("verified") is not True:
        state.requested_verification = True
        state.verification_passed = False
        state.verification_result = result.data
        state.status = "needs_verification"
        state.next_state = END_ROUTE
        append_error(state, "identity_verification_failed")
        return dump_state(state)

    state.verification_passed = True
    state.verification_result = result.data
    state.facts["customer_verified"] = True
    state.status = "identity_verified"
    state.next_state = "gather_facts"
    return dump_state(state)
