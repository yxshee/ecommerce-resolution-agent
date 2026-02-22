from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ecom_resolution_agent.eval.models import EvalScenario, ScenarioExpected


def load_eval_scenarios(path: str | Path) -> list[EvalScenario]:
    resolved_path = Path(path)
    scenarios: list[EvalScenario] = []
    lines = resolved_path.read_text(encoding="utf-8").splitlines()
    for line_number, raw_line in enumerate(lines, 1):
        line = raw_line.strip()
        if not line:
            continue
        payload = json.loads(line)
        scenarios.append(_parse_scenario(payload, line_number=line_number))

    if not scenarios:
        raise ValueError(f"No scenarios found in {resolved_path}")
    _validate_dataset_global_constraints(scenarios)
    return scenarios


def _parse_scenario(payload: dict[str, Any], *, line_number: int) -> EvalScenario:
    scenario_id = payload.get("scenario_id")
    if not isinstance(scenario_id, str) or not scenario_id:
        raise ValueError(f"Line {line_number}: scenario_id must be a non-empty string")

    ticket = payload.get("ticket")
    if not isinstance(ticket, dict):
        raise ValueError(f"Line {line_number}: ticket must be an object")

    expected_payload = payload.get("expected")
    if not isinstance(expected_payload, dict):
        raise ValueError(f"Line {line_number}: expected must be an object")

    labels_raw = payload.get("labels", [])
    if not isinstance(labels_raw, list) or not all(isinstance(item, str) for item in labels_raw):
        raise ValueError(f"Line {line_number}: labels must be a string array")
    labels = tuple(sorted(set(labels_raw)))

    repeat_count = payload.get("repeat_count", 1)
    if not isinstance(repeat_count, int) or repeat_count < 1:
        raise ValueError(f"Line {line_number}: repeat_count must be an integer >= 1")

    store_overrides = payload.get("store_overrides", {})
    if not isinstance(store_overrides, dict):
        raise ValueError(f"Line {line_number}: store_overrides must be an object")

    metadata = payload.get("metadata", {})
    if not isinstance(metadata, dict):
        raise ValueError(f"Line {line_number}: metadata must be an object")

    expected = _parse_expected(expected_payload, line_number=line_number)

    return EvalScenario(
        scenario_id=scenario_id,
        ticket=dict(ticket),
        expected=expected,
        labels=labels,
        repeat_count=repeat_count,
        store_overrides=store_overrides,
        metadata=metadata,
    )


def _parse_expected(payload: dict[str, Any], *, line_number: int) -> ScenarioExpected:
    selected_action = payload.get("selected_action")
    if not isinstance(selected_action, str) or not selected_action:
        raise ValueError(f"Line {line_number}: expected.selected_action must be a string")

    qa_approved = payload.get("qa_approved")
    human_escalation = payload.get("human_escalation")
    if not isinstance(qa_approved, bool):
        raise ValueError(f"Line {line_number}: expected.qa_approved must be a boolean")
    if not isinstance(human_escalation, bool):
        raise ValueError(f"Line {line_number}: expected.human_escalation must be a boolean")

    action_status = payload.get("action_status")
    if action_status is not None and not isinstance(action_status, str):
        raise ValueError(f"Line {line_number}: expected.action_status must be null or string")

    duplicate_replay = payload.get("duplicate_replay")
    if duplicate_replay is not None and not isinstance(duplicate_replay, bool):
        raise ValueError(f"Line {line_number}: expected.duplicate_replay must be null or boolean")

    max_refund = payload.get("max_refund_amount_cents")
    if max_refund is not None and not isinstance(max_refund, int):
        raise ValueError(
            f"Line {line_number}: expected.max_refund_amount_cents must be null or integer"
        )

    return ScenarioExpected(
        selected_action=selected_action,
        qa_approved=qa_approved,
        human_escalation=human_escalation,
        injection_detected=bool(payload.get("injection_detected", False)),
        action_status=action_status,
        duplicate_replay=duplicate_replay,
        policy_compliant=bool(payload.get("policy_compliant", True)),
        allow_refund=bool(payload.get("allow_refund", False)),
        max_refund_amount_cents=max_refund,
        critical=bool(payload.get("critical", False)),
    )


def _validate_dataset_global_constraints(scenarios: list[EvalScenario]) -> None:
    ids = [scenario.scenario_id for scenario in scenarios]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate scenario_id values detected in evaluation dataset")

    label_index: set[str] = set()
    for scenario in scenarios:
        label_index.update(scenario.labels)

    required_edge_labels = {"prompt_injection", "idempotency_duplicate_attempt"}
    missing = sorted(required_edge_labels - label_index)
    if missing:
        missing_str = ", ".join(missing)
        raise ValueError(f"Dataset is missing required edge-case label(s): {missing_str}")
