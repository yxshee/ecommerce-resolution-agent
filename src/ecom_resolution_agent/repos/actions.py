from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from ecom_resolution_agent.db.models import Action


class ActionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        *,
        action_id: str,
        run_id: str,
        action_type: str,
        idempotency_key: str,
        status: str,
        customer_id: str,
        order_id: str,
        simulation_mode: bool,
        external_reference: str | None = None,
        item_id: str | None = None,
        amount_cents: int | None = None,
        currency: str | None = None,
        approval_task_id: str | None = None,
        error_code: str | None = None,
    ) -> Action:
        action = Action(
            action_id=action_id,
            run_id=run_id,
            action_type=action_type,
            idempotency_key=idempotency_key,
            status=status,
            external_reference=external_reference,
            customer_id=customer_id,
            order_id=order_id,
            item_id=item_id,
            amount_cents=amount_cents,
            currency=currency,
            simulation_mode=simulation_mode,
            approval_task_id=approval_task_id,
            error_code=error_code,
        )
        self.session.add(action)
        self.session.flush()
        return action

    def get_by_idempotency_key(self, idempotency_key: str) -> Action | None:
        stmt = select(Action).where(Action.idempotency_key == idempotency_key)
        return self.session.execute(stmt).scalar_one_or_none()

    def list_by_run_id(self, run_id: str) -> list[Action]:
        stmt = select(Action).where(Action.run_id == run_id).order_by(Action.created_at.asc())
        return list(self.session.execute(stmt).scalars())
