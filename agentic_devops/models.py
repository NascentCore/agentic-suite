"""Core data models for the Agentic DevOps layer.

Design reference
----------------
- **DeployProfile / DeployEnvironment** mirror ``RepoProfile`` and ``RuntimeProfile``
  but describe the *deployment infrastructure* of an application.
- **PipelineDefinition / PipelineStage** implement the *Planner-Executor* (§2.C) and
  *Saga with Compensating Actions* (§2.F) patterns from ``BRAIN_STORM.md``.
- **HealthCheck / HealthStatus** support the *Observability Layer* (§4.6).
- **Incident / IncidentDiagnosis / RemediationAction** model the full incident lifecycle.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# Deploy Profile
# ---------------------------------------------------------------------------

class DeployEnvironment(BaseModel):
    """A single deployment environment (dev, staging, production, etc.)."""

    model_config = ConfigDict(extra="forbid")

    name: str
    protection_level: Literal["none", "approval_required", "restricted"] = "none"
    url: str | None = None
    health_endpoint: str | None = None


class DeployProfile(BaseModel):
    """Deployment infrastructure profile — analogous to ``RepoProfile`` / ``RuntimeProfile``."""

    model_config = ConfigDict(extra="forbid")

    app_name: str
    repo_path: str = ""
    deploy_method: Literal["docker", "k8s", "serverless", "bare_metal", "custom"] = "docker"
    ci_system: Literal["github_actions", "gitlab_ci", "jenkins", "custom"] | None = None
    environments: list[DeployEnvironment] = Field(default_factory=list)
    artifact_type: Literal["container_image", "binary", "package", "static_files"] = "container_image"
    discovered_at: datetime = Field(default_factory=_utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def to_template_context(self) -> dict[str, str]:
        env_bullets = "\n".join(
            f"- **{e.name}** (protection={e.protection_level}, url={e.url or 'N/A'})"
            for e in self.environments
        ) or "- No environments detected."
        return {
            "APP_NAME": self.app_name,
            "REPO_PATH": self.repo_path,
            "DEPLOY_METHOD": self.deploy_method,
            "CI_SYSTEM": self.ci_system or "unknown",
            "ARTIFACT_TYPE": self.artifact_type,
            "ENVIRONMENT_LIST": env_bullets,
            "ENVIRONMENT_COUNT": str(len(self.environments)),
        }


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

class PipelineTrigger(BaseModel):
    """What triggers a pipeline run."""

    model_config = ConfigDict(extra="forbid")

    trigger_type: Literal["push", "pr", "manual", "schedule", "webhook"] = "push"
    branch_pattern: str | None = None
    cron: str | None = None


class RollbackStrategy(BaseModel):
    """How to roll back a failed deployment."""

    model_config = ConfigDict(extra="forbid")

    strategy_type: Literal["revert_commit", "redeploy_previous", "blue_green_switch", "manual"] = "redeploy_previous"
    max_rollback_depth: int = 3
    auto_rollback_on_failure: bool = True


class PipelineStage(BaseModel):
    """A single stage in a CI/CD pipeline."""

    model_config = ConfigDict(extra="forbid")

    stage_id: str = Field(default_factory=_new_id)
    name: str
    stage_type: Literal["build", "test", "security_scan", "deploy", "verify", "notify"] = "build"
    commands: list[str] = Field(default_factory=list)
    compensator_commands: list[str] = Field(default_factory=list)
    timeout_ms: int = 300_000  # 5 minutes default
    requires_approval: bool = False
    depends_on: list[str] = Field(default_factory=list)
    environment: str | None = None


class PipelineDefinition(BaseModel):
    """A complete CI/CD pipeline definition."""

    model_config = ConfigDict(extra="forbid")

    pipeline_id: str = Field(default_factory=_new_id)
    name: str
    stages: list[PipelineStage] = Field(default_factory=list)
    trigger: PipelineTrigger = Field(default_factory=PipelineTrigger)
    rollback_strategy: RollbackStrategy = Field(default_factory=RollbackStrategy)


# ---------------------------------------------------------------------------
# Pipeline Execution
# ---------------------------------------------------------------------------

class StageExecution(BaseModel):
    """Record of a single stage execution within a pipeline run."""

    model_config = ConfigDict(extra="forbid")

    stage_id: str
    stage_name: str
    status: Literal["pending", "running", "succeeded", "failed", "skipped", "compensated"] = "pending"
    started_at: datetime | None = None
    finished_at: datetime | None = None
    output: str = ""
    error: str = ""


class PipelineProvenance(BaseModel):
    """Provenance record for a full pipeline run."""

    model_config = ConfigDict(extra="forbid")

    commit_sha: str = ""
    branch: str = ""
    triggered_by: str = ""
    policy_decisions: list[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=_utc_now)


class PipelineRun(BaseModel):
    """A single pipeline execution record."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(default_factory=_new_id)
    pipeline_id: str = ""
    trigger_event: str = ""
    status: Literal["queued", "running", "succeeded", "failed", "cancelled", "rolling_back"] = "queued"
    stages: list[StageExecution] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=_utc_now)
    finished_at: datetime | None = None
    provenance: PipelineProvenance = Field(default_factory=PipelineProvenance)


