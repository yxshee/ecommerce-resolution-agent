from __future__ import annotations

from ecom_resolution_agent.actions.caps import ActionCapsService
from ecom_resolution_agent.approvals import ApprovalService
from ecom_resolution_agent.risk import RiskScorer
from ecom_resolution_agent.schemas.agent_outputs import PolicyOutput


def test_risk_scorer_requires_approval_for_high_value_and_policy_flag() -> None:
    scorer = RiskScorer()
    policy = PolicyOutput(
        policy_version="v1_0_0",
        allowed_actions=["refund_full", "escalate_human"],
        constraints={},
        required_evidence=["tracking_events", "delivery_proof"],
        approval_required=True,
    )
    risk = scorer.score(
        facts={"order_total_cents": 80000, "cross_border": False, "delivery_proof_available": True},
        policy_output=policy,
    )

    assert risk.approval_required is True
    assert risk.risk_score >= 0.7
    assert "policy_requires_approval" in risk.risk_reasons


def test_risk_scorer_blocks_refund_and_reship_for_chargeback_history() -> None:
    scorer = RiskScorer()
    policy = PolicyOutput(
        policy_version="v1_0_0",
        allowed_actions=["replacement_reship", "refund_partial", "refund_full", "escalate_human"],
        constraints={},
        required_evidence=[],
        approval_required=False,
    )
    risk = scorer.score(
        facts={"customer_profile": {"risk_flags": ["chargeback_history"]}},
        policy_output=policy,
    )

    assert "refund_full" in risk.blocked_actions
    assert "replacement_reship" in risk.blocked_actions
    assert risk.risk_score >= 0.7


def test_approval_tokens_are_one_time_use() -> None:
    service = ApprovalService()
    result = service.request_approval(
        run_id="run_1",
        ticket_id="t_1",
        action_type="refund_full",
        order_id="ord_1",
        requested_reason="high risk",
        max_amount_cents=1000,
        ttl_seconds=60,
    )

    first = service.consume_approval_token(result.token)
    second = service.consume_approval_token(result.token)

    assert first is not None
    assert first.run_id == "run_1"
    assert second is None


def test_action_caps_enforce_thresholds() -> None:
    caps = ActionCapsService()

    assert caps.check_per_run(actions_this_run=3).allowed is False
    assert caps.check_customer_refunds_per_day(refunds_today=2).allowed is False

    percent_cap = caps.check_order_refund_percent(order_total_cents=10000, refund_amount_cents=6000)
    assert percent_cap.allowed is False
    assert percent_cap.approval_required is True
