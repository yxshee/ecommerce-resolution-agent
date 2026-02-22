from __future__ import annotations

from typing import Any

from ecom_resolution_agent.risk.scorer import RiskScorer
from ecom_resolution_agent.schemas.agent_outputs import PolicyOutput, RiskOutput


class DeterministicRiskAgent:
    def __init__(self, scorer: RiskScorer | None = None) -> None:
        self.scorer = scorer or RiskScorer()

    def assess(self, *, facts: dict[str, Any], policy_output: PolicyOutput) -> RiskOutput:
        return self.scorer.score(facts=facts, policy_output=policy_output)
