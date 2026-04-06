"""Incident management — detection, diagnosis, remediation proposal, and execution.

The incident lifecycle follows the self-evolution loop from ``INSTRUCTIONS.md``:
    Observe → Diagnose → Propose → Simulate → Apply → Verify → Reflect

For the DevOps context:
    Detect → Diagnose → Propose Remediation → Gate (policy) → Execute → Verify
"""

from __future__ import annotations

from typing import Any

from .models import (
    HealthStatus,
    Incident,
    IncidentDiagnosis,
    IncidentEvent,
    RemediationAction,
    _new_id,
    _utc_now,
)
from .monitor import MonitorEngine
from .policy_engine import DevOpsPolicyEngine


class IncidentManager:
    """AI-assisted incident lifecycle manager."""

    def __init__(
        self,
        monitor: MonitorEngine | None = None,
        policy_engine: DevOpsPolicyEngine | None = None,
    ) -> None:
        self._monitor = monitor or MonitorEngine()
        self._policy = policy_engine or DevOpsPolicyEngine()
        self._incidents: dict[str, Incident] = {}

    # -- CRUD ---------------------------------------------------------------

    @property
    def incidents(self) -> list[Incident]:
        return list(self._incidents.values())

    def get_incident(self, incident_id: str) -> Incident | None:
        return self._incidents.get(incident_id)

    # -- detection ----------------------------------------------------------

    def create_incident_from_health(self, status: HealthStatus) -> Incident:
        """Create an incident from an unhealthy / degraded health status."""

        severity = "critical" if status.status == "unhealthy" else "warning"
        incident = Incident(
            severity=severity,
            source=f"health_check:{status.check_id}",
            title=f"{status.name} is {status.status}",
            description=(
                f"Health check '{status.name}' (id={status.check_id}) reported "
                f"status={status.status} with {status.consecutive_failures} "
                f"consecutive failures. Details: {status.details}"
            ),
            timeline=[
                IncidentEvent(
                    event_type="detected",
                    description=f"Detected via health check: {status.name}",
                    actor="monitor_engine",
                ),
            ],
        )
        self._incidents[incident.incident_id] = incident
        return incident

    def create_incident(
        self,
        title: str,
        description: str,
        severity: str = "warning",
        source: str = "manual",
    ) -> Incident:
        """Manually create an incident."""
        incident = Incident(
            severity=severity,  # type: ignore[arg-type]
            source=source,
            title=title,
            description=description,
            timeline=[
                IncidentEvent(
                    event_type="detected",
                    description=f"Manually created: {title}",
                    actor="operator",
                ),
            ],
        )
        self._incidents[incident.incident_id] = incident
        return incident

    # -- diagnosis ----------------------------------------------------------

    def diagnose(self, incident_id: str) -> IncidentDiagnosis:
        """Generate a diagnosis for an incident.

        In a production system this would invoke an LLM with incident context,
        logs, recent deployments, and metric data.  Here we provide a
        deterministic heuristic-based diagnosis.
        """

        incident = self._incidents.get(incident_id)
        if incident is None:
            raise KeyError(f"Incident not found: {incident_id}")

        incident.status = "investigating"
        incident.timeline.append(IncidentEvent(
            event_type="investigating",
            description="Starting diagnosis.",
            actor="incident_manager",
        ))

        hypotheses = _generate_hypotheses(incident)
        evidence = _gather_evidence(incident)
        confidence = min(0.3 + 0.1 * len(evidence), 0.9)
        blast_radius = _estimate_blast_radius(incident)

        diagnosis = IncidentDiagnosis(
            hypotheses=hypotheses,
            evidence=evidence,
            confidence=confidence,
            blast_radius=blast_radius,
        )
        incident.diagnosis = diagnosis
        return diagnosis

    # -- remediation --------------------------------------------------------

    def propose_remediation(self, incident_id: str) -> list[RemediationAction]:
        """Propose remediation actions based on diagnosis."""

        incident = self._incidents.get(incident_id)
        if incident is None:
            raise KeyError(f"Incident not found: {incident_id}")

        actions = _generate_remediation_actions(incident)
        incident.proposed_actions = actions
        incident.timeline.append(IncidentEvent(
            event_type="note",
            description=f"Proposed {len(actions)} remediation action(s).",
            actor="incident_manager",
        ))
        return actions

    def execute_remediation(
        self,
        incident_id: str,
        action_id: str,
        approver_did: str = "",
    ) -> RemediationAction:
        """Execute a remediation action (with policy gating)."""

        incident = self._incidents.get(incident_id)
        if incident is None:
            raise KeyError(f"Incident not found: {incident_id}")

        action = None
        for a in incident.proposed_actions:
            if a.action_id == action_id:
                action = a
                break
        if action is None:
            raise KeyError(f"Action not found: {action_id}")

        # Policy check
        decision = self._policy.evaluate_remediation(action)
        if not decision.allowed:
            action.status = "proposed"
            incident.timeline.append(IncidentEvent(
                event_type="note",
                description=f"Remediation '{action.description}' blocked: {decision.reason}",
                actor="policy_engine",
            ))
            return action

        # Execute
        incident.status = "mitigating"
        action.status = "executing"
        incident.timeline.append(IncidentEvent(
            event_type="action_taken",
            description=f"Executing remediation: {action.description}",
            actor=approver_did or "incident_manager",
        ))

        # In a real system we'd run the commands here.
        # For the reference implementation, mark as succeeded.
        action.status = "succeeded"
        incident.timeline.append(IncidentEvent(
            event_type="mitigating",
            description=f"Remediation '{action.description}' completed successfully.",
            actor="incident_manager",
        ))

        return action

    # -- resolution ---------------------------------------------------------

    def resolve_incident(self, incident_id: str, resolution_note: str = "") -> Incident:
        """Mark an incident as resolved."""

        incident = self._incidents.get(incident_id)
        if incident is None:
            raise KeyError(f"Incident not found: {incident_id}")

        incident.status = "resolved"
        incident.timeline.append(IncidentEvent(
            event_type="resolved",
            description=resolution_note or "Incident resolved.",
            actor="operator",
        ))
        return incident

    # -- auto-detect from monitor -------------------------------------------

    def detect_incidents_from_monitor(self) -> list[Incident]:
        """Run health checks and auto-create incidents for unhealthy statuses."""

        statuses = self._monitor.run_health_checks()
        new_incidents: list[Incident] = []

        for status in statuses:
            if status.status in ("unhealthy", "degraded"):
                # Avoid duplicate incidents for same check
                already_open = any(
                    inc.source == f"health_check:{status.check_id}"
                    and inc.status != "resolved"
                    for inc in self._incidents.values()
                )
                if not already_open:
                    incident = self.create_incident_from_health(status)
                    new_incidents.append(incident)

        return new_incidents


