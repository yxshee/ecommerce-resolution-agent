from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from ecom_resolution_agent.audit.invariants import assert_action_success_claim_backed_by_audit
from ecom_resolution_agent.schemas.actions import ActionExecutionResult
from ecom_resolution_agent.schemas.agent_outputs import (
    QaVerificationResult,
    ReportOutput,
    ResolutionDecision,
)
from ecom_resolution_agent.schemas.audit import AuditEventRecord
from ecom_resolution_agent.schemas.tool_envelopes import ToolCallContext, ToolCallResult
from ecom_resolution_agent.security.redaction import Redactor
from ecom_resolution_agent.tools.executor import ToolExecutor


@dataclass
class ReportPublicationResult:
    report_output: ReportOutput
    internal_note_tool_result: ToolCallResult[dict[str, Any]]
    ticket_update_tool_result: ToolCallResult[dict[str, Any]]


class DeterministicReportAgent:
    def __init__(
        self,
        tool_executor: ToolExecutor,
        *,
        redactor: Redactor | None = None,
        resolved_ticket_status: str = "resolved",
        review_ticket_status: str = "pending_manual_review",
    ) -> None:
        self.tool_executor = tool_executor
        self.redactor = redactor or Redactor()
        self.resolved_ticket_status = resolved_ticket_status
        self.review_ticket_status = review_ticket_status
        self.last_publication: ReportPublicationResult | None = None

    def build_report_output(
        self,
        *,
        ticket: dict[str, Any],
        decision: ResolutionDecision | dict[str, Any],
        action_result: ActionExecutionResult | dict[str, Any] | None = None,
        qa_result: QaVerificationResult | dict[str, Any] | None = None,
        facts: dict[str, Any] | None = None,
        audit_events: list[AuditEventRecord | dict[str, Any]] | None = None,
        audit_bundle_refs: list[str] | None = None,
        run_id: str | None = None,
    ) -> ReportOutput:
        normalized_decision = (
            decision
            if isinstance(decision, ResolutionDecision)
            else ResolutionDecision.model_validate(decision)
        )
        normalized_action = self._normalize_action_result(action_result)
        normalized_qa = self._normalize_qa_result(qa_result)
        audit_event_list = audit_events or []

        if normalized_action is not None:
            assert_action_success_claim_backed_by_audit(
                action_result=normalized_action,
                audit_events=audit_event_list,
            )

        effective_run_id = (
            run_id
            or (normalized_action.run_id if normalized_action is not None else None)
            or self._infer_run_id(audit_event_list)
            or "unknown_run"
        )
        refs = list(audit_bundle_refs or [])
        customer_message = self._build_customer_markdown(
            ticket=ticket,
            decision=normalized_decision,
            action_result=normalized_action,
        )
        internal_summary = self._build_internal_markdown(
            run_id=effective_run_id,
            ticket=ticket,
            decision=normalized_decision,
            action_result=normalized_action,
            qa_result=normalized_qa,
            facts=facts or {},
            audit_bundle_refs=refs,
        )
        return ReportOutput(
            customer_message_markdown=customer_message,
            internal_summary_markdown=internal_summary,
            audit_bundle_refs=refs,
        )

    def publish_report(
        self,
        *,
        run_id: str,
        ticket_id: str,
        report_output: ReportOutput | dict[str, Any],
        simulation_mode: bool = True,
        ticket_status: str | None = None,
    ) -> ReportPublicationResult:
        normalized_report = (
            report_output
            if isinstance(report_output, ReportOutput)
            else ReportOutput.model_validate(report_output)
        )
        context = ToolCallContext(
            run_id=run_id,
            actor_agent="report",
            simulation_mode=simulation_mode,
        )
        final_status = ticket_status or self._default_ticket_status_for_report(normalized_report)

        note_result = self.tool_executor.invoke(
            "add_internal_note",
            {
                "ticket_id": ticket_id,
                "note_markdown": normalized_report.internal_summary_markdown,
            },
            context=context,
        )
        update_result = self.tool_executor.invoke(
            "update_ticket",
            {
                "ticket_id": ticket_id,
                "status": final_status,
            },
            context=context,
        )

        if not note_result.ok:
            message = note_result.error.message if note_result.error else "add_internal_note failed"
            raise RuntimeError(message)
        if not update_result.ok:
            message = update_result.error.message if update_result.error else "update_ticket failed"
            raise RuntimeError(message)

        return ReportPublicationResult(
            report_output=normalized_report,
            internal_note_tool_result=note_result,
            ticket_update_tool_result=update_result,
        )

    def generate_and_publish(
        self,
        *,
        run_id: str,
        ticket: dict[str, Any],
        decision: ResolutionDecision | dict[str, Any],
        action_result: ActionExecutionResult | dict[str, Any] | None = None,
        qa_result: QaVerificationResult | dict[str, Any] | None = None,
        facts: dict[str, Any] | None = None,
        audit_events: list[AuditEventRecord | dict[str, Any]] | None = None,
        audit_bundle_refs: list[str] | None = None,
        simulation_mode: bool = True,
        ticket_status: str | None = None,
    ) -> ReportPublicationResult:
        ticket_id = str(ticket.get("ticket_id", "") or "")
        if not ticket_id:
            raise ValueError("ticket must include ticket_id")

        report_output = self.build_report_output(
            ticket=ticket,
            decision=decision,
            action_result=action_result,
            qa_result=qa_result,
            facts=facts,
            audit_events=audit_events,
            audit_bundle_refs=audit_bundle_refs,
            run_id=run_id,
        )
        publication = self.publish_report(
            run_id=run_id,
            ticket_id=ticket_id,
            report_output=report_output,
            simulation_mode=simulation_mode,
            ticket_status=ticket_status,
        )
        self.last_publication = publication
        return publication

    def finalize_report(self, **kwargs: Any) -> ReportOutput:
        return self.generate_and_publish(**kwargs).report_output

    def run(self, **kwargs: Any) -> ReportOutput:
        return self.finalize_report(**kwargs)

    def generate_report(self, **kwargs: Any) -> ReportOutput:
        return self.build_report_output(**kwargs)

    def _build_customer_markdown(
        self,
        *,
        ticket: dict[str, Any],
        decision: ResolutionDecision,
        action_result: ActionExecutionResult | None,
    ) -> str:
        ticket_id = str(ticket.get("ticket_id", "unknown_ticket"))
        order_id = ticket.get("order_id")
        order_line = f"- Order ID: `{order_id}`\n" if order_id else ""
        status_line = ""
        if action_result is not None:
            status_line = f"- Action status: `{action_result.status}`\n"
        return (
            "# Resolution Update\n\n"
            f"- Ticket ID: `{ticket_id}`\n"
            f"{order_line}"
            f"- Selected action: `{decision.selected_action}`\n"
            f"{status_line}\n"
            "## Message\n"
            f"{decision.customer_message_draft.strip()}\n"
        )

    def _build_internal_markdown(
        self,
        *,
        run_id: str,
        ticket: dict[str, Any],
        decision: ResolutionDecision,
        action_result: ActionExecutionResult | None,
        qa_result: QaVerificationResult | None,
        facts: dict[str, Any],
        audit_bundle_refs: list[str],
    ) -> str:
        ticket_id = str(ticket.get("ticket_id", "unknown_ticket"))
        action_lines = "- Action execution: `not_provided`\n"
        if action_result is not None:
            action_lines = (
                f"- Action execution status: `{action_result.status}`\n"
                f"- Action external reference: `{action_result.external_reference or 'none'}`\n"
                f"- Action error code: `{action_result.error_code or 'none'}`\n"
            )
        qa_lines = "- QA result: `not_provided`\n"
        if qa_result is not None:
            violations = ", ".join(qa_result.violations) if qa_result.violations else "none"
            qa_lines = (
                f"- QA approved: `{qa_result.approved}`\n"
                f"- QA escalate to human: `{qa_result.escalate_to_human}`\n"
                f"- QA violations: `{violations}`\n"
            )
        refs = "\n".join(f"- `{ref}`" for ref in audit_bundle_refs) or "- none"
        redacted_ticket_snapshot = self.redactor.redact_value(
            {
                "ticket_id": ticket.get("ticket_id"),
                "customer_id": ticket.get("customer_id"),
                "order_id": ticket.get("order_id"),
                "status": ticket.get("status"),
                "issue_type": ticket.get("issue_type"),
                "customer_message": ticket.get("customer_message"),
            }
        )
        redacted_facts = self.redactor.redact_value(facts)
        facts_json = json.dumps(redacted_facts, indent=2, sort_keys=True, default=str)
        ticket_json = json.dumps(redacted_ticket_snapshot, indent=2, sort_keys=True, default=str)

        internal_note_draft = decision.internal_note_draft.strip()
        rationale = decision.rationale.strip()
        evidence = "\n".join(f"- `{ref}`" for ref in decision.evidence_refs) or "- none"
        return (
            "# Internal Resolution Summary\n\n"
            f"- Run ID: `{run_id}`\n"
            f"- Ticket ID: `{ticket_id}`\n"
            f"- Selected action: `{decision.selected_action}`\n"
            f"{action_lines}"
            f"{qa_lines}\n"
            "## Rationale\n"
            f"{rationale}\n\n"
            "## Evidence Refs\n"
            f"{evidence}\n\n"
            "## Internal Note Draft\n"
            f"{internal_note_draft}\n\n"
            "## Redacted Ticket Snapshot\n"
            f"```json\n{ticket_json}\n```\n\n"
            "## Redacted Facts Snapshot\n"
            f"```json\n{facts_json}\n```\n\n"
            "## Audit Bundle References\n"
            f"{refs}\n"
        )

    def _default_ticket_status_for_report(self, report: ReportOutput) -> str:
        lower = report.internal_summary_markdown.lower()
        qa_failed = "qa approved: `false`" in lower
        action_error_present = (
            "action error code: `" in lower and "action error code: `none`" not in lower
        )
        if qa_failed or action_error_present:
            return self.review_ticket_status
        return self.resolved_ticket_status

    def _infer_run_id(self, audit_events: list[AuditEventRecord | dict[str, Any]]) -> str | None:
        if not audit_events:
            return None
        first = audit_events[0]
        if isinstance(first, AuditEventRecord):
            return first.run_id
        run_id = first.get("run_id")
        return str(run_id) if isinstance(run_id, str) else None

    def _normalize_action_result(
        self,
        action_result: ActionExecutionResult | dict[str, Any] | None,
    ) -> ActionExecutionResult | None:
        if action_result is None:
            return None
        if isinstance(action_result, ActionExecutionResult):
            return action_result
        return ActionExecutionResult.model_validate(action_result)

    def _normalize_qa_result(
        self,
        qa_result: QaVerificationResult | dict[str, Any] | None,
    ) -> QaVerificationResult | None:
        if qa_result is None:
            return None
        if isinstance(qa_result, QaVerificationResult):
            return qa_result
        return QaVerificationResult.model_validate(qa_result)
