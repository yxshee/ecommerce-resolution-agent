from __future__ import annotations

import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ecom_resolution_agent.actions import ActionCapsService, ActionExecutor
from ecom_resolution_agent.agents import (
    DeterministicActionsAgent,
    DeterministicDecisionAgent,
    DeterministicQaAgent,
    DeterministicRiskAgent,
    DeterministicTriageAgent,
)
from ecom_resolution_agent.approvals import ApprovalService
from ecom_resolution_agent.audit import RunArtifactWriter
from ecom_resolution_agent.orchestration.graph import EcommerceOrchestrator
from ecom_resolution_agent.orchestration.nodes.common import OrchestrationDeps
from ecom_resolution_agent.orchestration.state import CaseState
from ecom_resolution_agent.policy import PolicyService
from ecom_resolution_agent.reporting import DeterministicReportAgent
from ecom_resolution_agent.schemas.actions import ActionExecutionResult
from ecom_resolution_agent.schemas.agent_outputs import (
    QaVerificationResult,
    ReportOutput,
    ResolutionDecision,
)
from ecom_resolution_agent.schemas.audit import AuditEventRecord
from ecom_resolution_agent.tools import InMemoryAuditSink, ToolExecutor
from ecom_resolution_agent.tools.mock import MockStore
from ecom_resolution_agent.tools.registry import build_mock_tool_registry

DEFAULT_FIXTURE_PATH = Path("tests/fixtures/mock_data/store_fixture.json")


@dataclass
class SimulationRunResult:
    run_id: str
    case_state: CaseState
    decision: ResolutionDecision
    qa_result: QaVerificationResult
    action_result: ActionExecutionResult | None
    report_output: ReportOutput
    audit_events: list[AuditEventRecord]
    artifact_dir: Path

    def summary(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "status": self.case_state.status,
            "issue_type": self.case_state.issue_type,
            "selected_action": self.decision.selected_action,
            "qa_approved": self.qa_result.approved,
            "qa_escalate_to_human": self.qa_result.escalate_to_human,
            "action_status": self.action_result.status if self.action_result else None,
            "artifact_dir": str(self.artifact_dir),
        }


