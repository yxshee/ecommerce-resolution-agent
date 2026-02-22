from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ecom_resolution_agent.qa import QaValidationInputs, QaValidator
from ecom_resolution_agent.schemas.agent_outputs import (
    PolicyOutput,
    QaVerificationResult,
    ResolutionDecision,
    RiskOutput,
)
from ecom_resolution_agent.security.redaction import Redactor


@dataclass
class DeterministicQaAgent:
    validator: QaValidator = QaValidator()
    redactor: Redactor = Redactor()

    def review(
        self,
        *,
        customer_message: str,
        verification_passed: bool,
        policy_output: PolicyOutput,
        risk_output: RiskOutput,
        decision: ResolutionDecision,
        facts: dict[str, Any],
        tool_results: dict[str, dict[str, Any]],
    ) -> QaVerificationResult:
        return self.validator.validate(
            QaValidationInputs(
                customer_message=customer_message,
                verification_passed=verification_passed,
                policy_output=policy_output,
                risk_output=risk_output,
                decision=decision,
                facts=facts,
                tool_results=tool_results,
            )
        )

    def build_internal_note_markdown(
        self,
        *,
        qa_result: QaVerificationResult,
        customer_message: str,
    ) -> str:
        redacted_message = self.redactor.redact_text(customer_message)
        violations = "\n".join(f"- `{v}`" for v in qa_result.violations) or "- none"
        evidence = "\n".join(f"- `{ref}`" for ref in qa_result.evidence_refs) or "- none"
        return (
            "# QA Verification Summary\n\n"
            f"- Approved: `{qa_result.approved}`\n"
            f"- Injection detected: `{qa_result.injection_detected}`\n"
            f"- Escalate to human: `{qa_result.escalate_to_human}`\n\n"
            "## Violations\n"
            f"{violations}\n\n"
            "## Evidence Refs\n"
            f"{evidence}\n\n"
            "## Redacted Customer Message\n"
            f"> {redacted_message}\n"
        )
