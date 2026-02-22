from __future__ import annotations

from pathlib import Path

from ecom_resolution_agent.eval import load_eval_scenarios, load_eval_thresholds

DATASET_PATH = Path("datasets/scenarios_v1.jsonl")
THRESHOLDS_PATH = Path("datasets/eval_thresholds.json")


def test_phase9_dataset_contract_and_edge_labels() -> None:
    scenarios = load_eval_scenarios(DATASET_PATH)

    assert len(scenarios) == 250

    label_counts: dict[str, int] = {}
    for scenario in scenarios:
        for label in scenario.labels:
            label_counts[label] = label_counts.get(label, 0) + 1

    assert label_counts.get("prompt_injection", 0) > 0
    assert label_counts.get("idempotency_duplicate_attempt", 0) > 0

    for scenario in scenarios:
        assert scenario.ticket.get("ticket_id")
        assert scenario.expected.selected_action
        assert scenario.repeat_count >= 1


def test_phase9_thresholds_define_metric_and_check_gates() -> None:
    thresholds = load_eval_thresholds(THRESHOLDS_PATH)

    assert thresholds.phase == 9
    for metric_name in [
        "resolution_accuracy",
        "policy_compliance_rate",
        "wrong_action_rate_critical",
        "unnecessary_escalation_rate",
        "average_turns",
        "tool_calls_per_ticket_avg",
        "refund_leakage_rate",
        "pii_leakage_rate",
    ]:
        assert metric_name in thresholds.metrics

    for check_name in [
        "audit_action_success_backed_by_audit",
        "report_has_audit_refs",
        "no_pii_leakage",
        "prompt_injection_blocked",
        "idempotency_duplicate_replayed",
    ]:
        assert check_name in thresholds.checks
