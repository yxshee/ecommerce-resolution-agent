from __future__ import annotations

from pathlib import Path

from ecom_resolution_agent.eval import EvaluationHarness, load_eval_scenarios, score_observations

DATASET_PATH = Path("datasets/scenarios_v1.jsonl")


def _pick_scenarios() -> list[str]:
    return [
        "dnr_reship_happy",
        "return_happy",
        "return_duplicate",
        "dnr_prompt_injection",
        "return_missing_item",
        "dnr_no_stock_action_failure",
    ]


def _select_by_template() -> list:
    selected = []
    seen_templates: set[str] = set()
    for scenario in load_eval_scenarios(DATASET_PATH):
        template = str(scenario.metadata.get("template", ""))
        if template not in _pick_scenarios():
            continue
        if template in seen_templates:
            continue
        seen_templates.add(template)
        selected.append(scenario)
        if len(seen_templates) == len(_pick_scenarios()):
            break
    return selected


def test_harness_scores_subset_with_prompt_injection_and_idempotency_checks() -> None:
    selected = _select_by_template()

    harness = EvaluationHarness()
    observations = [harness.run_scenario(scenario) for scenario in selected]
    summary = score_observations(observations)

    assert summary.scenario_count == len(selected)
    assert summary.attempt_count == 7  # one duplicate scenario repeats once
    assert set(summary.metrics) == {
        "resolution_accuracy",
        "policy_compliance_rate",
        "wrong_action_rate_critical",
        "unnecessary_escalation_rate",
        "average_turns",
        "tool_calls_per_ticket_avg",
        "refund_leakage_rate",
        "pii_leakage_rate",
    }
    assert summary.failed_checks == {}

    duplicate_obs = next(
        item for item in observations if "idempotency_duplicate_attempt" in item.scenario.labels
    )
    assert duplicate_obs.duplicate_replay_observed is True
    assert duplicate_obs.attempts[1].action_status == "duplicate_replay"

    prompt_obs = next(item for item in observations if "prompt_injection" in item.scenario.labels)
    assert prompt_obs.attempts[0].injection_detected is True
    assert prompt_obs.attempts[0].qa_approved is False
    assert prompt_obs.observed_human_escalation is True


def test_subset_run_is_deterministic_on_metrics_and_check_rollups() -> None:
    selected = _select_by_template()

    harness = EvaluationHarness()
    first = score_observations([harness.run_scenario(scenario) for scenario in selected])
    second = score_observations([harness.run_scenario(scenario) for scenario in selected])

    assert first.metrics == second.metrics
    assert first.checks == second.checks
    assert first.failed_checks == second.failed_checks
