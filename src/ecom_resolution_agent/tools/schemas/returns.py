from __future__ import annotations

from ecom_resolution_agent.schemas.base import StrictModel


class CreateReturnRequest(StrictModel):
    order_id: str
    item_id: str
    reason: str
    idempotency_key: str


class CreateReturnResponse(StrictModel):
    return_id: str
    status: str


class CreateLabelRequest(StrictModel):
    return_id: str
    carrier: str | None = None


class CreateLabelResponse(StrictModel):
    label_id: str
    label_url: str
    status: str


class SchedulePickupRequest(StrictModel):
    return_id: str
    pickup_date: str
    window: str | None = None


class SchedulePickupResponse(StrictModel):
    pickup_id: str
    status: str
