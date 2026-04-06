"""Tests for agentic_devops.models — all core data models."""

from __future__ import annotations

from agentic_devops.models import (
    DeployApprovalConfig,
    DeployEnvironment,
    DeployPolicyDecision,
    DeployPolicyMatcher,
    DeployPolicyRule,
    DeployProfile,
    HealthCheck,
    HealthStatus,
    Incident,
    IncidentDiagnosis,
    IncidentEvent,
    PipelineDefinition,
    PipelineProvenance,
    PipelineRun,
    PipelineStage,
    PipelineTrigger,
    RemediationAction,
    RollbackStrategy,
    StageExecution,
)


class TestDeployProfile:
    def test_defaults(self) -> None:
        p = DeployProfile(app_name="myapp")
        assert p.app_name == "myapp"
        assert p.deploy_method == "docker"
        assert p.environments == []

    def test_template_context(self) -> None:
        p = DeployProfile(
            app_name="myapp",
            deploy_method="k8s",
            ci_system="github_actions",
            environments=[
                DeployEnvironment(name="prod", protection_level="restricted"),
            ],
        )
        ctx = p.to_template_context()
        assert ctx["APP_NAME"] == "myapp"
        assert ctx["DEPLOY_METHOD"] == "k8s"
        assert ctx["ENVIRONMENT_COUNT"] == "1"
        assert "prod" in ctx["ENVIRONMENT_LIST"]

    def test_serialization(self) -> None:
        p = DeployProfile(app_name="test", deploy_method="docker")
        restored = DeployProfile.model_validate_json(p.model_dump_json())
        assert restored.app_name == "test"


class TestPipelineModels:
    def test_pipeline_definition(self) -> None:
        pipeline = PipelineDefinition(
            name="ci",
            stages=[
                PipelineStage(name="build", stage_type="build", commands=["make build"]),
                PipelineStage(name="test", stage_type="test", commands=["make test"]),
            ],
        )
        assert len(pipeline.stages) == 2
        assert pipeline.trigger.trigger_type == "push"
        assert pipeline.rollback_strategy.strategy_type == "redeploy_previous"

    def test_pipeline_run(self) -> None:
        run = PipelineRun(pipeline_id="p1", trigger_event="push")
        assert run.status == "queued"
        assert run.finished_at is None

    def test_stage_execution(self) -> None:
        se = StageExecution(stage_id="s1", stage_name="build")
        assert se.status == "pending"

    def test_pipeline_trigger(self) -> None:
        t = PipelineTrigger(trigger_type="schedule", cron="0 0 * * *")
        assert t.cron == "0 0 * * *"

    def test_rollback_strategy(self) -> None:
        rs = RollbackStrategy(max_rollback_depth=5, auto_rollback_on_failure=False)
        assert rs.max_rollback_depth == 5


class TestHealthModels:
    def test_health_check(self) -> None:
        hc = HealthCheck(name="api_health", check_type="http", target="http://localhost/health")
        assert hc.interval_seconds == 30
        assert hc.failure_threshold == 3

    def test_health_status(self) -> None:
        hs = HealthStatus(check_id="c1", name="api", status="healthy")
        assert hs.consecutive_failures == 0


class TestIncidentModels:
    def test_incident_creation(self) -> None:
        inc = Incident(
            severity="critical",
            source="health_check:c1",
            title="Service down",
            description="API is not responding",
        )
        assert inc.status == "open"
        assert inc.diagnosis is None

    def test_incident_diagnosis(self) -> None:
        diag = IncidentDiagnosis(
            hypotheses=["OOM kill", "Config error"],
            evidence=["Memory usage 98%"],
            confidence=0.7,
            blast_radius="service-wide",
        )
        assert len(diag.hypotheses) == 2

    def test_remediation_action(self) -> None:
        action = RemediationAction(
            description="Restart service",
            action_type="restart",
            risk_level="low",
            requires_approval=False,
        )
        assert action.status == "proposed"

    def test_incident_event(self) -> None:
        event = IncidentEvent(event_type="detected", description="Found by monitor")
        assert event.actor == ""


class TestPolicyModels:
    def test_deploy_policy_rule(self) -> None:
        rule = DeployPolicyRule(
            match=DeployPolicyMatcher(environments=["production"]),
            action="require_approval",
        )
        assert rule.action == "require_approval"

    def test_deploy_policy_decision(self) -> None:
        d = DeployPolicyDecision(allowed=False, action="deny", reason="blocked")
        assert not d.allowed
