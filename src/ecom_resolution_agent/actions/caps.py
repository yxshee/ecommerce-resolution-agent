from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ActionCapsConfig:
    max_actions_per_run: int = 3
    max_auto_refunds_per_customer_per_day: int = 2
    max_auto_refund_percent_per_order: int = 50


@dataclass(frozen=True)
class CapCheckResult:
    allowed: bool
    reason: str | None = None
    approval_required: bool = False


class ActionCapsService:
    def __init__(self, config: ActionCapsConfig | None = None) -> None:
        self.config = config or ActionCapsConfig()

    def check_per_run(self, actions_this_run: int) -> CapCheckResult:
        if actions_this_run >= self.config.max_actions_per_run:
            return CapCheckResult(allowed=False, reason="per_run_cap_exceeded")
        return CapCheckResult(allowed=True)

    def check_customer_refunds_per_day(self, refunds_today: int) -> CapCheckResult:
        if refunds_today >= self.config.max_auto_refunds_per_customer_per_day:
            return CapCheckResult(allowed=False, reason="customer_daily_refund_cap_exceeded")
        return CapCheckResult(allowed=True)

    def check_order_refund_percent(
        self,
        *,
        order_total_cents: int,
        refund_amount_cents: int,
    ) -> CapCheckResult:
        if order_total_cents <= 0:
            return CapCheckResult(allowed=False, reason="invalid_order_total")
        percent = (refund_amount_cents / order_total_cents) * 100
        if percent > self.config.max_auto_refund_percent_per_order:
            return CapCheckResult(
                allowed=False,
                reason="order_refund_percent_cap_exceeded",
                approval_required=True,
            )
        return CapCheckResult(allowed=True)
