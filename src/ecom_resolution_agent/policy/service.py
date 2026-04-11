from __future__ import annotations

from typing import Any

from ecom_resolution_agent.policy.evaluator import PolicyEvaluator
from ecom_resolution_agent.policy.loader import LoadedPolicyBundle, PolicyLoader
from ecom_resolution_agent.schemas.agent_outputs import PolicyOutput


class PolicyService:
    """Policy engine wrapper used by the Policy Agent and API/CLI callers."""

    def __init__(
        self,
        loader: PolicyLoader | None = None,
        evaluator: PolicyEvaluator | None = None,
    ) -> None:
        self.loader = loader or PolicyLoader()
        self.evaluator = evaluator or PolicyEvaluator()

    def load_bundle(self, policy_version: str) -> LoadedPolicyBundle:
        return self.loader.load(policy_version)

    def evaluate(
        self,
        *,
        issue_type: str,
        facts: dict[str, Any],
        policy_version: str,
    ) -> PolicyOutput:
        bundle = self.load_bundle(policy_version)
        issue_rule = bundle.rules.issue_rules.get(issue_type)
        return self.evaluator.evaluate(
            policy_version=bundle.metadata.version,
            issue_type=issue_type,
            issue_rule=issue_rule,
            facts=facts,
        )

    def get_policy_rules(self, policy_version: str) -> dict[str, Any]:
        bundle = self.load_bundle(policy_version)
        return bundle.rules.model_dump(mode="json")
