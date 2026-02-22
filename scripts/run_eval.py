#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = REPO_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from ecom_resolution_agent.eval import (  # noqa: E402
    EvaluationHarness,
    EvaluationHarnessConfig,
    enforce_regression_thresholds,
    load_eval_scenarios,
    load_eval_thresholds,
    score_observations,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Offline regression evaluation harness")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=REPO_ROOT / "datasets" / "scenarios_v1.jsonl",
        help="Path to evaluation scenarios JSONL",
    )
    parser.add_argument(
        "--thresholds",
        type=Path,
        default=REPO_ROOT / "datasets" / "eval_thresholds.json",
        help="Path to regression thresholds JSON",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Run only the first N scenarios (for quick local iteration)",
    )
    parser.add_argument(
        "--write-artifacts",
        action="store_true",
        help="Write per-run artifacts (disabled by default for speed)",
    )
    parser.add_argument(
        "--artifact-dir",
        type=Path,
        default=REPO_ROOT / "artifacts" / "eval_runs",
        help="Artifact directory when --write-artifacts is enabled",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional path to write JSON summary",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    scenarios = load_eval_scenarios(args.dataset)
    if args.limit is not None:
        scenarios = scenarios[: args.limit]
        if not scenarios:
            raise SystemExit("--limit produced zero scenarios")

    harness = EvaluationHarness(
        EvaluationHarnessConfig(
            artifact_base_dir=(args.artifact_dir if args.write_artifacts else None),
        )
    )
    observations = [harness.run_scenario(scenario) for scenario in scenarios]
    summary = score_observations(observations)
    thresholds = load_eval_thresholds(args.thresholds)
    failures = enforce_regression_thresholds(summary=summary, thresholds=thresholds)

    payload = summary.to_json()
    payload["threshold_file"] = str(args.thresholds)
    payload["dataset_file"] = str(args.dataset)
    payload["gate"] = {
        "passed": not failures,
        "failures": failures,
    }

    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    _print_summary(payload)
    return 0 if not failures else 1


def _print_summary(payload: dict[str, object]) -> None:
    metrics = payload.get("metrics", {})
    gate = payload.get("gate", {})
    if not isinstance(metrics, dict) or not isinstance(gate, dict):
        print("Malformed evaluation output payload", file=sys.stderr)
        return

    print("Phase 9 Eval Regression")
    print(f"Scenarios: {payload.get('scenario_count')}  Attempts: {payload.get('attempt_count')}")
    for key in [
        "resolution_accuracy",
        "policy_compliance_rate",
        "wrong_action_rate_critical",
        "unnecessary_escalation_rate",
        "average_turns",
        "tool_calls_per_ticket_avg",
        "refund_leakage_rate",
        "pii_leakage_rate",
    ]:
        print(f"- {key}: {metrics.get(key)}")

    passed = bool(gate.get("passed"))
    print(f"Gate: {'PASS' if passed else 'FAIL'}")
    failures = gate.get("failures", [])
    if isinstance(failures, list) and failures:
        for failure in failures:
            print(f"  * {failure}")


if __name__ == "__main__":
    raise SystemExit(main())
