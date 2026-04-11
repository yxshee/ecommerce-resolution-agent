from __future__ import annotations

from ecom_resolution_agent.orchestration.nodes.common import (
    OrchestrationDeps,
    dump_state,
    load_state,
)


def run_classify_issue(
    state_payload: dict[str, object],
    deps: OrchestrationDeps,
) -> dict[str, object]:
    state = load_state(state_payload)
    state.current_state = "classify_issue"

    triage_output = deps.triage_agent.classify(
        ticket=state.ticket,
        customer_message=state.customer_message,
        known_customer_id=state.customer_id,
        known_order_id=state.order_id,
    )
    state.triage_output = triage_output
    state.issue_type = triage_output.issue_type
    state.status = "issue_classified"
    state.next_state = "policy_lookup"
    return dump_state(state)
