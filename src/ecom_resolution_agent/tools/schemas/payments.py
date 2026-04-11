from __future__ import annotations

from ecom_resolution_agent.schemas.base import StrictModel


class IssueRefundRequest(StrictModel):
    order_id: str
    amount_cents: int
    currency: str
    reason: str
    idempotency_key: str
    approval_token: str | None = None


class IssueRefundResponse(StrictModel):
    refund_id: str
    status: str
    external_reference: str | None = None


class GetRefundStatusRequest(StrictModel):
    refund_id: str


class GetRefundStatusResponse(StrictModel):
    refund_id: str
    status: str
    amount_cents: int | None = None
    currency: str | None = None
