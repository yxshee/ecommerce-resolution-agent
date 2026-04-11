from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Protocol

from ecom_resolution_agent.schemas.audit import AuditEventRecord
from ecom_resolution_agent.schemas.tool_envelopes import ToolCallContext, ToolCallResult, ToolError
from ecom_resolution_agent.security.redaction import Redactor
from ecom_resolution_agent.tools.registry import RegisteredTool, ToolRegistry


class AuditSinkProtocol(Protocol):
    def record(self, event: AuditEventRecord) -> None: ...


@dataclass
class InMemoryAuditSink(AuditSinkProtocol):
    events: list[AuditEventRecord] = field(default_factory=list)

    def record(self, event: AuditEventRecord) -> None:
        self.events.append(event)


@dataclass(frozen=True)
class ToolExecutorConfig:
    enable_real_actions: bool = False


DEFAULT_CAPABILITY_MATRIX: dict[str, set[str]] = {
    "triage": {
        "verify_customer",
        "get_customer_profile",
        "get_order",
        "get_order_items",
        "get_fulfillment_status",
        "get_tracking_events",
        "get_delivery_proof",
        "get_policy_version",
        "get_policy_rules",
        "search_kb_articles",
    },
    "policy": {"get_policy_version", "get_policy_rules", "search_kb_articles"},
    "risk": {
        "get_customer_profile",
        "get_order",
        "get_order_items",
        "get_fulfillment_status",
        "get_tracking_events",
        "get_delivery_proof",
    },
    "actions": {
        "create_return",
        "create_label",
        "schedule_pickup",
        "issue_refund",
        "get_refund_status",
        "check_stock",
        "reserve_stock",
        "update_ticket",
        "add_internal_note",
    },
    "qa": {
        "get_customer_profile",
        "get_order",
        "get_order_items",
        "get_fulfillment_status",
        "get_tracking_events",
        "get_delivery_proof",
        "get_policy_version",
        "get_policy_rules",
        "search_kb_articles",
        "get_refund_status",
    },
    "report": {"update_ticket", "add_internal_note", "search_kb_articles"},
    "system": {"*"},
}


class ToolExecutor:
    def __init__(
        self,
        registry: ToolRegistry,
        *,
        redactor: Redactor | None = None,
        audit_sink: AuditSinkProtocol | None = None,
        config: ToolExecutorConfig | None = None,
        capability_matrix: dict[str, set[str]] | None = None,
    ) -> None:
        self.registry = registry
        self.redactor = redactor or Redactor()
        self.audit_sink = audit_sink or InMemoryAuditSink()
        self.config = config or ToolExecutorConfig()
        self.capability_matrix = capability_matrix or DEFAULT_CAPABILITY_MATRIX

    def invoke(
        self,
        tool_name: str,
        tool_input: dict[str, Any] | Any,
        *,
        context: ToolCallContext,
        idempotency_key: str | None = None,
    ) -> ToolCallResult[dict[str, Any]]:
        started = time.perf_counter()
        timestamp = datetime.now(UTC)

        try:
            spec = self.registry.get(tool_name)
        except KeyError:
            error = ToolError(code="tool_not_found", message=f"Unknown tool: {tool_name}")
            result = ToolCallResult[dict[str, Any]](
                tool_name=tool_name,
                ok=False,
                data=None,
                error=error,
                latency_ms=self._latency_ms(started),
                simulated=context.simulation_mode,
            )
            self._record_audit(
                timestamp=timestamp,
                context=context,
                tool_name=tool_name,
                tool_input=tool_input,
                tool_output={"error": error.model_dump()},
                decision_note="tool_not_found",
            )
            return result

        if not self._is_allowed(context.actor_agent, spec):
            error = ToolError(code="permission_denied", message="Actor agent cannot call tool")
            result = ToolCallResult[dict[str, Any]](
                tool_name=tool_name,
                ok=False,
                data=None,
                error=error,
                latency_ms=self._latency_ms(started),
                simulated=context.simulation_mode,
            )
            self._record_audit(
                timestamp=timestamp,
                context=context,
                tool_name=tool_name,
                tool_input=tool_input,
                tool_output={"error": error.model_dump()},
                decision_note="permission_denied",
            )
            return result

        if (
            spec.is_action_tool
            and not context.simulation_mode
            and not self.config.enable_real_actions
        ):
            error = ToolError(
                code="real_actions_disabled",
                message="Real action execution is disabled",
            )
            result = ToolCallResult[dict[str, Any]](
                tool_name=tool_name,
                ok=False,
                data=None,
                error=error,
                latency_ms=self._latency_ms(started),
                simulated=context.simulation_mode,
            )
            self._record_audit(
                timestamp=timestamp,
                context=context,
                tool_name=tool_name,
                tool_input=tool_input,
                tool_output={"error": error.model_dump()},
                decision_note="real_actions_disabled",
            )
            return result

        try:
            request_obj = spec.request_model.model_validate(tool_input)
            raw_response = spec.handler(request_obj)
            response_obj = spec.response_model.model_validate(raw_response)
            response_data = response_obj.model_dump(mode="json")
            result = ToolCallResult[dict[str, Any]](
                tool_name=tool_name,
                ok=True,
                data=response_data,
                error=None,
                external_reference=self._external_reference_from_response(response_data),
                latency_ms=self._latency_ms(started),
                simulated=context.simulation_mode,
            )
            self._record_audit(
                timestamp=timestamp,
                context=context,
                tool_name=tool_name,
                tool_input=request_obj.model_dump(mode="json"),
                tool_output=response_data,
                decision_note="success",
            )
            return result
        except Exception as exc:  # noqa: BLE001 - convert to structured tool error
            error = ToolError(
                code="tool_execution_error",
                message=str(exc),
                retryable=False,
            )
            result = ToolCallResult[dict[str, Any]](
                tool_name=tool_name,
                ok=False,
                data=None,
                error=error,
                latency_ms=self._latency_ms(started),
                simulated=context.simulation_mode,
            )
            self._record_audit(
                timestamp=timestamp,
                context=context,
                tool_name=tool_name,
                tool_input=tool_input,
                tool_output={"error": error.model_dump()},
                decision_note="tool_execution_error",
            )
            return result

    def _is_allowed(self, actor_agent: str, spec: RegisteredTool) -> bool:
        allowed = self.capability_matrix.get(actor_agent, set())
        return "*" in allowed or spec.name in allowed

    def _record_audit(
        self,
        *,
        timestamp: datetime,
        context: ToolCallContext,
        tool_name: str,
        tool_input: Any,
        tool_output: Any,
        decision_note: str,
    ) -> None:
        input_payload = tool_input if isinstance(tool_input, dict) else {"value": str(tool_input)}
        output_payload = (
            tool_output if isinstance(tool_output, dict) else {"value": str(tool_output)}
        )
        event = AuditEventRecord(
            event_id=f"evt_{uuid.uuid4().hex[:16]}",
            run_id=context.run_id,
            timestamp=timestamp,
            actor_agent=context.actor_agent,
            tool_name=tool_name,
            tool_input_redacted_json=self.redactor.redact_value(input_payload),
            tool_output_redacted_json=self.redactor.redact_value(output_payload),
            decision_note=decision_note,
        )
        self.audit_sink.record(event)

    @staticmethod
    def _external_reference_from_response(payload: dict[str, Any]) -> str | None:
        external_reference = payload.get("external_reference")
        if isinstance(external_reference, str):
            return external_reference
        return None

    @staticmethod
    def _latency_ms(started: float) -> int:
        return max(0, int((time.perf_counter() - started) * 1000))
