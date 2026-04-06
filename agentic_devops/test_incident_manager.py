"""Tests for agentic_devops.incident_manager — incident lifecycle."""

from __future__ import annotations

import pytest

from agentic_devops.incident_manager import IncidentManager
from agentic_devops.models import HealthCheck, HealthStatus, RemediationAction
from agentic_devops.monitor import MonitorEngine
from agentic_devops.policy_engine import DevOpsPolicyEngine


class TestIncidentCreation:
    def test_create_from_health(self) -> None:
        mgr = IncidentManager()
        status = HealthStatus(
            check_id="c1", name="api_health",
            status="unhealthy", consecutive_failures=5,
            details={"error": "connection refused"},
        )
        incident = mgr.create_incident_from_health(status)
        assert incident.severity == "critical"
        assert incident.status == "open"
        assert "api_health" in incident.title
        assert len(incident.timeline) == 1
        assert incident.timeline[0].event_type == "detected"

    def test_create_from_degraded(self) -> None:
        mgr = IncidentManager()
        status = HealthStatus(check_id="c2", name="cache", status="degraded")
        incident = mgr.create_incident_from_health(status)
        assert incident.severity == "warning"

    def test_create_manual(self) -> None:
        mgr = IncidentManager()
        incident = mgr.create_incident("Disk full", "Root partition at 95%", severity="critical")
        assert incident.title == "Disk full"
        assert incident.source == "manual"

    def test_list_incidents(self) -> None:
        mgr = IncidentManager()
        mgr.create_incident("A", "desc1")
        mgr.create_incident("B", "desc2")
        assert len(mgr.incidents) == 2


class TestDiagnosis:
    def test_diagnose(self) -> None:
        mgr = IncidentManager()
        status = HealthStatus(check_id="c1", name="api", status="unhealthy")
        incident = mgr.create_incident_from_health(status)
        diagnosis = mgr.diagnose(incident.incident_id)
        assert len(diagnosis.hypotheses) > 0
        assert len(diagnosis.evidence) > 0
        assert diagnosis.confidence > 0
        assert incident.status == "investigating"
        # Timeline should have investigating event
        assert any(e.event_type == "investigating" for e in incident.timeline)

    def test_diagnose_not_found(self) -> None:
        mgr = IncidentManager()
        with pytest.raises(KeyError):
            mgr.diagnose("nonexistent")


class TestRemediation:
    def test_propose_remediation(self) -> None:
        mgr = IncidentManager()
        status = HealthStatus(check_id="c1", name="api", status="unhealthy")
        incident = mgr.create_incident_from_health(status)
        mgr.diagnose(incident.incident_id)
        actions = mgr.propose_remediation(incident.incident_id)
        assert len(actions) >= 1
        # Should have restart as first option
        assert any(a.action_type == "restart" for a in actions)

    def test_critical_incident_gets_rollback_option(self) -> None:
        mgr = IncidentManager()
        status = HealthStatus(check_id="c1", name="api", status="unhealthy")
        incident = mgr.create_incident_from_health(status)
        assert incident.severity == "critical"
        actions = mgr.propose_remediation(incident.incident_id)
        assert any(a.action_type == "rollback" for a in actions)

    def test_execute_remediation(self) -> None:
        mgr = IncidentManager(policy_engine=DevOpsPolicyEngine())
        incident = mgr.create_incident("test", "test incident")
        actions = mgr.propose_remediation(incident.incident_id)
        # Find a non-approval-requiring action
        auto_action = next((a for a in actions if not a.requires_approval), None)
        assert auto_action is not None
        result = mgr.execute_remediation(incident.incident_id, auto_action.action_id)
        assert result.status == "succeeded"
        assert incident.status == "mitigating"

    def test_propose_not_found(self) -> None:
        mgr = IncidentManager()
        with pytest.raises(KeyError):
            mgr.propose_remediation("nonexistent")


class TestResolution:
    def test_resolve_incident(self) -> None:
        mgr = IncidentManager()
        incident = mgr.create_incident("test", "test")
        resolved = mgr.resolve_incident(incident.incident_id, "Fixed by restart")
        assert resolved.status == "resolved"
        assert any(e.event_type == "resolved" for e in resolved.timeline)

    def test_resolve_not_found(self) -> None:
        mgr = IncidentManager()
        with pytest.raises(KeyError):
            mgr.resolve_incident("nonexistent")


class TestAutoDetection:
    def test_detect_from_monitor(self) -> None:
        monitor = MonitorEngine(checks=[
            HealthCheck(check_id="c1", name="api", check_type="command", target="false", failure_threshold=1),
        ])
        mgr = IncidentManager(monitor=monitor)
        incidents = mgr.detect_incidents_from_monitor()
        assert len(incidents) == 1
        assert incidents[0].severity in ("critical", "warning")

    def test_no_duplicate_incidents(self) -> None:
        monitor = MonitorEngine(checks=[
            HealthCheck(check_id="c1", name="api", check_type="command", target="false", failure_threshold=1),
        ])
        mgr = IncidentManager(monitor=monitor)
        mgr.detect_incidents_from_monitor()
        # Second call should not create duplicates
        incidents = mgr.detect_incidents_from_monitor()
        assert len(incidents) == 0
        assert len(mgr.incidents) == 1

    def test_healthy_creates_no_incidents(self) -> None:
        monitor = MonitorEngine(checks=[
            HealthCheck(check_id="c1", name="api", check_type="command", target="true"),
        ])
        mgr = IncidentManager(monitor=monitor)
        incidents = mgr.detect_incidents_from_monitor()
        assert len(incidents) == 0
