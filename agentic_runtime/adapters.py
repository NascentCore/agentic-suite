"""Framework adapters — PydanticAI agent and LangGraph graph for runtime interaction.

Architecture follows the same port-adapter pattern as ``amcp/adapters.py``:

- **Layer 1** — framework-agnostic core (models, policy, executor)
- **Layer 2** — adapter ports (this file)
- **Layer 3** — framework-specific runtime (PydanticAI / LangGraph)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, TypedDict

from .executor import RuntimeExecutor
from .models import (
    ActionRequest,
    ActionResponse,
    PolicyDecision,
    RuntimeProfile,
    _new_id,
)
from .policy_engine import RuntimePolicyEngine
from .tool_registry import ToolRegistry


# ---------------------------------------------------------------------------
# PydanticAI adapter
# ---------------------------------------------------------------------------

@dataclass
class RuntimeAgentDeps:
    """Dependency carrier injected into PydanticAI tool functions."""

    executor: RuntimeExecutor
    registry: ToolRegistry
    policy_engine: RuntimePolicyEngine
    user_did: str = ""
    session_id: str = ""
    attempts: list[dict[str, Any]] = field(default_factory=list)


def create_runtime_pydantic_agent(
    profile: RuntimeProfile,
    policy_engine: RuntimePolicyEngine | None = None,
    model: Any = "test",
) -> Any:
    """Create a PydanticAI ``Agent`` with one tool per runtime capability.

    Each capability is registered as a PydanticAI tool that goes through the
    full policy → execute → provenance pipeline.

    Returns the ``Agent`` instance.  Import is deferred so that pydantic-ai
    remains an optional dependency.
    """

    from pydantic_ai import Agent, RunContext  # type: ignore[import-untyped]

    engine = policy_engine or RuntimePolicyEngine()
    registry = ToolRegistry(app_name=profile.app_name)
    registry.refresh_from_profile(profile)
    executor = RuntimeExecutor(registry=registry, policy_engine=engine)

    agent: Agent[RuntimeAgentDeps, str] = Agent(
        model,
        deps_type=RuntimeAgentDeps,
        output_type=str,
        retries=1,
        instructions=(
            f"You are the runtime agent for **{profile.app_name}**. "
            "Use the available tools to fulfil user requests. "
            "If a tool requires approval, inform the user."
        ),
    )

    @agent.tool
    def invoke_runtime_tool(
        ctx: RunContext[RuntimeAgentDeps],
        tool_name: str,
        parameters: dict[str, Any] | None = None,
    ) -> str:
        """Invoke a registered runtime tool by name."""

        manifest = ctx.deps.registry.get_by_name(tool_name)
        if manifest is None:
            return f"ERROR: tool '{tool_name}' not found in registry."

        request = ActionRequest(
            tool_id=manifest.tool_id,
            parameters=parameters or {},
            requester_did=ctx.deps.user_did,
            purpose="runtime_interaction",
        )
        response = ctx.deps.executor.execute(request)

        ctx.deps.attempts.append({
            "tool_name": tool_name,
            "status": response.status,
            "result": response.result,
            "error": response.error,
        })

        if response.status == "success":
            return f"OK: {response.result}"
        if response.status == "requires_approval":
            return f"APPROVAL_REQUIRED: token={response.approval_token}"
        return f"FAILED: {response.error}"

    @agent.tool
    def list_available_tools(ctx: RunContext[RuntimeAgentDeps]) -> str:
        """List all tools available in the registry."""
        tools = ctx.deps.registry.tools
        if not tools:
            return "No tools available."
        lines = [f"- {t.name} ({t.risk_level}): {t.description}" for t in tools]
        return "\n".join(lines)

    return agent


# ---------------------------------------------------------------------------
# LangGraph adapter
# ---------------------------------------------------------------------------

class RuntimeLangGraphState(TypedDict):
    """Shared state for the runtime LangGraph application."""

    user_did: str
    tool_name: str
    parameters: dict[str, Any]
    policy_decision: PolicyDecision | None
    action_response: ActionResponse | None
    route: str
    result: str


def build_runtime_langgraph_app(
    profile: RuntimeProfile,
    policy_engine: RuntimePolicyEngine | None = None,
) -> Any:
    """Build a compiled LangGraph ``StateGraph`` for runtime interaction.

    Nodes:
        intent_resolve_node → policy_check_node → execute_node / approval_node / error_node

    Returns a compiled LangGraph app.
    """

    from langgraph.graph import END, START, StateGraph  # type: ignore[import-untyped]

    engine = policy_engine or RuntimePolicyEngine()
    registry = ToolRegistry(app_name=profile.app_name)
    registry.refresh_from_profile(profile)
    executor = RuntimeExecutor(registry=registry, policy_engine=engine)

    def intent_resolve_node(state: RuntimeLangGraphState) -> dict:
        """Resolve tool_name to a tool manifest."""
        manifest = registry.get_by_name(state["tool_name"])
        if manifest is None:
            return {"route": "error_node", "result": f"Tool not found: {state['tool_name']}"}
        return {}

    def policy_check_node(state: RuntimeLangGraphState) -> dict:
        """Evaluate policy for the requested tool."""
        manifest = registry.get_by_name(state["tool_name"])
        if manifest is None:
            return {
                "policy_decision": PolicyDecision(
                    allowed=False, action="deny", reason="Tool not found."
                )
            }
        request = ActionRequest(
            tool_id=manifest.tool_id,
            parameters=state["parameters"],
            requester_did=state["user_did"],
            purpose="runtime_interaction",
        )
        decision = engine.evaluate(request, registry)
        return {"policy_decision": decision}

    def execute_node(state: RuntimeLangGraphState) -> dict:
        """Execute the tool."""
        manifest = registry.get_by_name(state["tool_name"])
        if manifest is None:
            return {"route": "error_node", "result": "Tool not found."}
        request = ActionRequest(
            tool_id=manifest.tool_id,
            parameters=state["parameters"],
            requester_did=state["user_did"],
            purpose="runtime_interaction",
        )
        response = executor.execute(request)
        return {
            "action_response": response,
            "route": "execute_node",
            "result": f"{response.status}: {response.result or response.error}",
        }

    def approval_node(state: RuntimeLangGraphState) -> dict:
        """Handle tools that require human approval."""
        decision = state["policy_decision"]
        token = decision.approval_token if decision else None
        return {
            "route": "approval_node",
            "result": f"Approval required. Token: {token}",
        }

    def error_node(state: RuntimeLangGraphState) -> dict:
        """Handle errors."""
        decision = state["policy_decision"]
        reason = decision.reason if decision else "Unknown error."
        return {
            "route": "error_node",
            "result": f"Denied: {reason}",
        }

    def route_by_policy(state: RuntimeLangGraphState) -> str:
        decision = state.get("policy_decision")
        if decision is None:
            return "error_node"
        if decision.allowed:
            return "execute_node"
        if decision.action == "require_approval":
            return "approval_node"
        return "error_node"

    graph = StateGraph(RuntimeLangGraphState)
    graph.add_node("intent_resolve_node", intent_resolve_node)
    graph.add_node("policy_check_node", policy_check_node)
    graph.add_node("execute_node", execute_node)
    graph.add_node("approval_node", approval_node)
    graph.add_node("error_node", error_node)

    graph.add_edge(START, "intent_resolve_node")
    graph.add_edge("intent_resolve_node", "policy_check_node")
    graph.add_conditional_edges(
        "policy_check_node",
        route_by_policy,
        {
            "execute_node": "execute_node",
            "approval_node": "approval_node",
            "error_node": "error_node",
        },
    )
    graph.add_edge("execute_node", END)
    graph.add_edge("approval_node", END)
    graph.add_edge("error_node", END)

    return graph.compile()
