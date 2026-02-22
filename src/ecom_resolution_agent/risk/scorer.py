from __future__ import annotations

from typing import Any

from ecom_resolution_agent.schemas.agent_outputs import PolicyOutput, RiskOutput


class RiskScorer:
    def score(self, *, facts: dict[str, Any], policy_output: PolicyOutput) -> RiskOutput:
        score = 0.05
        reasons: list[str] = []
        blocked_actions: list[str] = []

        customer_profile = facts.get("customer_profile", {}) if isinstance(facts, dict) else {}
        risk_flags = (
            customer_profile.get("risk_flags", []) if isinstance(customer_profile, dict) else []
        )
        if "chargeback_history" in risk_flags:
            score += 0.65
            reasons.append("customer_chargeback_history")
            blocked_actions.extend(["refund_partial", "refund_full", "replacement_reship"])

        if facts.get("cross_border") is True:
            score += 0.15
            reasons.append("cross_border_order")

        if facts.get("cash_on_delivery") is True:
            score += 0.2
            reasons.append("cash_on_delivery")

        if facts.get("delivery_proof_available") is False:
            score += 0.2
            reasons.append("no_delivery_proof")

        order_total_cents = facts.get("order_total_cents")
        if isinstance(order_total_cents, int) and order_total_cents >= 50000:
            score += 0.35
            reasons.append("high_order_value")

        if policy_output.approval_required:
            score = max(score, 0.7)
            reasons.append("policy_requires_approval")

        risk_score = min(1.0, round(score, 2))
        approval_required = policy_output.approval_required or risk_score >= 0.7

        return RiskOutput(
            risk_score=risk_score,
            risk_reasons=reasons,
            approval_required=approval_required,
            blocked_actions=sorted(set(blocked_actions)),
        )
