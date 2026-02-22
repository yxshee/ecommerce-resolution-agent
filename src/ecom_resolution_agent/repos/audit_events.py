from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from ecom_resolution_agent.db.models import AuditEvent


class AuditEventRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        *,
        event_id: str,
        run_id: str,
        actor_agent: str,
        tool_name: str | None,
        tool_input_redacted_json: dict[str, Any] | None,
        tool_output_redacted_json: dict[str, Any] | None,
        decision_note: str | None,
        timestamp: datetime | None = None,
    ) -> AuditEvent:
        event = AuditEvent(
            event_id=event_id,
            run_id=run_id,
            actor_agent=actor_agent,
            tool_name=tool_name,
            tool_input_redacted_json=tool_input_redacted_json,
            tool_output_redacted_json=tool_output_redacted_json,
            decision_note=decision_note,
        )
        if timestamp is not None:
            event.timestamp = timestamp
        self.session.add(event)
        self.session.flush()
        return event

    def list_by_run_id(self, run_id: str) -> list[AuditEvent]:
        stmt = (
            select(AuditEvent)
            .where(AuditEvent.run_id == run_id)
            .order_by(AuditEvent.timestamp.asc())
        )
        return list(self.session.execute(stmt).scalars())
