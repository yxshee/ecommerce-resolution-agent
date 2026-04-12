from __future__ import annotations

from ecom_resolution_agent.schemas.actions import ActionExecutionResult
from ecom_resolution_agent.schemas.agent_outputs import QaVerificationResult, ResolutionDecision


def customer_resolution_template(
    *,
    ticket_id: str,
    order_id: str | None,
    decision: ResolutionDecision,
    action_result: ActionExecutionResult | None,
) -> str:
    status_line = (
        f"- Action status: `{action_result.status}`\n" if action_result is not None else ""
    )
    order_line = f"- Order ID: `{order_id}`\n" if order_id else ""
    return (
        "# Resolution Update\n\n"
        f"- Ticket ID: `{ticket_id}`\n"
        f"{order_line}"
        f"- Selected action: `{decision.selected_action}`\n"
        f"{status_line}\n"
        "## Message\n"
        f"{decision.customer_message_draft.strip()}\n"
    )


def internal_resolution_template(
    *,
    run_id: str,
    ticket_id: str,
    decision: ResolutionDecision,
    action_result: ActionExecutionResult | None,
    qa_result: QaVerificationResult | None,
) -> str:
    action_line = (
        f"- Action execution status: `{action_result.status}`\n"
        if action_result is not None
        else "- Action execution: `not_provided`\n"
    )
    qa_line = (
        f"- QA approved: `{qa_result.approved}`\n"
        if qa_result is not None
        else "- QA result: `not_provided`\n"
    )
    return (
        "# Internal Resolution Summary\n\n"
        f"- Run ID: `{run_id}`\n"
        f"- Ticket ID: `{ticket_id}`\n"
        f"- Selected action: `{decision.selected_action}`\n"
        f"{action_line}"
        f"{qa_line}\n"
        "## Rationale\n"
        f"{decision.rationale.strip()}\n"
    )
