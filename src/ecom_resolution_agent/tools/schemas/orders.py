from __future__ import annotations

from ecom_resolution_agent.schemas.base import StrictModel
from ecom_resolution_agent.tools.schemas.common import Address, Money, OrderItem


class GetOrderRequest(StrictModel):
    order_id: str


class GetOrderResponse(StrictModel):
    order_id: str
    customer_id: str
    status: str
    issue_type_hint: str | None = None
    total: Money
    shipping_address: Address | None = None
    shipping_tracking_number: str | None = None


class GetOrderItemsRequest(StrictModel):
    order_id: str


class GetOrderItemsResponse(StrictModel):
    order_id: str
    items: list[OrderItem]


class GetFulfillmentStatusRequest(StrictModel):
    order_id: str


class GetFulfillmentStatusResponse(StrictModel):
    order_id: str
    status: str
    shipped: bool
    delivered: bool
    tracking_number: str | None = None
    carrier: str | None = None
