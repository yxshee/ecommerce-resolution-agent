from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from ecom_resolution_agent.db.models import ApprovalTask


class ApprovalTaskRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        *,
        approval_task_id: str,
        run_id: str,
        action_type: str,
        status: str,
        requested_reason: str,
        ticket_id: str | None = None,
        token_id: str | None = None,
    ) -> ApprovalTask:
        task = ApprovalTask(
            approval_task_id=approval_task_id,
            run_id=run_id,
            ticket_id=ticket_id,
            action_type=action_type,
            status=status,
            requested_reason=requested_reason,
            token_id=token_id,
        )
        self.session.add(task)
        self.session.flush()
        return task

    def get(self, approval_task_id: str) -> ApprovalTask | None:
        return self.session.get(ApprovalTask, approval_task_id)

    def resolve(
        self,
        approval_task_id: str,
        *,
        status: str,
        resolver_id: str,
    ) -> ApprovalTask | None:
        task = self.get(approval_task_id)
        if task is None:
            return None
        task.status = status
        task.resolver_id = resolver_id
        task.resolved_at = datetime.now(UTC)
        self.session.flush()
        return task

    def list_by_run_id(self, run_id: str) -> list[ApprovalTask]:
        stmt = select(ApprovalTask).where(ApprovalTask.run_id == run_id)
        return list(self.session.execute(stmt).scalars())
