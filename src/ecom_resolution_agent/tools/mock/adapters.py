from __future__ import annotations

from typing import Any

from ecom_resolution_agent.tools.mock.store import MockStore
from ecom_resolution_agent.tools.schemas.common import KbArticleSummary
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


class MockCustomerTools:
    def __init__(self, store: MockStore) -> None:
        self.store = store

    def verify_customer(self, request: VerifyCustomerRequest) -> VerifyCustomerResponse:
        customers = self.store.data.get("customers", {})
        orders = self.store.data.get("orders", {})
        customer = customers.get(request.customer_id)
        order = orders.get(request.order_id)
        if customer is None or order is None:
            return VerifyCustomerResponse(
                verified=False,
                verification_method=None,
                reason="customer_or_order_not_found",
            )
        if order.get("customer_id") != request.customer_id:
            return VerifyCustomerResponse(
                verified=False,
                verification_method=None,
                reason="order_customer_mismatch",
            )
        if request.email and request.email.lower() == str(customer.get("email", "")).lower():
            return VerifyCustomerResponse(
                verified=True,
                verification_method="email_exact_match",
                reason=None,
            )
        if request.phone_last4 and str(customer.get("phone", "")).endswith(request.phone_last4):
            return VerifyCustomerResponse(
                verified=True,
                verification_method="phone_last4_match",
                reason=None,
            )
        return VerifyCustomerResponse(
            verified=False,
            verification_method=None,
            reason="verification_signal_mismatch",
        )

    def get_customer_profile(
        self,
        request: GetCustomerProfileRequest,
    ) -> GetCustomerProfileResponse:
        customer = self.store.data["customers"][request.customer_id]
        return GetCustomerProfileResponse.model_validate(customer)


class MockOrdersTools:
    def __init__(self, store: MockStore) -> None:
        self.store = store

    def get_order(self, request: GetOrderRequest) -> GetOrderResponse:
        order = self.store.data["orders"][request.order_id]
        return GetOrderResponse.model_validate(order)

    def get_order_items(self, request: GetOrderItemsRequest) -> GetOrderItemsResponse:
        items = self.store.data.get("order_items", {}).get(request.order_id, [])
        return GetOrderItemsResponse(order_id=request.order_id, items=items)

    def get_fulfillment_status(
        self,
        request: GetFulfillmentStatusRequest,
    ) -> GetFulfillmentStatusResponse:
        status = self.store.data["fulfillment_statuses"][request.order_id]
        return GetFulfillmentStatusResponse.model_validate(status)


class MockShippingTools:
    def __init__(self, store: MockStore) -> None:
        self.store = store

    def get_tracking_events(self, request: GetTrackingEventsRequest) -> GetTrackingEventsResponse:
        payload = self.store.data["tracking_events"][request.tracking_number]
        return GetTrackingEventsResponse.model_validate(payload)

    def get_delivery_proof(self, request: GetDeliveryProofRequest) -> GetDeliveryProofResponse:
        proof = self.store.data["delivery_proofs"][request.order_id]
        return GetDeliveryProofResponse.model_validate(proof)


class MockReturnsTools:
    def __init__(self, store: MockStore) -> None:
        self.store = store

    def create_return(self, request: CreateReturnRequest) -> CreateReturnResponse:
        return_id = self.store.next_id("ret")
        self.store.data.setdefault("returns", {})[return_id] = {
            "return_id": return_id,
            "order_id": request.order_id,
            "item_id": request.item_id,
            "status": "created",
            "idempotency_key": request.idempotency_key,
        }
        return CreateReturnResponse(return_id=return_id, status="created")

    def create_label(self, request: CreateLabelRequest) -> CreateLabelResponse:
        label_id = self.store.next_id("lbl")
        return CreateLabelResponse(
            label_id=label_id,
            label_url=f"https://mock.local/labels/{label_id}.pdf",
            status="created",
        )

    def schedule_pickup(self, request: SchedulePickupRequest) -> SchedulePickupResponse:
        pickup_id = self.store.next_id("pku")
        return SchedulePickupResponse(pickup_id=pickup_id, status="scheduled")


