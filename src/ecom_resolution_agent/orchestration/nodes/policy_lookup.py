from __future__ import annotations

from ecom_resolution_agent.orchestration.nodes.common import (
    OrchestrationDeps,
    append_error,
    dump_state,
    load_state,
    record_tool_result,
    tool_context,
)
from ecom_resolution_agent.orchestration.state import END_ROUTE


def run_policy_lookup(
    state_payload: dict[str, object],
    deps: OrchestrationDeps,
) -> dict[str, object]:
    state = load_state(state_payload)
    state.current_state = "policy_lookup"

    if not state.issue_type:
        append_error(state, "missing_issue_type")
        state.status = "policy_lookup_failed"
        state.next_state = END_ROUTE
        return dump_state(state)

    policy_version_result = deps.tool_executor.invoke(
        "get_policy_version",
        {"issue_type": state.issue_type, "country": "US"},
        context=tool_context(state=state, actor_agent="policy"),
    )
    record_tool_result(
        state,
        "get_policy_version",
        policy_version_result.model_dump(mode="json"),
    )
    if not policy_version_result.ok or policy_version_result.data is None:
        append_error(state, "get_policy_version_failed")
        state.status = "policy_lookup_failed"
        state.next_state = END_ROUTE
        return dump_state(state)

    policy_version = str(policy_version_result.data["policy_version"])
    state.policy_version = policy_version

    policy_rules_result = deps.tool_executor.invoke(
        "get_policy_rules",
        {"policy_version": policy_version},
        context=tool_context(state=state, actor_agent="policy"),
    )
    record_tool_result(
        state,
        "get_policy_rules",
        policy_rules_result.model_dump(mode="json"),
    )

    policy_output = deps.policy_service.evaluate(
        issue_type=state.issue_type,
        facts=state.facts,
        policy_version=policy_version,
    )
    state.policy_output = policy_output
    state.status = "policy_evaluated"
    state.next_state = END_ROUTE
    return dump_state(state)
