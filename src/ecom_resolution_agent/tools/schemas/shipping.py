from __future__ import annotations

from datetime import datetime

from ecom_resolution_agent.schemas.base import StrictModel
from ecom_resolution_agent.tools.schemas.common import TrackingEvent


class GetTrackingEventsRequest(StrictModel):
    tracking_number: str


class GetTrackingEventsResponse(StrictModel):
    tracking_number: str
    carrier: str | None = None
    events: list[TrackingEvent]


class GetDeliveryProofRequest(StrictModel):
    order_id: str
    tracking_number: str | None = None


class GetDeliveryProofResponse(StrictModel):
    order_id: str
    tracking_number: str | None = None
    available: bool
    proof_type: str | None = None
    delivered_at: datetime | None = None
    proof_reference: str | None = None
