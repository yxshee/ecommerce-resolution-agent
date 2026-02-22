from __future__ import annotations

from typing import Protocol

from ecom_resolution_agent.tools.schemas.customer import (
    GetCustomerProfileRequest,
    GetCustomerProfileResponse,
    VerifyCustomerRequest,
    VerifyCustomerResponse,
)
from ecom_resolution_agent.tools.schemas.inventory import (
    CheckStockRequest,
    CheckStockResponse,
    ReserveStockRequest,
    ReserveStockResponse,
)
from ecom_resolution_agent.tools.schemas.knowledge_base import (
    GetPolicyRulesRequest,
    GetPolicyRulesResponse,
    GetPolicyVersionRequest,
    GetPolicyVersionResponse,
    SearchKbArticlesRequest,
    SearchKbArticlesResponse,
)
from ecom_resolution_agent.tools.schemas.orders import (
    GetFulfillmentStatusRequest,
    GetFulfillmentStatusResponse,
    GetOrderItemsRequest,
    GetOrderItemsResponse,
    GetOrderRequest,
    GetOrderResponse,
)
from ecom_resolution_agent.tools.schemas.payments import (
    GetRefundStatusRequest,
    GetRefundStatusResponse,
    IssueRefundRequest,
    IssueRefundResponse,
)
from ecom_resolution_agent.tools.schemas.returns import (
    CreateLabelRequest,
    CreateLabelResponse,
    CreateReturnRequest,
    CreateReturnResponse,
    SchedulePickupRequest,
    SchedulePickupResponse,
)
from ecom_resolution_agent.tools.schemas.shipping import (
    GetDeliveryProofRequest,
    GetDeliveryProofResponse,
    GetTrackingEventsRequest,
    GetTrackingEventsResponse,
)
from ecom_resolution_agent.tools.schemas.ticketing import (
    AddInternalNoteRequest,
    AddInternalNoteResponse,
    CreateTicketRequest,
    CreateTicketResponse,
    UpdateTicketRequest,
    UpdateTicketResponse,
)


class CustomerToolProtocol(Protocol):
    def verify_customer(
        self,
        request: VerifyCustomerRequest,
    ) -> VerifyCustomerResponse: ...

    def get_customer_profile(
        self,
        request: GetCustomerProfileRequest,
    ) -> GetCustomerProfileResponse: ...


class OrdersToolProtocol(Protocol):
    def get_order(self, request: GetOrderRequest) -> GetOrderResponse: ...

    def get_order_items(
        self,
        request: GetOrderItemsRequest,
    ) -> GetOrderItemsResponse: ...
    def get_fulfillment_status(
        self,
        request: GetFulfillmentStatusRequest,
    ) -> GetFulfillmentStatusResponse: ...


class ShippingToolProtocol(Protocol):
    def get_tracking_events(
        self,
        request: GetTrackingEventsRequest,
    ) -> GetTrackingEventsResponse: ...
    def get_delivery_proof(
        self,
        request: GetDeliveryProofRequest,
    ) -> GetDeliveryProofResponse: ...


class ReturnsToolProtocol(Protocol):
    def create_return(self, request: CreateReturnRequest) -> CreateReturnResponse: ...

    def create_label(self, request: CreateLabelRequest) -> CreateLabelResponse: ...

    def schedule_pickup(
        self,
        request: SchedulePickupRequest,
    ) -> SchedulePickupResponse: ...


class PaymentsToolProtocol(Protocol):
    def issue_refund(self, request: IssueRefundRequest) -> IssueRefundResponse: ...

    def get_refund_status(
        self,
        request: GetRefundStatusRequest,
    ) -> GetRefundStatusResponse: ...


class InventoryToolProtocol(Protocol):
    def check_stock(self, request: CheckStockRequest) -> CheckStockResponse: ...

    def reserve_stock(self, request: ReserveStockRequest) -> ReserveStockResponse: ...


class TicketingToolProtocol(Protocol):
    def create_ticket(self, request: CreateTicketRequest) -> CreateTicketResponse: ...

    def update_ticket(self, request: UpdateTicketRequest) -> UpdateTicketResponse: ...

    def add_internal_note(
        self,
        request: AddInternalNoteRequest,
    ) -> AddInternalNoteResponse: ...


class KnowledgeBaseToolProtocol(Protocol):
    def get_policy_version(
        self,
        request: GetPolicyVersionRequest,
    ) -> GetPolicyVersionResponse: ...
    def get_policy_rules(self, request: GetPolicyRulesRequest) -> GetPolicyRulesResponse: ...
    def search_kb_articles(
        self,
        request: SearchKbArticlesRequest,
    ) -> SearchKbArticlesResponse: ...
