from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ecom_resolution_agent.qa.prompt_injection import (
    PromptInjectionDetection,
    PromptInjectionDetector,
)
from ecom_resolution_agent.schemas.agent_outputs import (
    PolicyOutput,
    QaVerificationResult,
    ResolutionDecision,
    RiskOutput,
)


@dataclass(frozen=True)
class QaValidationInputs:
    customer_message: str
    verification_passed: bool
    policy_output: PolicyOutput
    risk_output: RiskOutput
    decision: ResolutionDecision
    facts: dict[str, Any]
    tool_results: dict[str, dict[str, Any]]


class QaValidator:
    def __init__(self, *, injection_detector: PromptInjectionDetector | None = None) -> None:
        self.injection_detector = injection_detector or PromptInjectionDetector()

    def validate(self, inputs: QaValidationInputs) -> QaVerificationResult:
        violations: list[str] = []
        evidence_refs: list[str] = []

        injection = self.injection_detector.detect(inputs.customer_message)
        if injection.detected:
            violations.extend(
                [f"prompt_injection_detected:{pattern}" for pattern in injection.matched_patterns]
            )

        if not inputs.verification_passed:
            violations.append("identity_not_verified")

        if inputs.decision.selected_action not in inputs.policy_output.allowed_actions:
            violations.append("selected_action_not_allowed_by_policy")

        if inputs.decision.selected_action in inputs.risk_output.blocked_actions:
            violations.append("selected_action_blocked_by_risk")

        missing_evidence = self._missing_required_evidence(inputs)
        violations.extend(f"missing_evidence:{evidence}" for evidence in missing_evidence)

        if "delivery_proof" in inputs.policy_output.required_evidence and (
            "get_delivery_proof" in inputs.tool_results
        ):
            evidence_refs.append("tool:get_delivery_proof")
        if inputs.risk_output.risk_score >= 0:
            evidence_refs.append("fact:risk_score")
        if inputs.verification_passed:
            evidence_refs.append("fact:identity_verified")

        approved = not violations
        escalate = injection.detected or any(v.startswith("missing_evidence:") for v in violations)
        return QaVerificationResult(
            approved=approved,
            violations=violations,
            injection_detected=injection.detected,
            escalate_to_human=escalate,
            evidence_refs=sorted(set(evidence_refs)),
        )

    def detect_injection(self, message: str) -> PromptInjectionDetection:
        return self.injection_detector.detect(message)

    @staticmethod
    def _missing_required_evidence(inputs: QaValidationInputs) -> list[str]:
        missing: list[str] = []
        for evidence in inputs.policy_output.required_evidence:
            if evidence == "delivery_proof":
                proof_from_facts = inputs.facts.get("delivery_proof_available") is True
                proof_tool = (
                    inputs.tool_results.get("get_delivery_proof", {}).get("available") is True
                )
                if not (proof_from_facts or proof_tool):
                    missing.append("delivery_proof")
                continue
            if evidence == "risk_score":
                if "risk_score" not in inputs.facts:
                    missing.append("risk_score")
                continue
            if evidence == "identity_verified":
                if not inputs.verification_passed:
                    missing.append("identity_verified")
                continue
            # Preserve unknown requirements as explicit violations instead of silently passing.
            if evidence not in inputs.facts:
                missing.append(evidence)
        return missing
