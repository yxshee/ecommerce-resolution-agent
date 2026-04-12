from __future__ import annotations

from ecom_resolution_agent.orchestration.nodes.common import (
    OrchestrationDeps,
    append_error,
    dump_state,
    load_state,
)
from ecom_resolution_agent.orchestration.state import END_ROUTE


def run_risk_assessment(
    state_payload: dict[str, object],
    deps: OrchestrationDeps,
) -> dict[str, object]:
    state = load_state(state_payload)
    state.current_state = "risk_assessment"

    if state.policy_output is None:
        append_error(state, "missing_policy_output")
        state.status = "risk_assessment_failed"
        state.next_state = END_ROUTE
        return dump_state(state)

    risk_output = deps.risk_agent.assess(facts=state.facts, policy_output=state.policy_output)

    requested_refund_amount_cents = state.ticket.get("requested_refund_amount_cents")
    if isinstance(requested_refund_amount_cents, int) and isinstance(
        state.facts.get("order_total_cents"),
        int,
    ):
        percent_check = deps.caps_service.check_order_refund_percent(
            order_total_cents=state.facts["order_total_cents"],
            refund_amount_cents=requested_refund_amount_cents,
        )
        if not percent_check.allowed and percent_check.approval_required:
            risk_output.approval_required = True
            if percent_check.reason is not None:
                risk_output.risk_reasons.append(percent_check.reason)

    state.risk_output = risk_output
    state.facts["risk_score"] = risk_output.risk_score

    auto_actions = [a for a in state.policy_output.allowed_actions if a != "escalate_human"]
    if auto_actions and all(action in risk_output.blocked_actions for action in auto_actions):
        state.status = "blocked_high_risk"
        state.next_state = END_ROUTE
        return dump_state(state)

    if risk_output.approval_required:
        requested_action = auto_actions[0] if auto_actions else "escalate_human"
        approval = deps.approval_service.request_approval(
            run_id=state.run_id,
            ticket_id=str(state.ticket.get("ticket_id")) if state.ticket.get("ticket_id") else None,
            action_type=requested_action,
            order_id=str(state.order_id or "unknown_order"),
            requested_reason=", ".join(risk_output.risk_reasons) or "risk_threshold_exceeded",
            max_amount_cents=(
                requested_refund_amount_cents
                if isinstance(requested_refund_amount_cents, int)
                else None
            ),
        )
        state.approval_task_id = approval.task.approval_task_id
        state.approval_token = approval.token
        state.status = "approval_required"
        state.next_state = END_ROUTE
        return dump_state(state)

    state.status = "risk_assessed"
    state.next_state = END_ROUTE
    return dump_state(state)