class SimulationPipeline:
    def __init__(
        self,
        *,
        store: MockStore,
        artifact_writer: RunArtifactWriter | None = None,
    ) -> None:
        self.store = store
        self.audit_sink = InMemoryAuditSink()
        self.tool_executor = ToolExecutor(
            build_mock_tool_registry(self.store),
            audit_sink=self.audit_sink,
        )
        self.policy_service = PolicyService()
        self.approval_service = ApprovalService()
        self.caps_service = ActionCapsService()
        self.triage_agent = DeterministicTriageAgent()
        self.risk_agent = DeterministicRiskAgent()
        self.decision_agent = DeterministicDecisionAgent()
        self.qa_agent = DeterministicQaAgent()
        self.actions_agent = DeterministicActionsAgent(
            ActionExecutor(
                self.tool_executor,
                caps_service=self.caps_service,
                approval_service=self.approval_service,
            )
        )
        self.report_agent = DeterministicReportAgent(self.tool_executor)
        self.artifact_writer = artifact_writer or RunArtifactWriter()

    def run_case(
        self,
        *,
        ticket: dict[str, Any],
        run_id: str | None = None,
        simulation_mode: bool = True,
        artifact_ref_prefix: str = "artifacts/runs",
    ) -> SimulationRunResult:
        resolved_run_id = run_id or f"run_{uuid.uuid4().hex[:12]}"
        deps = OrchestrationDeps(
            tool_executor=self.tool_executor,
            policy_service=self.policy_service,
            triage_agent=self.triage_agent,
            risk_agent=self.risk_agent,
            approval_service=self.approval_service,
            caps_service=self.caps_service,
        )
        orchestrator = EcommerceOrchestrator(deps)
        initial_state = CaseState(
            run_id=resolved_run_id,
            ticket=ticket,
            simulation_mode=simulation_mode,
        )
        case_state = orchestrator.run(initial_state)

        decision = self.decision_agent.decide(case_state)
        qa_result = self._qa_review(case_state=case_state, decision=decision)
        action_result = self._execute_selected_action(
            case_state=case_state,
            decision=decision,
            qa_result=qa_result,
        )

        audit_ref = f"{artifact_ref_prefix}/{resolved_run_id}"
        report_output = self.report_agent.generate_report(
            ticket=ticket,
            decision=decision,
            action_result=action_result,
            qa_result=qa_result,
            facts=case_state.facts,
            audit_events=list(self.audit_sink.events),
            audit_bundle_refs=[audit_ref],
            run_id=resolved_run_id,
        )
        self.report_agent.publish_report(
            run_id=resolved_run_id,
            ticket_id=str(ticket.get("ticket_id", "")),
            report_output=report_output,
            simulation_mode=simulation_mode,
        )

        artifact_dir = self.artifact_writer.write_bundle(
            run_id=resolved_run_id,
            run_config={
                "run_id": resolved_run_id,
                "simulation_mode": simulation_mode,
                "ticket_id": ticket.get("ticket_id"),
                "customer_id": ticket.get("customer_id"),
                "order_id": ticket.get("order_id"),
            },
            audit_events=list(self.audit_sink.events),
            decision={
                "decision": decision.model_dump(mode="json"),
                "qa_result": qa_result.model_dump(mode="json"),
                "action_result": (
                    action_result.model_dump(mode="json") if action_result is not None else None
                ),
            },
            report_output=report_output,
        )

        return SimulationRunResult(
            run_id=resolved_run_id,
            case_state=case_state,
            decision=decision,
            qa_result=qa_result,
            action_result=action_result,
            report_output=report_output,
            audit_events=list(self.audit_sink.events),
            artifact_dir=artifact_dir,
        )

    def _qa_review(
        self,
        *,
        case_state: CaseState,
        decision: ResolutionDecision,
    ) -> QaVerificationResult:
        if case_state.policy_output is None or case_state.risk_output is None:
            return QaVerificationResult(
                approved=False,
                violations=["missing_policy_or_risk"],
                injection_detected=False,
                escalate_to_human=True,
                evidence_refs=[],
            )
        return self.qa_agent.review(
            customer_message=str(
                case_state.ticket.get("customer_message") or case_state.customer_message or ""
            ),
            verification_passed=case_state.verification_passed,
            policy_output=case_state.policy_output,
            risk_output=case_state.risk_output,
            decision=decision,
            facts=case_state.facts,
            tool_results=case_state.tool_results,
        )

    def _execute_selected_action(
        self,
        *,
        case_state: CaseState,
        decision: ResolutionDecision,
        qa_result: QaVerificationResult,
    ) -> ActionExecutionResult | None:
        if not qa_result.approved:
            return None
        if decision.selected_action == "escalate_human":
            return None
        if case_state.policy_version is None:
            return None
        if case_state.customer_id is None or case_state.order_id is None:
            return None

        order = case_state.facts.get("order", {})
        order_total = None
        currency = None
        if isinstance(order, dict):
            total = order.get("total", {})
            if isinstance(total, dict):
                amount_raw = total.get("amount_cents")
                if isinstance(amount_raw, int):
                    order_total = amount_raw
                currency_raw = total.get("currency")
                if isinstance(currency_raw, str):
                    currency = currency_raw

        item_id = None
        item_sku = None
        order_items = case_state.facts.get("order_items")
        if isinstance(order_items, list) and order_items:
            first_item = order_items[0]
            if isinstance(first_item, dict):
                if isinstance(first_item.get("item_id"), str):
                    item_id = str(first_item["item_id"])
                if isinstance(first_item.get("sku"), str):
                    item_sku = str(first_item["sku"])
        ticket_item_id = case_state.ticket.get("item_id")
        if item_id is None and isinstance(ticket_item_id, str):
            item_id = ticket_item_id

        amount_cents = None
        if decision.selected_action == "refund_partial":
            requested = case_state.ticket.get("requested_refund_amount_cents")
            if isinstance(requested, int):
                amount_cents = requested
            elif isinstance(order_total, int):
                amount_cents = min(order_total, 1000)
        elif decision.selected_action == "refund_full":
            amount_cents = order_total

        return self.actions_agent.execute_resolution(
            run_id=case_state.run_id,
            action_type=decision.selected_action,
            customer_id=case_state.customer_id,
            order_id=case_state.order_id,
            policy_version=case_state.policy_version,
            item_id=item_id,
            item_sku=item_sku,
            amount_cents=amount_cents,
            currency=currency,
            simulation_mode=case_state.simulation_mode,
            approval_required=False,
            approval_token=None,
            order_total_cents=order_total,
            reason="policy_resolution",
        )


def build_simulation_pipeline(
    *,
    fixture_path: str | Path = DEFAULT_FIXTURE_PATH,
    artifact_writer: RunArtifactWriter | None = None,
) -> SimulationPipeline:
    store = MockStore.from_file(fixture_path)
    return SimulationPipeline(store=store, artifact_writer=artifact_writer)
