from __future__ import annotations

from typing import Any

from ecom_resolution_agent.policy.loader import PolicyIssueRule, PolicyVariant
from ecom_resolution_agent.schemas.agent_outputs import PolicyOutput


class PolicyEvaluator:
    def evaluate(
        self,
        *,
        policy_version: str,
        issue_type: str,
        issue_rule: PolicyIssueRule | None,
        facts: dict[str, Any],
    ) -> PolicyOutput:
        if issue_rule is None:
            return PolicyOutput(
                policy_version=policy_version,
                allowed_actions=["escalate_human"],
                constraints={"reason": "unknown_issue_type"},
                required_evidence=[],
                approval_required=True,
            )

        variant = self._select_variant(issue_rule, facts)
        available_evidence = set(self._available_evidence(facts))
        missing_evidence = [e for e in variant.required_evidence if e not in available_evidence]

        approval_required = self._approval_required(variant, facts)
        constraints = dict(variant.constraints)
        if missing_evidence:
            constraints["missing_evidence"] = missing_evidence
            if variant.on_missing_evidence == "defer":
                constraints["deferred"] = True
                allowed_actions = [a for a in variant.allowed_actions if a == "escalate_human"]
                if not allowed_actions:
                    allowed_actions = ["escalate_human"]
            else:
                allowed_actions = ["escalate_human"]
        else:
            allowed_actions = list(variant.allowed_actions)

        return PolicyOutput(
            policy_version=policy_version,
            allowed_actions=allowed_actions,
            constraints=constraints,
            required_evidence=list(variant.required_evidence),
            approval_required=approval_required,
        )

    def _select_variant(self, issue_rule: PolicyIssueRule, facts: dict[str, Any]) -> PolicyVariant:
        for variant in issue_rule.variants:
            if self._matches(variant.when, facts):
                return variant
        return issue_rule.default

    def _matches(self, when: dict[str, Any], facts: dict[str, Any]) -> bool:
        fact_equals = when.get("fact_equals", {})
        for key, value in fact_equals.items():
            if self._fact_value(facts, key) != value:
                return False

        fact_in = when.get("fact_in", {})
        for key, options in fact_in.items():
            if self._fact_value(facts, key) not in set(options):
                return False

        fact_gte = when.get("fact_gte", {})
        for key, threshold in fact_gte.items():
            fact_val = self._fact_value(facts, key)
            if fact_val is None or float(fact_val) < float(threshold):
                return False

        return True

    def _approval_required(self, variant: PolicyVariant, facts: dict[str, Any]) -> bool:
        if variant.approval_required:
            return True

        overrides = variant.approval_overrides
        order_total_threshold = overrides.get("order_total_cents_gte")
        if order_total_threshold is not None:
            order_total = self._fact_value(facts, "order_total_cents")
            if order_total is not None and int(order_total) >= int(order_total_threshold):
                return True

        if (
            overrides.get("cross_border") is True
            and self._fact_value(facts, "cross_border") is True
        ):
            return True

        if (
            overrides.get("cash_on_delivery") is True
            and self._fact_value(
                facts,
                "cash_on_delivery",
            )
            is True
        ):
            return True

        return False

    def _available_evidence(self, facts: dict[str, Any]) -> list[str]:
        if isinstance(facts.get("available_evidence"), list):
            return [str(item) for item in facts["available_evidence"]]
        evidence = facts.get("evidence")
        if isinstance(evidence, dict):
            return [key for key, value in evidence.items() if bool(value)]
        return []

    def _fact_value(self, facts: dict[str, Any], key: str) -> Any:
        current: Any = facts
        for part in key.split("."):
            if not isinstance(current, dict) or part not in current:
                return None
            current = current[part]
        return current
