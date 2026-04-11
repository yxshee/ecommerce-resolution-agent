from __future__ import annotations

from collections.abc import Hashable
from typing import Any

from langgraph.graph import END, StateGraph

from ecom_resolution_agent.orchestration.nodes import (
    run_classify_issue,
    run_gather_facts,
    run_intake,
    run_policy_lookup,
    run_verify_identity,
)
from ecom_resolution_agent.orchestration.nodes.common import OrchestrationDeps
from ecom_resolution_agent.orchestration.state import END_ROUTE, CaseState


class EcommerceOrchestrator:
    """LangGraph orchestration for Phase 4 (intake through policy lookup)."""

    def __init__(self, deps: OrchestrationDeps) -> None:
        self.deps = deps
        self._graph = self._build_graph()

    def _build_graph(self) -> Any:
        # LangGraph's generics are stricter than our dynamic dict state in Phase 4.
        builder = StateGraph(dict)  # type: ignore[type-var]

        builder.add_node("intake", run_intake)  # type: ignore[call-overload]
        builder.add_node("verify_identity", lambda state: run_verify_identity(state, self.deps))
        builder.add_node("gather_facts", lambda state: run_gather_facts(state, self.deps))
        builder.add_node("classify_issue", lambda state: run_classify_issue(state, self.deps))
        builder.add_node("policy_lookup", lambda state: run_policy_lookup(state, self.deps))

        builder.set_entry_point("intake")

        route_map: dict[Hashable, str] = {
            "verify_identity": "verify_identity",
            "gather_facts": "gather_facts",
            "classify_issue": "classify_issue",
            "policy_lookup": "policy_lookup",
            END_ROUTE: END,
        }
        for node_name in [
            "intake",
            "verify_identity",
            "gather_facts",
            "classify_issue",
            "policy_lookup",
        ]:
            builder.add_conditional_edges(  # type: ignore[arg-type]
                node_name,
                self._route_next_state,
                route_map,
            )

        return builder.compile()

    @staticmethod
    def _route_next_state(state: dict[str, Any]) -> str:
        return str(state.get("next_state") or END_ROUTE)

    def run(self, initial_state: CaseState | dict[str, Any]) -> CaseState:
        payload = (
            initial_state.as_graph_state()
            if isinstance(initial_state, CaseState)
            else CaseState.model_validate(initial_state).as_graph_state()
        )
        result = self._graph.invoke(payload)
        return CaseState.from_graph_state(result)