class MockPaymentsTools:
    def __init__(self, store: MockStore) -> None:
        self.store = store

    def issue_refund(self, request: IssueRefundRequest) -> IssueRefundResponse:
        refund_id = self.store.next_id("rfd")
        status = "simulated_success"
        self.store.data.setdefault("refunds", {})[refund_id] = {
            "refund_id": refund_id,
            "status": status,
            "amount_cents": request.amount_cents,
            "currency": request.currency,
            "order_id": request.order_id,
            "idempotency_key": request.idempotency_key,
        }
        return IssueRefundResponse(
            refund_id=refund_id,
            status=status,
            external_reference=f"mock_ref_{refund_id}",
        )

    def get_refund_status(self, request: GetRefundStatusRequest) -> GetRefundStatusResponse:
        refund = self.store.data.get("refunds", {}).get(request.refund_id)
        if refund is None:
            return GetRefundStatusResponse(
                refund_id=request.refund_id,
                status="not_found",
                amount_cents=None,
                currency=None,
            )
        return GetRefundStatusResponse.model_validate(refund)


class MockInventoryTools:
    def __init__(self, store: MockStore) -> None:
        self.store = store

    def check_stock(self, request: CheckStockRequest) -> CheckStockResponse:
        stock = self.store.data.get("inventory", {}).get(request.sku, {"available_quantity": 0})
        available_quantity = int(stock.get("available_quantity", 0))
        return CheckStockResponse(
            sku=request.sku,
            requested_quantity=request.quantity,
            available_quantity=available_quantity,
            in_stock=available_quantity >= request.quantity,
        )

    def reserve_stock(self, request: ReserveStockRequest) -> ReserveStockResponse:
        inventory = self.store.data.setdefault("inventory", {})
        stock = inventory.setdefault(request.sku, {"available_quantity": 0})
        available_quantity = int(stock.get("available_quantity", 0))
        if available_quantity >= request.quantity:
            stock["available_quantity"] = available_quantity - request.quantity
            status = "reserved"
        else:
            status = "insufficient_stock"
        return ReserveStockResponse(
            reservation_id=self.store.next_id("rsv"),
            sku=request.sku,
            quantity=request.quantity,
            status=status,
        )


class MockTicketingTools:
    def __init__(self, store: MockStore) -> None:
        self.store = store

    def create_ticket(self, request: CreateTicketRequest) -> CreateTicketResponse:
        self.store.data.setdefault("tickets", {})[request.ticket_id] = {
            "ticket_id": request.ticket_id,
            "customer_id": request.customer_id,
            "order_id": request.order_id,
            "issue_type": request.issue_type,
            "status": request.status,
            "customer_message": request.customer_message,
        }
        return CreateTicketResponse(ticket_id=request.ticket_id, status=request.status)

    def update_ticket(self, request: UpdateTicketRequest) -> UpdateTicketResponse:
        ticket = self.store.data.setdefault("tickets", {}).setdefault(
            request.ticket_id,
            {"ticket_id": request.ticket_id, "status": request.status},
        )
        ticket["status"] = request.status
        return UpdateTicketResponse(ticket_id=request.ticket_id, status=request.status)

    def add_internal_note(self, request: AddInternalNoteRequest) -> AddInternalNoteResponse:
        note_id = self.store.next_id("note")
        notes = self.store.data.setdefault("ticket_notes", {}).setdefault(request.ticket_id, [])
        notes.append({"note_id": note_id, "note_markdown": request.note_markdown})
        return AddInternalNoteResponse(ticket_id=request.ticket_id, note_id=note_id, status="added")


class MockKnowledgeBaseTools:
    def __init__(self, store: MockStore) -> None:
        self.store = store

    def get_policy_version(self, request: GetPolicyVersionRequest) -> GetPolicyVersionResponse:
        versions = self.store.data.get("kb", {}).get("policy_versions", {})
        policy_version = versions.get(request.issue_type, "v1_0_0")
        return GetPolicyVersionResponse(policy_version=policy_version)

    def get_policy_rules(self, request: GetPolicyRulesRequest) -> GetPolicyRulesResponse:
        rules = (
            self.store.data.get("kb", {}).get("policy_rules", {}).get(request.policy_version, {})
        )
        return GetPolicyRulesResponse(policy_version=request.policy_version, rules=rules)

    def search_kb_articles(self, request: SearchKbArticlesRequest) -> SearchKbArticlesResponse:
        articles: list[dict[str, Any]] = self.store.data.get("kb", {}).get("articles", [])
        query_terms = {term.lower() for term in request.query.split() if term.strip()}
        ranked = []
        for article in articles:
            haystack = f"{article.get('title', '')} {article.get('snippet', '')}".lower()
            score = sum(1 for term in query_terms if term in haystack)
            if score > 0 or not query_terms:
                ranked.append((score, article))
        ranked.sort(key=lambda item: item[0], reverse=True)
        results = [
            KbArticleSummary.model_validate(article) for _, article in ranked[: request.limit]
        ]
        return SearchKbArticlesResponse(query=request.query, results=results)
