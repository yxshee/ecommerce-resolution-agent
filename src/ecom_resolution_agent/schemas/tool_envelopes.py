from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import Field, model_validator

from ecom_resolution_agent.schemas.base import StrictModel

T = TypeVar("T")


class ToolCallContext(StrictModel):
    run_id: str
    actor_agent: str
    simulation_mode: bool = True
    request_id: str | None = None
    approval_token: str | None = None


class ToolError(StrictModel):
    code: str
    message: str
    retryable: bool = False
    details: dict[str, Any] = Field(default_factory=dict)


class ToolCallRequest(StrictModel, Generic[T]):
    tool_name: str
    tool_input: T
    context: ToolCallContext
    idempotency_key: str | None = None


class ToolCallResult(StrictModel, Generic[T]):
    tool_name: str
    ok: bool
    data: T | None = None
    error: ToolError | None = None
    external_reference: str | None = None
    latency_ms: int = Field(ge=0)
    simulated: bool = True

    @model_validator(mode="after")
    def validate_result_shape(self) -> ToolCallResult[T]:
        if self.ok and self.error is not None:
            raise ValueError("error must be null when ok=true")
        if not self.ok and self.error is None:
            raise ValueError("error is required when ok=false")
        return self