# ---------------------------------------------------------------------------
# Health Monitoring
# ---------------------------------------------------------------------------

class HealthCheck(BaseModel):
    """Definition of a health check probe."""

    model_config = ConfigDict(extra="forbid")

    check_id: str = Field(default_factory=_new_id)
    name: str
    check_type: Literal["http", "tcp", "command", "metric_threshold"] = "http"
    target: str = ""
    interval_seconds: int = 30
    timeout_seconds: int = 5
    failure_threshold: int = 3


class HealthStatus(BaseModel):
    """Point-in-time health status from a single check."""

    model_config = ConfigDict(extra="forbid")

    check_id: str
    name: str = ""
    status: Literal["healthy", "degraded", "unhealthy", "unknown"] = "unknown"
    last_checked: datetime = Field(default_factory=_utc_now)
    consecutive_failures: int = 0
    details: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Incident Management
# ---------------------------------------------------------------------------

class IncidentEvent(BaseModel):
    """A timestamped event in the incident timeline."""

    model_config = ConfigDict(extra="forbid")

    event_id: str = Field(default_factory=_new_id)
    timestamp: datetime = Field(default_factory=_utc_now)
    event_type: Literal["detected", "investigating", "mitigating", "action_taken", "resolved", "note"] = "note"
    description: str = ""
    actor: str = ""


class IncidentDiagnosis(BaseModel):
    """AI-assisted diagnosis of an incident."""

    model_config = ConfigDict(extra="forbid")

    hypotheses: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    blast_radius: str = "unknown"
    diagnosed_at: datetime = Field(default_factory=_utc_now)


class RemediationAction(BaseModel):
    """A proposed or executed remediation action."""

    model_config = ConfigDict(extra="forbid")

    action_id: str = Field(default_factory=_new_id)
    description: str = ""
    action_type: Literal["rollback", "scale", "restart", "config_change", "hotfix", "manual"] = "manual"
    risk_level: Literal["low", "medium", "high"] = "medium"
    requires_approval: bool = True
    commands: list[str] = Field(default_factory=list)
    compensator_commands: list[str] = Field(default_factory=list)
    status: Literal["proposed", "approved", "executing", "succeeded", "failed"] = "proposed"


class Incident(BaseModel):
    """Full incident record."""

    model_config = ConfigDict(extra="forbid")

    incident_id: str = Field(default_factory=_new_id)
    severity: Literal["info", "warning", "critical"] = "warning"
    source: str = ""
    title: str = ""
    description: str = ""
    detected_at: datetime = Field(default_factory=_utc_now)
    status: Literal["open", "investigating", "mitigating", "resolved"] = "open"
    diagnosis: IncidentDiagnosis | None = None
    proposed_actions: list[RemediationAction] = Field(default_factory=list)
    timeline: list[IncidentEvent] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# DevOps Policy
# ---------------------------------------------------------------------------

class DeployPolicyMatcher(BaseModel):
    """Matching predicate for a DevOps policy rule."""

    model_config = ConfigDict(extra="forbid")

    environments: list[str] | None = None
    stage_types: list[str] | None = None
    severity_levels: list[str] | None = None
    requester_dids: list[str] | None = None


class DeployApprovalConfig(BaseModel):
    """Approval parameters for deployment gates."""

    model_config = ConfigDict(extra="forbid")

    approver_dids: list[str] = Field(default_factory=list)
    timeout_seconds: int = 600
    auto_deny_on_timeout: bool = True


class DeployPolicyRule(BaseModel):
    """A single DevOps policy rule."""

    model_config = ConfigDict(extra="forbid")

    rule_id: str = Field(default_factory=_new_id)
    match: DeployPolicyMatcher = Field(default_factory=DeployPolicyMatcher)
    action: Literal["allow", "deny", "require_approval"] = "allow"
    priority: int = 0
    approval_config: DeployApprovalConfig | None = None


class DeployPolicyDecision(BaseModel):
    """Result of evaluating a DevOps policy."""

    model_config = ConfigDict(extra="forbid")

    allowed: bool
    action: Literal["allow", "deny", "require_approval"]
    reason: str
    approval_token: str | None = None
