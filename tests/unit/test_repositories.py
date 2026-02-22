from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from ecom_resolution_agent.db.base import Base
from ecom_resolution_agent.repos import (
    ActionRepository,
    AuditEventRepository,
    CaseRepository,
    TicketRepository,
)


def make_session() -> Session:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    return factory()


def test_ticket_and_case_repositories_crud() -> None:
    session = make_session()
    try:
        tickets = TicketRepository(session)
        cases = CaseRepository(session)

        tickets.create(
            ticket_id="t_1",
            customer_id="c_1",
            order_id="o_1",
            issue_type="order_status",
            status="open",
        )
        session.commit()

        loaded = tickets.get("t_1")
        assert loaded is not None
        assert loaded.status == "open"

        updated = tickets.update_status("t_1", "in_progress")
        session.commit()
        assert updated is not None
        assert updated.status == "in_progress"

        case = cases.create(
            case_id="case_1",
            ticket_id="t_1",
            run_id="run_1",
            policy_version="v1_0_0",
            risk_score=0.2,
            decision_json={"selected_action": "escalate_human"},
        )
        session.commit()

        assert case.run_id == "run_1"
        loaded_case = cases.get_by_run_id("run_1")
        assert loaded_case is not None
        assert loaded_case.ticket_id == "t_1"
    finally:
        session.close()


def test_audit_and_action_repositories_crud() -> None:
    session = make_session()
    try:
        audits = AuditEventRepository(session)
        actions = ActionRepository(session)

        audits.create(
            event_id="evt_1",
            run_id="run_1",
            actor_agent="triage",
            tool_name="get_order",
            tool_input_redacted_json={"order_id": "o_1"},
            tool_output_redacted_json={"status": "shipped"},
            decision_note="facts retrieved",
        )
        actions.create(
            action_id="act_1",
            run_id="run_1",
            action_type="refund_partial",
            idempotency_key="idem_1",
            status="simulated_success",
            customer_id="c_1",
            order_id="o_1",
            simulation_mode=True,
            amount_cents=500,
            currency="USD",
        )
        session.commit()

        run_events = audits.list_by_run_id("run_1")
        assert len(run_events) == 1
        assert run_events[0].tool_name == "get_order"

        stored_action = actions.get_by_idempotency_key("idem_1")
        assert stored_action is not None
        assert stored_action.status == "simulated_success"
        assert stored_action.amount_cents == 500
        assert len(actions.list_by_run_id("run_1")) == 1
    finally:
        session.close()
