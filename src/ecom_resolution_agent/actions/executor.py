from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, date, datetime

from ecom_resolution_agent.actions.caps import ActionCapsService
from ecom_resolution_agent.actions.reconciliation import reconcile_refund_after_timeout
from ecom_resolution_agent.approvals import ApprovalService
from ecom_resolution_agent.schemas.actions import ActionExecutionRequest, ActionExecutionResult
from ecom_resolution_agent.schemas.tool_envelopes import ToolCallContext
from ecom_resolution_agent.tools.executor import ToolExecutor

REFUND_ACTIONS = {"refund_partial", "refund_full"}


@dataclass
class StoredActionRecord:
    request: ActionExecutionRequest
    result: ActionExecutionResult
    created_at: datetime


@dataclass
class InMemoryActionLedger:
    by_idempotency_key: dict[str, StoredActionRecord] = field(default_factory=dict)
    by_run_id: dict[str, list[StoredActionRecord]] = field(default_factory=dict)
    by_customer_refund_day: dict[tuple[str, date], list[StoredActionRecord]] = field(
        default_factory=dict
    )

    def get_duplicate(self, idempotency_key: str) -> StoredActionRecord | None:
        return self.by_idempotency_key.get(idempotency_key)

    def store(self, record: StoredActionRecord) -> None:
        self.by_idempotency_key[record.request.idempotency_key] = record
        self.by_run_id.setdefault(record.request.run_id, []).append(record)
        if record.request.action_type in REFUND_ACTIONS:
            key = (record.request.customer_id, record.created_at.date())
            self.by_customer_refund_day.setdefault(key, []).append(record)

    def actions_this_run(self, run_id: str) -> int:
        return len(self.by_run_id.get(run_id, []))

    def refunds_for_customer_today(self, customer_id: str, today: date) -> int:
        return len(self.by_customer_refund_day.get((customer_id, today), []))


