from __future__ import annotations

from pathlib import Path

from ecom_resolution_agent.eval.harness import EvaluationHarness, EvaluationHarnessConfig
from ecom_resolution_agent.eval.models import EvalRunSummary
from ecom_resolution_agent.eval.scorer import score_observations


def run_evaluation(
    *,
    dataset_path: str | Path,
    write_artifacts: bool = False,
    artifact_dir: str | Path | None = None,
) -> EvalRunSummary:
    from ecom_resolution_agent.eval.dataset import load_eval_scenarios

    scenarios = load_eval_scenarios(dataset_path)
    config = EvaluationHarnessConfig(
        artifact_base_dir=Path(artifact_dir) if write_artifacts and artifact_dir else None
    )
    harness = EvaluationHarness(config)
    observations = [harness.run_scenario(scenario) for scenario in scenarios]
    return score_observations(observations)
