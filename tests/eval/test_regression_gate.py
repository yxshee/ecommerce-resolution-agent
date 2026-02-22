from __future__ import annotations

from ecom_resolution_agent.eval.models import EvalRunSummary
from ecom_resolution_agent.eval.thresholds import (
    enforce_regression_thresholds,
    load_eval_thresholds,
)


def test_regression_gate_fails_when_critical_metric_regresses() -> None:
    thresholds = load_eval_thresholds("datasets/eval_thresholds.json")
    summary = EvalRunSummary(
        scenario_count=1,
        attempt_count=1,
        metrics={
            "resolution_accuracy": 1.0,
            "policy_compliance_rate": 1.0,
            "wrong_action_rate_critical": 0.1,
            "unnecessary_escalation_rate": 0.0,
            "average_turns": 1.0,
            "tool_calls_per_ticket_avg": 1.0,
            "refund_leakage_rate": 0.0,
            "pii_leakage_rate": 0.0,
        },
        checks={
            "audit_action_success_backed_by_audit": {"passed": 1, "failed": 0},
            "report_has_audit_refs": {"passed": 1, "failed": 0},
            "no_pii_leakage": {"passed": 1, "failed": 0},
            "prompt_injection_blocked": {"passed": 1, "failed": 0},
            "idempotency_duplicate_replayed": {"passed": 1, "failed": 0},
        },
        failed_checks={},
        scenarios=(),
    )

    failures = enforce_regression_thresholds(summary=summary, thresholds=thresholds)

    assert any("wrong_action_rate_critical" in failure for failure in failures)
