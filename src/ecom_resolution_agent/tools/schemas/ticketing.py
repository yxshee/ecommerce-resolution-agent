from __future__ import annotations

from ecom_resolution_agent.schemas.base import StrictModel


class CreateTicketRequest(StrictModel):
    ticket_id: str
    customer_id: str
    order_id: str
    issue_type: str
    status: str
    customer_message: str


class CreateTicketResponse(StrictModel):
    ticket_id: str
    status: str


class UpdateTicketRequest(StrictModel):
    ticket_id: str
    status: str


class UpdateTicketResponse(StrictModel):
    ticket_id: str
    status: str


class AddInternalNoteRequest(StrictModel):
    ticket_id: str
    note_markdown: str


class AddInternalNoteResponse(StrictModel):
    ticket_id: str
    note_id: str
    status: str
