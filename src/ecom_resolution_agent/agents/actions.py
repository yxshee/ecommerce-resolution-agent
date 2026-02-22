from __future__ import annotations

from ecom_resolution_agent.actions.executor import ActionExecutor
from ecom_resolution_agent.actions.idempotency import IdempotencyKeyInput, build_idempotency_key
from ecom_resolution_agent.schemas.actions import ActionExecutionRequest, ActionExecutionResult


class DeterministicActionsAgent:
    def __init__(self, executor: ActionExecutor) -> None:
        self.executor = executor

    def execute_resolution(
        self,
        *,
        run_id: str,
        action_type: str,
        customer_id: str,
        order_id: str,
        policy_version: str,
        item_id: str | None = None,
        item_sku: str | None = None,
        amount_cents: int | None = None,
        currency: str | None = None,
        simulation_mode: bool = True,
        approval_required: bool = False,
        approval_token: str | None = None,
        order_total_cents: int | None = None,
        reason: str = "policy_resolution",
    ) -> ActionExecutionResult:
        idem = build_idempotency_key(
            IdempotencyKeyInput(
                order_id=order_id,
                action_type=action_type,
                item_id=item_id,
                amount_cents=amount_cents,
                currency=currency,
                policy_version=policy_version,
            )
        )
        request = ActionExecutionRequest(
            run_id=run_id,
            action_type=action_type,
            customer_id=customer_id,
            order_id=order_id,
            item_id=item_id,
            amount_cents=amount_cents,
            currency=currency,
            idempotency_key=idem,
            approval_token=approval_token,
            simulation_mode=simulation_mode,
        )
        return self.executor.execute(
            request,
            order_total_cents=order_total_cents,
            approval_required=approval_required,
            item_sku=item_sku,
            reason=reason,
        )
