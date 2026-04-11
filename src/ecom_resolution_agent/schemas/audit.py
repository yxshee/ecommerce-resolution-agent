from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field

from ecom_resolution_agent.schemas.base import StrictModel


class AuditEventRecord(StrictModel):
    event_id: str
    run_id: str
    timestamp: datetime
    actor_agent: str
    tool_name: str | None = None
    tool_input_redacted_json: dict[str, Any] | None = None
    tool_output_redacted_json: dict[str, Any] | None = None
    decision_note: str | None = None


class StateTransitionEvent(StrictModel):
    run_id: str
    state: str
    phase: str = Field(pattern="^(enter|exit)$")
    timestamp: datetime
    next_state: str | None = None
    success: bool = True
    error_kind: str | None = None


class TraceSpanRecord(StrictModel):
    run_id: str
    span_name: str
    started_at: datetime
    ended_at: datetime
    attributes: dict[str, Any] = Field(default_factory=dict)
    success: bool = True
