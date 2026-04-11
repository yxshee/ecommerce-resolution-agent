from __future__ import annotations

from datetime import datetime

from pydantic import Field

from ecom_resolution_agent.schemas.base import StrictModel


class VerifyCustomerRequest(StrictModel):
    customer_id: str
    order_id: str
    email: str | None = None
    phone_last4: str | None = Field(default=None, min_length=4, max_length=4)


class VerifyCustomerResponse(StrictModel):
    verified: bool
    verification_method: str | None = None
    reason: str | None = None


class GetCustomerProfileRequest(StrictModel):
    customer_id: str


class GetCustomerProfileResponse(StrictModel):
    customer_id: str
    email: str
    phone: str | None = None
    default_shipping_address: dict[str, str] | None = None
    created_at: datetime
    risk_flags: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
