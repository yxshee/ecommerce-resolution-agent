from __future__ import annotations

from sqlalchemy.orm import Session

from ecom_resolution_agent.db.models import Ticket


class TicketRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        *,
        ticket_id: str,
        customer_id: str,
        order_id: str,
        issue_type: str,
        status: str,
    ) -> Ticket:
        ticket = Ticket(
            ticket_id=ticket_id,
            customer_id=customer_id,
            order_id=order_id,
            issue_type=issue_type,
            status=status,
        )
        self.session.add(ticket)
        self.session.flush()
        return ticket

    def get(self, ticket_id: str) -> Ticket | None:
        return self.session.get(Ticket, ticket_id)

    def update_status(self, ticket_id: str, status: str) -> Ticket | None:
        ticket = self.get(ticket_id)
        if ticket is None:
            return None
        ticket.status = status
        self.session.flush()
        return ticket
