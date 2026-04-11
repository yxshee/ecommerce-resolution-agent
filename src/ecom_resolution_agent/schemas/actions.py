from __future__ import annotations

from datetime import datetime

from pydantic import Field

from ecom_resolution_agent.schemas.base import StrictModel


class ActionExecutionRequest(StrictModel):
    run_id: str
    action_type: str
    customer_id: str
    order_id: str
    item_id: str | None = None
    amount_cents: int | None = Field(default=None, ge=0)
    currency: str | None = None
    idempotency_key: str
    approval_token: str | None = None
    simulation_mode: bool = True


class ActionExecutionResult(StrictModel):
    action_id: str
    run_id: str
    action_type: str
    status: str
    external_reference: str | None = None
    simulated: bool = True
    error_code: str | None = None


class ApprovalTokenClaims(StrictModel):
    token_id: str
    run_id: str
    action_type: str
    order_id: str
    max_amount_cents: int | None = Field(default=None, ge=0)
    expires_at: datetime
