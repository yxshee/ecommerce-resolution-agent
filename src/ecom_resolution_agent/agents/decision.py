from __future__ import annotations

from dataclasses import dataclass

from ecom_resolution_agent.orchestration.state import CaseState
from ecom_resolution_agent.schemas.agent_outputs import ResolutionDecision


@dataclass
class DeterministicDecisionAgent:
    """Selects a safe resolution deterministically from policy/risk/facts."""

    action_priority: tuple[str, ...] = (
        "replacement_reship",
        "return_initiation",
        "refund_partial",
        "refund_full",
        "cancel_order",
        "address_update",
        "escalate_human",
    )

    def decide(self, state: CaseState) -> ResolutionDecision:
        policy_output = state.policy_output
        risk_output = state.risk_output
        if policy_output is None or risk_output is None:
            return self._escalation_decision(
                state=state,
                rationale="Missing policy or risk output.",
            )

        if risk_output.approval_required:
            return self._escalation_decision(
                state=state,
                rationale="Approval required before automated action.",
            )

        allowed = list(policy_output.allowed_actions)
        blocked = set(risk_output.blocked_actions)

        selected_action = "escalate_human"
        for candidate in self.action_priority:
            if candidate not in allowed:
                continue
            if candidate in blocked:
                continue
            if candidate in {"cancel_order", "address_update"}:
                # Tool support is not implemented for these actions yet.
                continue
            selected_action = candidate
            break

        if selected_action == "escalate_human":
            return self._escalation_decision(
                state=state,
                rationale="No safe auto-action available after policy/risk filtering.",
            )

        evidence_refs = self._evidence_refs(state)
        issue_type = state.issue_type or "unknown_issue"
        customer_message = self._customer_message(selected_action, issue_type)
        return ResolutionDecision(
            selected_action=selected_action,
            rationale=(
                "Selected "
                f"`{selected_action}` because it is allowed by policy "
                f"`{policy_output.policy_version}` "
                f"and not blocked by risk (score={risk_output.risk_score})."
            ),
            evidence_refs=evidence_refs,
            customer_message_draft=customer_message,
            internal_note_draft=(
                f"Decision selected `{selected_action}` for issue `{issue_type}` "
                "using policy "
                f"`{policy_output.policy_version}` and risk score "
                f"`{risk_output.risk_score}`."
            ),
        )

    def _escalation_decision(self, *, state: CaseState, rationale: str) -> ResolutionDecision:
        return ResolutionDecision(
            selected_action="escalate_human",
            rationale=rationale,
            evidence_refs=self._evidence_refs(state),
            customer_message_draft=(
                "We need a specialist to review this case before taking action. "
                "We have documented the details and escalated it for manual review."
            ),
            internal_note_draft=(f"Escalated to human reviewer. Reason: {rationale}"),
        )

    def _evidence_refs(self, state: CaseState) -> list[str]:
        refs: list[str] = []
        for tool_name, tool_result in sorted(state.tool_results.items()):
            if tool_result.get("ok") is True:
                refs.append(f"tool:{tool_name}")
        if state.verification_passed:
            refs.append("fact:identity_verified")
        if isinstance(state.facts.get("risk_score"), (int, float)):
            refs.append("fact:risk_score")
        return refs

    def _customer_message(self, action: str, issue_type: str) -> str:
        if action == "replacement_reship":
            return (
                "We verified your order details and can send a replacement shipment "
                "in simulation mode "
                "for this case. You will receive tracking updates once it is processed."
            )
        if action == "return_initiation":
            return (
                "We can start your return and generate a return workflow for the selected item. "
                "We will share next steps for label and pickup options."
            )
        if action in {"refund_partial", "refund_full"}:
            return (
                "We can issue a refund for this order in simulation mode after "
                "verifying policy and risk checks. "
                "The refund posting time depends on your payment provider."
            )
        return (
            "We reviewed your request and are escalating it for manual handling "
            f"because automated resolution is not available for `{issue_type}`."
        )
