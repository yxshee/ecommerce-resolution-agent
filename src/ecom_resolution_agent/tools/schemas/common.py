from __future__ import annotations

from datetime import datetime

from pydantic import Field

from ecom_resolution_agent.schemas.base import StrictModel


class Money(StrictModel):
    amount_cents: int = Field(ge=0)
    currency: str


class Address(StrictModel):
    name: str | None = None
    line1: str
    city: str
    region: str | None = None
    postal_code: str | None = None
    country: str = "US"


class TrackingEvent(StrictModel):
    event_id: str
    status: str
    description: str
    location: str | None = None
    timestamp: datetime


class OrderItem(StrictModel):
    item_id: str
    sku: str
    title: str
    quantity: int = Field(ge=1)
    unit_price_cents: int = Field(ge=0)
    currency: str = "USD"
    shippable: bool = True


class KbArticleSummary(StrictModel):
    article_id: str
    title: str
    snippet: str
