from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Any

from ecom_resolution_agent.schemas.actions import ActionExecutionResult
from ecom_resolution_agent.schemas.audit import AuditEventRecord

ACTION_SUCCESS_TOOL_MAP: dict[str, set[str]] = {
    "refund_partial": {"issue_refund", "get_refund_status"},
    "refund_full": {"issue_refund", "get_refund_status"},
    "replacement_reship": {"reserve_stock"},
    "return_initiation": {"create_return"},
}

FALLBACK_ACTION_TOOLS = {
    "create_return",
    "create_label",
    "schedule_pickup",
    "issue_refund",
    "reserve_stock",
    "get_refund_status",
}


class AuditInvariantViolation(ValueError):
    """Raised when a report/action claim is not supported by the audit trail."""


def has_matching_action_success_audit_event(
    *,
    action_result: ActionExecutionResult | dict[str, Any] | None,
    audit_events: Sequence[AuditEventRecord | dict[str, Any]],
) -> bool:
    """Return True when a success-like action result is backed by a matching audit event.

    Non-success action results return True because the invariant is only about success claims.
    """

    normalized = _normalize_action_result(action_result)
    if normalized is None:
        return True
    if not _is_success_claim(normalized):
        return True

    expected_tools = ACTION_SUCCESS_TOOL_MAP.get(normalized.action_type, FALLBACK_ACTION_TOOLS)
    for event in _iter_events(audit_events):
        if event.run_id != normalized.run_id:
            continue
        if event.decision_note != "success":
            continue
        if event.tool_name not in expected_tools:
            continue
        if _matches_external_reference(normalized.external_reference, event):
            return True
    return False


def assert_action_success_claim_backed_by_audit(
    *,
    action_result: ActionExecutionResult | dict[str, Any] | None,
    audit_events: Sequence[AuditEventRecord | dict[str, Any]],
) -> None:
    normalized = _normalize_action_result(action_result)
    if normalized is None or not _is_success_claim(normalized):
        return
    if has_matching_action_success_audit_event(action_result=normalized, audit_events=audit_events):
        return

    expected_tools = sorted(
        ACTION_SUCCESS_TOOL_MAP.get(normalized.action_type, FALLBACK_ACTION_TOOLS)
    )
    raise AuditInvariantViolation(
        "action success claim is not backed by a matching success audit event "
        f"(run_id={normalized.run_id!r}, action_type={normalized.action_type!r}, "
        f"expected_tools={expected_tools})"
    )


def _normalize_action_result(
    action_result: ActionExecutionResult | dict[str, Any] | None,
) -> ActionExecutionResult | None:
    if action_result is None:
        return None
    if isinstance(action_result, ActionExecutionResult):
        return action_result
    return ActionExecutionResult.model_validate(action_result)


def _iter_events(
    audit_events: Iterable[AuditEventRecord | dict[str, Any]],
) -> Iterable[AuditEventRecord]:
    for event in audit_events:
        if isinstance(event, AuditEventRecord):
            yield event
        else:
            yield AuditEventRecord.model_validate(event)


def _is_success_claim(action_result: ActionExecutionResult) -> bool:
    if action_result.error_code is not None:
        return False
    status = action_result.status.strip().lower()
    if status in {"", "failed"}:
        return False
    # "duplicate_replay" is a replay/receipt outcome, not a fresh action-success claim.
    if status == "duplicate_replay":
        return False
    return True


def _matches_external_reference(
    external_reference: str | None,
    event: AuditEventRecord,
) -> bool:
    if not external_reference:
        return True
    payload = event.tool_output_redacted_json or {}
    for candidate in _iter_strings(payload):
        if candidate == external_reference:
            return True
    return False


def _iter_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
        return
    if isinstance(value, dict):
        for nested in value.values():
            yield from _iter_strings(nested)
        return
    if isinstance(value, list):
        for nested in value:
            yield from _iter_strings(nested)
