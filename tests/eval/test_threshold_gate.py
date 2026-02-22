from __future__ import annotations

from ecom_resolution_agent.eval.models import EvalRunSummary
from ecom_resolution_agent.eval.thresholds import (
    enforce_regression_thresholds,
    load_eval_thresholds,
)


def _summary_with_metrics(**overrides: float) -> EvalRunSummary:
    metrics = {
        "resolution_accuracy": 1.0,
        "policy_compliance_rate": 1.0,
        "wrong_action_rate_critical": 0.0,
        "unnecessary_escalation_rate": 0.0,
        "average_turns": 1.14,
        "tool_calls_per_ticket_avg": 14.644,
        "refund_leakage_rate": 0.0,
        "pii_leakage_rate": 0.0,
    }
    metrics.update(overrides)
    checks = {
        "audit_action_success_backed_by_audit": {"passed": 250, "failed": 0},
        "report_has_audit_refs": {"passed": 250, "failed": 0},
        "no_pii_leakage": {"passed": 250, "failed": 0},
        "prompt_injection_blocked": {"passed": 250, "failed": 0},
        "idempotency_duplicate_replayed": {"passed": 250, "failed": 0},
    }
    return EvalRunSummary(
        scenario_count=250,
        attempt_count=285,
        metrics=metrics,
        checks=checks,
        failed_checks={},
        scenarios=(),
    )


def test_regression_gate_passes_baseline_metrics() -> None:
    thresholds = load_eval_thresholds("datasets/eval_thresholds.json")
    failures = enforce_regression_thresholds(summary=_summary_with_metrics(), thresholds=thresholds)

    assert failures == []


def test_regression_gate_fails_on_metric_and_check_regressions() -> None:
    thresholds = load_eval_thresholds("datasets/eval_thresholds.json")
    summary = _summary_with_metrics(resolution_accuracy=0.95)
    summary = EvalRunSummary(
        scenario_count=summary.scenario_count,
        attempt_count=summary.attempt_count,
        metrics=summary.metrics,
        checks={
            **summary.checks,
            "no_pii_leakage": {"passed": 249, "failed": 1},
        },
        failed_checks={"no_pii_leakage": ["scenario_001"]},
        scenarios=summary.scenarios,
    )

    failures = enforce_regression_thresholds(summary=summary, thresholds=thresholds)

    assert any("metric:resolution_accuracy" in failure for failure in failures)
    assert any("check:no_pii_leakage" in failure for failure in failures)
