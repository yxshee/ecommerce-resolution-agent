from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ecom_resolution_agent.agents.triage import DeterministicTriageAgent
from ecom_resolution_agent.orchestration.state import CaseState
from ecom_resolution_agent.policy.service import PolicyService
from ecom_resolution_agent.schemas.tool_envelopes import ToolCallContext
from ecom_resolution_agent.tools.executor import ToolExecutor


@dataclass
class OrchestrationDeps:
    tool_executor: ToolExecutor
    policy_service: PolicyService
    triage_agent: DeterministicTriageAgent
    default_policy_version: str = "v1_0_0"


def load_state(payload: dict[str, Any]) -> CaseState:
    return CaseState.from_graph_state(payload)


def dump_state(state: CaseState) -> dict[str, Any]:
    return state.as_graph_state()


def tool_context(*, state: CaseState, actor_agent: str) -> ToolCallContext:
    return ToolCallContext(
        run_id=state.run_id,
        actor_agent=actor_agent,
        simulation_mode=state.simulation_mode,
    )


def record_tool_result(state: CaseState, tool_name: str, result: dict[str, Any]) -> None:
    state.tool_results[tool_name] = result


def append_error(state: CaseState, message: str) -> None:
    state.errors.append(message)