class ActionExecutor:
    def __init__(
        self,
        tool_executor: ToolExecutor,
        *,
        caps_service: ActionCapsService,
        approval_service: ApprovalService,
        ledger: InMemoryActionLedger | None = None,
    ) -> None:
        self.tool_executor = tool_executor
        self.caps_service = caps_service
        self.approval_service = approval_service
        self.ledger = ledger or InMemoryActionLedger()

    def execute(
        self,
        request: ActionExecutionRequest,
        *,
        order_total_cents: int | None = None,
        approval_required: bool = False,
        item_sku: str | None = None,
        reason: str = "policy_resolution",
    ) -> ActionExecutionResult:
        duplicate = self.ledger.get_duplicate(request.idempotency_key)
        if duplicate is not None:
            return ActionExecutionResult(
                action_id=duplicate.result.action_id,
                run_id=request.run_id,
                action_type=request.action_type,
                status="duplicate_replay",
                external_reference=duplicate.result.external_reference,
                simulated=request.simulation_mode,
                error_code=None,
            )

        cap_run = self.caps_service.check_per_run(self.ledger.actions_this_run(request.run_id))
        if not cap_run.allowed:
            return self._failed_result(request, error_code=cap_run.reason or "per_run_cap_exceeded")

        today = datetime.now(UTC).date()
        if request.action_type in REFUND_ACTIONS:
            cap_customer = self.caps_service.check_customer_refunds_per_day(
                self.ledger.refunds_for_customer_today(request.customer_id, today)
            )
            if not cap_customer.allowed:
                return self._failed_result(
                    request,
                    error_code=cap_customer.reason or "customer_daily_refund_cap_exceeded",
                )
            if request.amount_cents is not None and order_total_cents is not None:
                cap_percent = self.caps_service.check_order_refund_percent(
                    order_total_cents=order_total_cents,
                    refund_amount_cents=request.amount_cents,
                )
                if not cap_percent.allowed and not approval_required:
                    return self._failed_result(
                        request,
                        error_code=cap_percent.reason or "order_refund_percent_cap_exceeded",
                    )
                if cap_percent.approval_required:
                    approval_required = True

        if approval_required:
            if not request.approval_token:
                return self._failed_result(request, error_code="approval_token_required")
            claims = self.approval_service.consume_approval_token(request.approval_token)
            if claims is None:
                return self._failed_result(request, error_code="approval_token_invalid")
            if claims.run_id != request.run_id or claims.action_type != request.action_type:
                return self._failed_result(request, error_code="approval_token_scope_mismatch")
            if claims.order_id != request.order_id:
                return self._failed_result(request, error_code="approval_token_order_mismatch")
            if (
                claims.max_amount_cents is not None
                and request.amount_cents is not None
                and request.amount_cents > claims.max_amount_cents
            ):
                return self._failed_result(request, error_code="approval_token_amount_exceeded")

        context = ToolCallContext(
            run_id=request.run_id,
            actor_agent="actions",
            simulation_mode=request.simulation_mode,
            approval_token=request.approval_token,
        )

        if request.action_type in REFUND_ACTIONS:
            return self._execute_refund(request, context=context, reason=reason)
        if request.action_type == "replacement_reship":
            return self._execute_reship(request, context=context, item_sku=item_sku)
        if request.action_type == "return_initiation":
            return self._execute_return(request, context=context, reason=reason)

        return self._failed_result(request, error_code="unsupported_action_type")

    def _execute_refund(
        self,
        request: ActionExecutionRequest,
        *,
        context: ToolCallContext,
        reason: str,
    ) -> ActionExecutionResult:
        if request.amount_cents is None or not request.currency:
            return self._failed_result(request, error_code="refund_amount_or_currency_missing")

        result = self.tool_executor.invoke(
            "issue_refund",
            {
                "order_id": request.order_id,
                "amount_cents": request.amount_cents,
                "currency": request.currency,
                "reason": reason,
                "idempotency_key": request.idempotency_key,
                "approval_token": request.approval_token,
            },
            context=context,
            idempotency_key=request.idempotency_key,
        )
        if result.ok and result.data is not None:
            action_result = ActionExecutionResult(
                action_id=f"act_{uuid.uuid4().hex[:16]}",
                run_id=request.run_id,
                action_type=request.action_type,
                status=str(result.data.get("status", "success")),
                external_reference=str(
                    result.data.get("refund_id") or result.external_reference or ""
                ),
                simulated=request.simulation_mode,
                error_code=None,
            )
            self._store(request, action_result)
            return action_result

        if result.error and "timeout_after_creation:" in result.error.message:
            reconciliation = reconcile_refund_after_timeout(
                self.tool_executor,
                context=context,
                timeout_error_message=result.error.message,
            )
            if reconciliation.resolved:
                action_result = ActionExecutionResult(
                    action_id=f"act_{uuid.uuid4().hex[:16]}",
                    run_id=request.run_id,
                    action_type=request.action_type,
                    status=reconciliation.status,
                    external_reference=reconciliation.refund_id,
                    simulated=request.simulation_mode,
                    error_code=None,
                )
                self._store(request, action_result)
                return action_result

        return self._failed_result(
            request,
            error_code=(result.error.code if result.error else "refund_failed"),
        )

    def _execute_reship(
        self,
        request: ActionExecutionRequest,
        *,
        context: ToolCallContext,
        item_sku: str | None,
    ) -> ActionExecutionResult:
        if item_sku is None:
            return self._failed_result(request, error_code="missing_item_sku")

        check = self.tool_executor.invoke(
            "check_stock",
            {"sku": item_sku, "quantity": 1},
            context=context,
        )
        if not check.ok or check.data is None or check.data.get("in_stock") is not True:
            return self._failed_result(request, error_code="stock_unavailable")

        reserve = self.tool_executor.invoke(
            "reserve_stock",
            {
                "sku": item_sku,
                "quantity": 1,
                "reservation_key": request.idempotency_key,
            },
            context=context,
            idempotency_key=request.idempotency_key,
        )
        if not reserve.ok or reserve.data is None or reserve.data.get("status") != "reserved":
            return self._failed_result(request, error_code="reserve_stock_failed")

        action_result = ActionExecutionResult(
            action_id=f"act_{uuid.uuid4().hex[:16]}",
            run_id=request.run_id,
            action_type=request.action_type,
            status="simulated_reship_reserved",
            external_reference=str(reserve.data.get("reservation_id") or ""),
            simulated=request.simulation_mode,
            error_code=None,
        )
        self._store(request, action_result)
        return action_result

    def _execute_return(
        self,
        request: ActionExecutionRequest,
        *,
        context: ToolCallContext,
        reason: str,
    ) -> ActionExecutionResult:
        if request.item_id is None:
            return self._failed_result(request, error_code="missing_item_id")
        created = self.tool_executor.invoke(
            "create_return",
            {
                "order_id": request.order_id,
                "item_id": request.item_id,
                "reason": reason,
                "idempotency_key": request.idempotency_key,
            },
            context=context,
            idempotency_key=request.idempotency_key,
        )
        if not created.ok or created.data is None:
            return self._failed_result(request, error_code="create_return_failed")

        action_result = ActionExecutionResult(
            action_id=f"act_{uuid.uuid4().hex[:16]}",
            run_id=request.run_id,
            action_type=request.action_type,
            status=str(created.data.get("status", "created")),
            external_reference=str(created.data.get("return_id") or ""),
            simulated=request.simulation_mode,
            error_code=None,
        )
        self._store(request, action_result)
        return action_result

    def _failed_result(
        self,
        request: ActionExecutionRequest,
        *,
        error_code: str,
    ) -> ActionExecutionResult:
        return ActionExecutionResult(
            action_id=f"act_{uuid.uuid4().hex[:16]}",
            run_id=request.run_id,
            action_type=request.action_type,
            status="failed",
            external_reference=None,
            simulated=request.simulation_mode,
            error_code=error_code,
        )

    def _store(self, request: ActionExecutionRequest, result: ActionExecutionResult) -> None:
        self.ledger.store(
            StoredActionRecord(
                request=request,
                result=result,
                created_at=datetime.now(UTC),
            )
        )
