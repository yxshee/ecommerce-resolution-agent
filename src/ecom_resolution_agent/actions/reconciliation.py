from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ecom_resolution_agent.schemas.tool_envelopes import ToolCallContext, ToolCallResult
from ecom_resolution_agent.tools.executor import ToolExecutor


@dataclass(frozen=True)
class RefundReconciliationResult:
    resolved: bool
    status: str
    refund_id: str | None = None
    external_reference: str | None = None


def parse_timeout_refund_id(error_message: str) -> str | None:
    marker = "timeout_after_creation:"
    if marker not in error_message:
        return None
    return error_message.split(marker, 1)[1].strip() or None


def reconcile_refund_after_timeout(
    tool_executor: ToolExecutor,
    *,
    context: ToolCallContext,
    timeout_error_message: str,
) -> RefundReconciliationResult:
    refund_id = parse_timeout_refund_id(timeout_error_message)
    if refund_id is None:
        return RefundReconciliationResult(resolved=False, status="unresolved_timeout")

    status_result: ToolCallResult[dict[str, Any]] = tool_executor.invoke(
        "get_refund_status",
        {"refund_id": refund_id},
        context=context,
    )
    if not status_result.ok or status_result.data is None:
        return RefundReconciliationResult(resolved=False, status="status_check_failed")

    return RefundReconciliationResult(
        resolved=True,
        status=str(status_result.data.get("status", "unknown")),
        refund_id=refund_id,
        external_reference=None,
    )
