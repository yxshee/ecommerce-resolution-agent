from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, TypeAlias

JsonDict: TypeAlias = dict[str, Any]


@dataclass(frozen=True)
class ScenarioExpected:
    selected_action: str
    qa_approved: bool
    human_escalation: bool
    injection_detected: bool = False
    action_status: str | None = None
    duplicate_replay: bool | None = None
    policy_compliant: bool = True
    allow_refund: bool = False
    max_refund_amount_cents: int | None = None
    critical: bool = False


@dataclass(frozen=True)
class EvalScenario:
    scenario_id: str
    ticket: JsonDict
    expected: ScenarioExpected
    labels: tuple[str, ...] = ()
    repeat_count: int = 1
    store_overrides: JsonDict = field(default_factory=dict)
    metadata: JsonDict = field(default_factory=dict)

    def has_label(self, label: str) -> bool:
        return label in self.labels


@dataclass(frozen=True)
class AttemptObservation:
    attempt_index: int
    run_id: str
    selected_action: str
    qa_approved: bool
    qa_escalate_to_human: bool
    injection_detected: bool
    qa_violations: tuple[str, ...]
    action_status: str | None
    action_type: str | None
    action_error_code: str | None
    tool_call_count: int
    final_ticket_status: str | None
    report_customer_markdown: str
    report_internal_markdown: str
    audit_bundle_refs: tuple[str, ...]
    audit_events_json: tuple[JsonDict, ...]


@dataclass(frozen=True)
class ScenarioObservation:
    scenario: EvalScenario
    attempts: tuple[AttemptObservation, ...]
    checks: dict[str, bool]
    check_failures: tuple[str, ...]
    observed_human_escalation: bool
    observed_policy_compliant: bool
    refund_leakage: bool
    pii_leakage: bool
    duplicate_replay_observed: bool
    turns: int
    tool_calls_total: int


@dataclass(frozen=True)
class EvalRunSummary:
    scenario_count: int
    attempt_count: int
    metrics: dict[str, float]
    checks: dict[str, dict[str, int]]
    failed_checks: dict[str, list[str]]
    scenarios: tuple[ScenarioObservation, ...]

    def to_json(self) -> JsonDict:
        return {
            "scenario_count": self.scenario_count,
            "attempt_count": self.attempt_count,
            "metrics": self.metrics,
            "checks": self.checks,
            "failed_checks": self.failed_checks,
            "scenarios": [
                {
                    "scenario_id": item.scenario.scenario_id,
                    "labels": list(item.scenario.labels),
                    "check_failures": list(item.check_failures),
                    "observed_human_escalation": item.observed_human_escalation,
                    "observed_policy_compliant": item.observed_policy_compliant,
                    "refund_leakage": item.refund_leakage,
                    "pii_leakage": item.pii_leakage,
                    "duplicate_replay_observed": item.duplicate_replay_observed,
                    "turns": item.turns,
                    "tool_calls_total": item.tool_calls_total,
                    "attempts": [
                        {
                            "attempt_index": attempt.attempt_index,
                            "run_id": attempt.run_id,
                            "selected_action": attempt.selected_action,
                            "qa_approved": attempt.qa_approved,
                            "qa_escalate_to_human": attempt.qa_escalate_to_human,
                            "injection_detected": attempt.injection_detected,
                            "qa_violations": list(attempt.qa_violations),
                            "action_status": attempt.action_status,
                            "action_type": attempt.action_type,
                            "action_error_code": attempt.action_error_code,
                            "tool_call_count": attempt.tool_call_count,
                            "final_ticket_status": attempt.final_ticket_status,
                            "audit_bundle_refs": list(attempt.audit_bundle_refs),
                        }
                        for attempt in item.attempts
                    ],
                }
                for item in self.scenarios
            ],
        }


@dataclass(frozen=True)
class MetricThreshold:
    min: float | None = None
    max: float | None = None


@dataclass(frozen=True)
class CheckThreshold:
    max_failures: int = 0


@dataclass(frozen=True)
class EvalThresholds:
    phase: int
    metrics: dict[str, MetricThreshold]
    checks: dict[str, CheckThreshold]
    note: str | None = None
    source_path: Path | None = None