# ---------------------------------------------------------------------------
# Heuristic helpers (placeholder for LLM-powered diagnosis)
# ---------------------------------------------------------------------------

def _generate_hypotheses(incident: Incident) -> list[str]:
    """Generate diagnostic hypotheses from incident metadata."""
    hypotheses = []

    if "health_check" in incident.source:
        hypotheses.append("Application process may have crashed or become unresponsive.")
        hypotheses.append("Network connectivity issue between monitor and target.")
        hypotheses.append("Resource exhaustion (CPU/memory/disk) on the target host.")

    if incident.severity == "critical":
        hypotheses.append("Recent deployment may have introduced a breaking change.")
        hypotheses.append("External dependency (database, cache, queue) may be unavailable.")

    if not hypotheses:
        hypotheses.append("Cause unknown — manual investigation required.")

    return hypotheses


def _gather_evidence(incident: Incident) -> list[str]:
    """Gather evidence from incident context."""
    evidence = []
    evidence.append(f"Source: {incident.source}")
    evidence.append(f"Severity: {incident.severity}")
    evidence.append(f"Description: {incident.description[:200]}")
    return evidence


def _estimate_blast_radius(incident: Incident) -> str:
    """Estimate the blast radius of an incident."""
    if incident.severity == "critical":
        return "service-wide"
    if incident.severity == "warning":
        return "partial"
    return "minimal"


def _generate_remediation_actions(incident: Incident) -> list[RemediationAction]:
    """Generate remediation action proposals based on incident analysis."""
    actions: list[RemediationAction] = []

    # Always suggest restart as low-risk first step
    actions.append(RemediationAction(
        description="Restart the affected service",
        action_type="restart",
        risk_level="low",
        requires_approval=False,
        commands=["systemctl restart <service>"],
    ))

    if incident.severity == "critical":
        # Suggest rollback for critical incidents
        actions.append(RemediationAction(
            description="Rollback to the last known-good deployment",
            action_type="rollback",
            risk_level="medium",
            requires_approval=True,
            commands=["rollback --to-version previous"],
            compensator_commands=["deploy --version current"],
        ))

    # Always suggest scaling as an option
    actions.append(RemediationAction(
        description="Scale up the service for additional capacity",
        action_type="scale",
        risk_level="low",
        requires_approval=False,
        commands=["scale --replicas +2"],
    ))

    return actions
