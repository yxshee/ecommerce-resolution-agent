from __future__ import annotations

from typing import Any

from pydantic import Field

from ecom_resolution_agent.schemas.agent_outputs import PolicyOutput, RiskOutput, TriageOutput
from ecom_resolution_agent.schemas.base import StrictModel

ALL_STATES = [
    "intake",
    "verify_identity",
    "gather_facts",
    "classify_issue",
    "policy_lookup",
    "risk_assessment",
    "propose_resolution",
    "verify_resolution",
    "execute_or_escalate",
    "finalize_report",
    "persist_audit",
]

END_ROUTE = "__end__"


class CaseState(StrictModel):
    run_id: str
    ticket: dict[str, Any]
    customer_message: str = ""
    simulation_mode: bool = True

    current_state: str | None = None
    next_state: str | None = None
    status: str = "pending"

    customer_id: str | None = None
    order_id: str | None = None
    issue_type: str | None = None
    policy_version: str | None = None
    approval_task_id: str | None = None
    approval_token: str | None = None

    verification_passed: bool = False
    verification_result: dict[str, Any] | None = None
    requested_verification: bool = False

    triage_output: TriageOutput | None = None
    policy_output: PolicyOutput | None = None
    risk_output: RiskOutput | None = None

    facts: dict[str, Any] = Field(default_factory=dict)
    tool_results: dict[str, dict[str, Any]] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)

    def as_graph_state(self) -> dict[str, Any]:
        return self.model_dump(mode="json")

    @classmethod
    def from_graph_state(cls, payload: dict[str, Any]) -> CaseState:
        return cls.model_validate(payload)
