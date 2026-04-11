from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from ecom_resolution_agent.schemas.base import StrictModel
from ecom_resolution_agent.tools.mock import (
    MockCustomerTools,
    MockInventoryTools,
    MockKnowledgeBaseTools,
    MockOrdersTools,
    MockPaymentsTools,
    MockReturnsTools,
    MockShippingTools,
    MockStore,
    MockTicketingTools,
)
from ecom_resolution_agent.tools.schemas import (
    AddInternalNoteRequest,
    AddInternalNoteResponse,
    CheckStockRequest,
    CheckStockResponse,
    CreateLabelRequest,
    CreateLabelResponse,
    CreateReturnRequest,
    CreateReturnResponse,
    CreateTicketRequest,
    CreateTicketResponse,
    GetCustomerProfileRequest,
    GetCustomerProfileResponse,
    GetDeliveryProofRequest,
    GetDeliveryProofResponse,
    GetFulfillmentStatusRequest,
    GetFulfillmentStatusResponse,
    GetOrderItemsRequest,
    GetOrderItemsResponse,
    GetOrderRequest,
    GetOrderResponse,
    GetPolicyRulesRequest,
    GetPolicyRulesResponse,
    GetPolicyVersionRequest,
    GetPolicyVersionResponse,
    GetRefundStatusRequest,
    GetRefundStatusResponse,
    GetTrackingEventsRequest,
    GetTrackingEventsResponse,
    IssueRefundRequest,
    IssueRefundResponse,
    ReserveStockRequest,
    ReserveStockResponse,
    SchedulePickupRequest,
    SchedulePickupResponse,
    SearchKbArticlesRequest,
    SearchKbArticlesResponse,
    UpdateTicketRequest,
    UpdateTicketResponse,
    VerifyCustomerRequest,
    VerifyCustomerResponse,
)

Handler = Callable[[Any], Any]


@dataclass(frozen=True)
class RegisteredTool:
    name: str
    request_model: type[StrictModel]
    response_model: type[StrictModel]
    handler: Handler
    is_action_tool: bool = False


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, RegisteredTool] = {}

    def register(self, spec: RegisteredTool) -> None:
        if spec.name in self._tools:
            raise ValueError(f"tool already registered: {spec.name}")
        self._tools[spec.name] = spec

    def get(self, tool_name: str) -> RegisteredTool:
        try:
            return self._tools[tool_name]
        except KeyError as exc:
            raise KeyError(f"unknown tool: {tool_name}") from exc

    def names(self) -> list[str]:
        return sorted(self._tools)


ACTION_TOOL_NAMES = {
    "create_return",
    "create_label",
    "schedule_pickup",
    "issue_refund",
    "reserve_stock",
    "update_ticket",
    "add_internal_note",
}


def build_mock_tool_registry(store: MockStore) -> ToolRegistry:
    registry = ToolRegistry()

    customer = MockCustomerTools(store)
    orders = MockOrdersTools(store)
    shipping = MockShippingTools(store)
    returns = MockReturnsTools(store)
    payments = MockPaymentsTools(store)
    inventory = MockInventoryTools(store)
    ticketing = MockTicketingTools(store)
    kb = MockKnowledgeBaseTools(store)

    defs: list[tuple[str, type[StrictModel], type[StrictModel], Handler]] = [
        (
            "verify_customer",
            VerifyCustomerRequest,
            VerifyCustomerResponse,
            customer.verify_customer,
        ),
        (
            "get_customer_profile",
            GetCustomerProfileRequest,
            GetCustomerProfileResponse,
            customer.get_customer_profile,
        ),
        ("get_order", GetOrderRequest, GetOrderResponse, orders.get_order),
        ("get_order_items", GetOrderItemsRequest, GetOrderItemsResponse, orders.get_order_items),
        (
            "get_fulfillment_status",
            GetFulfillmentStatusRequest,
            GetFulfillmentStatusResponse,
            orders.get_fulfillment_status,
        ),
        (
            "get_tracking_events",
            GetTrackingEventsRequest,
            GetTrackingEventsResponse,
            shipping.get_tracking_events,
        ),
        (
            "get_delivery_proof",
            GetDeliveryProofRequest,
            GetDeliveryProofResponse,
            shipping.get_delivery_proof,
        ),
        ("create_return", CreateReturnRequest, CreateReturnResponse, returns.create_return),
        ("create_label", CreateLabelRequest, CreateLabelResponse, returns.create_label),
        ("schedule_pickup", SchedulePickupRequest, SchedulePickupResponse, returns.schedule_pickup),
        ("issue_refund", IssueRefundRequest, IssueRefundResponse, payments.issue_refund),
        (
            "get_refund_status",
            GetRefundStatusRequest,
            GetRefundStatusResponse,
            payments.get_refund_status,
        ),
        ("check_stock", CheckStockRequest, CheckStockResponse, inventory.check_stock),
        ("reserve_stock", ReserveStockRequest, ReserveStockResponse, inventory.reserve_stock),
        ("create_ticket", CreateTicketRequest, CreateTicketResponse, ticketing.create_ticket),
        ("update_ticket", UpdateTicketRequest, UpdateTicketResponse, ticketing.update_ticket),
        (
            "add_internal_note",
            AddInternalNoteRequest,
            AddInternalNoteResponse,
            ticketing.add_internal_note,
        ),
        (
            "get_policy_version",
            GetPolicyVersionRequest,
            GetPolicyVersionResponse,
            kb.get_policy_version,
        ),
        ("get_policy_rules", GetPolicyRulesRequest, GetPolicyRulesResponse, kb.get_policy_rules),
        (
            "search_kb_articles",
            SearchKbArticlesRequest,
            SearchKbArticlesResponse,
            kb.search_kb_articles,
        ),
    ]

    for name, request_model, response_model, handler in defs:
        registry.register(
            RegisteredTool(
                name=name,
                request_model=request_model,
                response_model=response_model,
                handler=handler,
                is_action_tool=name in ACTION_TOOL_NAMES,
            )
        )

    return registry
