from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ecom_resolution_agent.eval.models import (
    CheckThreshold,
    EvalRunSummary,
    EvalThresholds,
    MetricThreshold,
)


def load_eval_thresholds(path: str | Path) -> EvalThresholds:
    resolved_path = Path(path)
    payload = json.loads(resolved_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Threshold file must contain a JSON object")

    phase = payload.get("phase")
    if not isinstance(phase, int):
        raise ValueError("Threshold file must include integer `phase`")

    metrics_payload = payload.get("metrics")
    if not isinstance(metrics_payload, dict):
        raise ValueError("Threshold file must include object `metrics`")

    checks_payload = payload.get("checks")
    if not isinstance(checks_payload, dict):
        raise ValueError("Threshold file must include object `checks`")

    metrics: dict[str, MetricThreshold] = {}
    for name, config in metrics_payload.items():
        if not isinstance(name, str) or not isinstance(config, dict):
            raise ValueError("Each metric threshold entry must be an object")
        min_value = _float_or_none(config.get("min"))
        max_value = _float_or_none(config.get("max"))
        metrics[name] = MetricThreshold(min=min_value, max=max_value)

    checks: dict[str, CheckThreshold] = {}
    for name, config in checks_payload.items():
        if not isinstance(name, str) or not isinstance(config, dict):
            raise ValueError("Each check threshold entry must be an object")
        max_failures = config.get("max_failures", 0)
        if not isinstance(max_failures, int) or max_failures < 0:
            raise ValueError("check.max_failures must be an integer >= 0")
        checks[name] = CheckThreshold(max_failures=max_failures)

    note = payload.get("note")
    if note is not None and not isinstance(note, str):
        raise ValueError("`note` must be a string if provided")

    return EvalThresholds(
        phase=phase,
        metrics=metrics,
        checks=checks,
        note=note,
        source_path=resolved_path,
    )


def enforce_regression_thresholds(
    *,
    summary: EvalRunSummary,
    thresholds: EvalThresholds,
) -> list[str]:
    failures: list[str] = []

    for metric_name, metric_threshold in thresholds.metrics.items():
        if metric_name not in summary.metrics:
            failures.append(f"missing_metric:{metric_name}")
            continue
        value = summary.metrics[metric_name]
        if metric_threshold.min is not None and value < metric_threshold.min:
            failures.append(f"metric:{metric_name}:value={value} below min={metric_threshold.min}")
        if metric_threshold.max is not None and value > metric_threshold.max:
            failures.append(f"metric:{metric_name}:value={value} above max={metric_threshold.max}")

    for check_name, check_threshold in thresholds.checks.items():
        check_result = summary.checks.get(check_name)
        failed_count = 0 if check_result is None else int(check_result.get("failed", 0))
        if failed_count > check_threshold.max_failures:
            failures.append(
                "check:"
                f"{check_name}:failed={failed_count} exceeds "
                f"max_failures={check_threshold.max_failures}"
            )

    return failures


def _float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    raise ValueError("metric threshold min/max must be numeric or null")
