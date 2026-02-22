from __future__ import annotations

from pydantic import Field

from ecom_resolution_agent.schemas.base import StrictModel


class CheckStockRequest(StrictModel):
    sku: str
    quantity: int = Field(ge=1)


class CheckStockResponse(StrictModel):
    sku: str
    requested_quantity: int
    available_quantity: int = Field(ge=0)
    in_stock: bool


class ReserveStockRequest(StrictModel):
    sku: str
    quantity: int = Field(ge=1)
    reservation_key: str


class ReserveStockResponse(StrictModel):
    reservation_id: str
    sku: str
    quantity: int
    status: str
