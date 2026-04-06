"""Framework adapters — PydanticAI agent and LangGraph graph for DevOps operations.

Same port-adapter architecture as ``amcp/adapters.py`` and
``agentic_runtime/adapters.py``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, TypedDict

from .models import (
    DeployPolicyDecision,
    DeployProfile,
    PipelineDefinition,
    _new_id,
)
from .incident_manager import IncidentManager
from .monitor import MonitorEngine
from .pipeline_engine import PipelineEngine
from .policy_engine import DevOpsPolicyEngine
from .rollback import RollbackEngine


# ---------------------------------------------------------------------------
# PydanticAI adapter
# ---------------------------------------------------------------------------

@dataclass
class DevOpsAgentDeps:
    """Dependency carrier injected into PydanticAI tool functions."""

    pipeline_engine: PipelineEngine
    monitor: MonitorEngine
    incident_manager: IncidentManager
    rollback_engine: RollbackEngine
    policy_engine: DevOpsPolicyEngine
    deploy_profile: DeployProfile
    pipeline_definition: PipelineDefinition | None = None
    requester_did: str = ""
    attempts: list[dict[str, Any]] = field(default_factory=list)


def create_devops_pydantic_agent(
    profile: DeployProfile,
    pipeline_definition: PipelineDefinition | None = None,
    model: Any = "test",
) -> Any:
    """Create a PydanticAI ``Agent`` with DevOps tools.

    Tools:
    - ``deploy`` — execute a pipeline
    - ``check_health`` — run health checks
    - ``list_incidents`` — list open incidents
    - ``diagnose_incident`` — diagnose an incident
    - ``rollback`` — rollback a deployment
    """

    from pydantic_ai import Agent, RunContext  # type: ignore[import-untyped]

    policy = DevOpsPolicyEngine()
    monitor = MonitorEngine()
    pipeline_engine = PipelineEngine(policy_engine=policy)
    incident_manager = IncidentManager(monitor=monitor, policy_engine=policy)
    rollback_engine = RollbackEngine(policy_engine=policy)

    agent: Agent[DevOpsAgentDeps, str] = Agent(
        model,
        deps_type=DevOpsAgentDeps,
        output_type=str,
        retries=1,
        instructions=(
            f"You are the DevOps agent for **{profile.app_name}**. "
            "Use the available tools to manage deployments, monitor health, "
            "and respond to incidents."
        ),
    )

    @agent.tool
    def deploy(
        ctx: RunContext[DevOpsAgentDeps],
        environment: str = "staging",
    ) -> str:
        """Execute the deployment pipeline."""
        if ctx.deps.pipeline_definition is None:
            return "ERROR: No pipeline definition configured."
        run = ctx.deps.pipeline_engine.execute_pipeline(
            ctx.deps.pipeline_definition,
            environment=environment,
            requester_did=ctx.deps.requester_did,
        )
        ctx.deps.attempts.append({"action": "deploy", "run_id": run.run_id, "status": run.status})
        return f"Pipeline {run.run_id}: {run.status}"

    @agent.tool
    def check_health(ctx: RunContext[DevOpsAgentDeps]) -> str:
        """Run health checks and return status."""
        overall = ctx.deps.monitor.evaluate_overall_health()
        statuses = ctx.deps.monitor.run_health_checks()
        lines = [f"Overall: {overall}"]
        for s in statuses:
            lines.append(f"  {s.name}: {s.status} (failures={s.consecutive_failures})")
        return "\n".join(lines)

    @agent.tool
    def list_incidents(ctx: RunContext[DevOpsAgentDeps]) -> str:
        """List all open incidents."""
        incidents = ctx.deps.incident_manager.incidents
        if not incidents:
            return "No incidents."
        lines = []
        for inc in incidents:
            lines.append(f"  [{inc.severity}] {inc.incident_id}: {inc.title} ({inc.status})")
        return "\n".join(lines)

    @agent.tool
    def diagnose_incident(ctx: RunContext[DevOpsAgentDeps], incident_id: str) -> str:
        """Diagnose an incident."""
        try:
            diagnosis = ctx.deps.incident_manager.diagnose(incident_id)
            return (
                f"Hypotheses: {diagnosis.hypotheses}\n"
                f"Evidence: {diagnosis.evidence}\n"
                f"Confidence: {diagnosis.confidence}\n"
                f"Blast radius: {diagnosis.blast_radius}"
            )
        except KeyError:
            return f"ERROR: Incident {incident_id} not found."

    @agent.tool
    def rollback(
        ctx: RunContext[DevOpsAgentDeps],
        environment: str = "staging",
        depth: int = 1,
    ) -> str:
        """Rollback to a previous deployment version."""
        result = ctx.deps.rollback_engine.execute_rollback(environment, depth, ctx.deps.requester_did)
        ctx.deps.attempts.append({"action": "rollback", "result": result})
        if result.get("success"):
            return f"Rollback successful: {result.get('to_version', {}).get('version_id', 'unknown')}"
        return f"Rollback failed: {result.get('reason', 'unknown')}"

    return agent


# ---------------------------------------------------------------------------
# LangGraph adapter
# ---------------------------------------------------------------------------

class DevOpsLangGraphState(TypedDict):
    """Shared state for the DevOps LangGraph application."""

    action: str  # "deploy", "monitor", "diagnose", "rollback"
    environment: str
    incident_id: str
    policy_decision: DeployPolicyDecision | None
    route: str
    result: str


def build_devops_langgraph_app(
    profile: DeployProfile,
    pipeline_definition: PipelineDefinition | None = None,
) -> Any:
    """Build a compiled LangGraph ``StateGraph`` for DevOps operations.

    Nodes:
        action_router → deploy_node / monitor_node / diagnose_node / rollback_node
    """

    from langgraph.graph import END, START, StateGraph  # type: ignore[import-untyped]

    policy = DevOpsPolicyEngine()
    monitor = MonitorEngine()
    pipeline_engine = PipelineEngine(policy_engine=policy)
    incident_manager = IncidentManager(monitor=monitor, policy_engine=policy)
    rollback_engine = RollbackEngine(policy_engine=policy)

    def action_router(state: DevOpsLangGraphState) -> dict:
        return {}

    def deploy_node(state: DevOpsLangGraphState) -> dict:
        if pipeline_definition is None:
            return {"route": "deploy_node", "result": "No pipeline definition."}
        run = pipeline_engine.execute_pipeline(
            pipeline_definition,
            environment=state.get("environment", "staging"),
        )
        return {"route": "deploy_node", "result": f"Pipeline {run.run_id}: {run.status}"}

    def monitor_node(state: DevOpsLangGraphState) -> dict:
        overall = monitor.evaluate_overall_health()
        return {"route": "monitor_node", "result": f"Overall health: {overall}"}

    def diagnose_node(state: DevOpsLangGraphState) -> dict:
        inc_id = state.get("incident_id", "")
        if not inc_id:
            return {"route": "diagnose_node", "result": "No incident_id provided."}
        try:
            diagnosis = incident_manager.diagnose(inc_id)
            return {"route": "diagnose_node", "result": f"Diagnosis: {diagnosis.hypotheses}"}
        except KeyError:
            return {"route": "diagnose_node", "result": f"Incident {inc_id} not found."}

    def rollback_node(state: DevOpsLangGraphState) -> dict:
        env = state.get("environment", "staging")
        result = rollback_engine.execute_rollback(env)
        return {"route": "rollback_node", "result": f"Rollback: {result}"}

    def route_by_action(state: DevOpsLangGraphState) -> str:
        action = state.get("action", "monitor")
        if action == "deploy":
            return "deploy_node"
        if action == "diagnose":
            return "diagnose_node"
        if action == "rollback":
            return "rollback_node"
        return "monitor_node"

    graph = StateGraph(DevOpsLangGraphState)
    graph.add_node("action_router", action_router)
    graph.add_node("deploy_node", deploy_node)
    graph.add_node("monitor_node", monitor_node)
    graph.add_node("diagnose_node", diagnose_node)
    graph.add_node("rollback_node", rollback_node)

    graph.add_edge(START, "action_router")
    graph.add_conditional_edges(
        "action_router",
        route_by_action,
        {
            "deploy_node": "deploy_node",
            "monitor_node": "monitor_node",
            "diagnose_node": "diagnose_node",
            "rollback_node": "rollback_node",
        },
    )
    graph.add_edge("deploy_node", END)
    graph.add_edge("monitor_node", END)
    graph.add_edge("diagnose_node", END)
    graph.add_edge("rollback_node", END)

    return graph.compile()
