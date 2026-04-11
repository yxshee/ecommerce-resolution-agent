from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from ecom_resolution_agent.db.models import Case


class CaseRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        *,
        case_id: str,
        ticket_id: str,
        run_id: str,
        policy_version: str,
        risk_score: float | None,
        decision_json: dict[str, Any] | None,
    ) -> Case:
        case = Case(
            case_id=case_id,
            ticket_id=ticket_id,
            run_id=run_id,
            policy_version=policy_version,
            risk_score=risk_score,
            decision_json=decision_json,
        )
        self.session.add(case)
        self.session.flush()
        return case

    def get_by_run_id(self, run_id: str) -> Case | None:
        stmt = select(Case).where(Case.run_id == run_id)
        return self.session.execute(stmt).scalar_one_or_none()
