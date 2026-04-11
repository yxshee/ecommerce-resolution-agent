from __future__ import annotations

from typing import Any

from pydantic import Field

from ecom_resolution_agent.schemas.base import StrictModel


class TriageOutput(StrictModel):
    issue_type: str
    missing_info_list: list[str] = Field(default_factory=list)
    required_tools_list: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)


class PolicyOutput(StrictModel):
    policy_version: str
    allowed_actions: list[str] = Field(default_factory=list)
    constraints: dict[str, Any] = Field(default_factory=dict)
    required_evidence: list[str] = Field(default_factory=list)
    approval_required: bool


class RiskOutput(StrictModel):
    risk_score: float = Field(ge=0.0, le=1.0)
    risk_reasons: list[str] = Field(default_factory=list)
    approval_required: bool
    blocked_actions: list[str] = Field(default_factory=list)


class ResolutionDecision(StrictModel):
    selected_action: str
    rationale: str
    evidence_refs: list[str] = Field(default_factory=list)
    customer_message_draft: str
    internal_note_draft: str


class QaVerificationResult(StrictModel):
    approved: bool
    violations: list[str] = Field(default_factory=list)
    injection_detected: bool = False
    escalate_to_human: bool = False
    evidence_refs: list[str] = Field(default_factory=list)


class ReportOutput(StrictModel):
    customer_message_markdown: str
    internal_summary_markdown: str
    audit_bundle_refs: list[str] = Field(default_factory=list)
