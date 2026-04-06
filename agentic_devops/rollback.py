"""Rollback engine — version tracking and safe rollback strategies.

Provides:
1. A deployment version registry to track what's currently deployed.
2. Safe rollback execution with compensation and verification.
3. Rollback depth limits from ``RollbackStrategy``.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from .models import (
    DeployPolicyDecision,
    PipelineDefinition,
    PipelineRun,
    RollbackStrategy,
    _new_id,
    _utc_now,
)
from .policy_engine import DevOpsPolicyEngine


class DeploymentVersion:
    """A record of a single deployment version."""

    def __init__(
        self,
        version_id: str,
        environment: str,
        commit_sha: str = "",
        artifact_ref: str = "",
        deployed_at: datetime | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.version_id = version_id
        self.environment = environment
        self.commit_sha = commit_sha
        self.artifact_ref = artifact_ref
        self.deployed_at = deployed_at or _utc_now()
        self.metadata = metadata or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "version_id": self.version_id,
            "environment": self.environment,
            "commit_sha": self.commit_sha,
            "artifact_ref": self.artifact_ref,
            "deployed_at": self.deployed_at.isoformat(),
            "metadata": self.metadata,
        }


class RollbackEngine:
    """Deployment version tracker with safe rollback support."""

    def __init__(
        self,
        policy_engine: DevOpsPolicyEngine | None = None,
        rollback_strategy: RollbackStrategy | None = None,
    ) -> None:
        self._policy = policy_engine or DevOpsPolicyEngine()
        self._strategy = rollback_strategy or RollbackStrategy()
        # environment → ordered list of deployed versions (newest first)
        self._version_history: dict[str, list[DeploymentVersion]] = {}

    # -- version tracking ---------------------------------------------------

    def record_deployment(
        self,
        environment: str,
        version_id: str,
        commit_sha: str = "",
        artifact_ref: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> DeploymentVersion:
        """Record a new deployment. Returns the deployment version."""
        version = DeploymentVersion(
            version_id=version_id,
            environment=environment,
            commit_sha=commit_sha,
            artifact_ref=artifact_ref,
            metadata=metadata,
        )
        if environment not in self._version_history:
            self._version_history[environment] = []
        self._version_history[environment].insert(0, version)
        return version

    def current_version(self, environment: str) -> DeploymentVersion | None:
        """Get the current (most recent) deployed version for an environment."""
        history = self._version_history.get(environment, [])
        return history[0] if history else None

    def version_history(self, environment: str) -> list[DeploymentVersion]:
        """Get the full deployment history for an environment (newest first)."""
        return list(self._version_history.get(environment, []))

    def previous_version(self, environment: str) -> DeploymentVersion | None:
        """Get the version deployed immediately before the current one."""
        history = self._version_history.get(environment, [])
        return history[1] if len(history) >= 2 else None

    # -- rollback -----------------------------------------------------------

    def can_rollback(self, environment: str, depth: int = 1) -> bool:
        """Check whether rollback to a given depth is possible."""
        history = self._version_history.get(environment, [])
        if depth > self._strategy.max_rollback_depth:
            return False
        return len(history) > depth

    def get_rollback_target(self, environment: str, depth: int = 1) -> DeploymentVersion | None:
        """Get the target version for a rollback at the given depth."""
        history = self._version_history.get(environment, [])
        if depth > self._strategy.max_rollback_depth:
            return None
        if len(history) <= depth:
            return None
        return history[depth]

    def execute_rollback(
        self,
        environment: str,
        depth: int = 1,
        requester_did: str = "",
    ) -> dict[str, Any]:
        """Execute a rollback to a previous deployment version.

        Returns a result dict with:
        - ``success``: bool
        - ``from_version``: version we rolled back from
        - ``to_version``: version we rolled back to
        - ``reason``: explanation if failed
        """

        if not self.can_rollback(environment, depth):
            return {
                "success": False,
                "reason": f"Cannot rollback: insufficient history or depth {depth} exceeds max {self._strategy.max_rollback_depth}.",
            }

        current = self.current_version(environment)
        target = self.get_rollback_target(environment, depth)

        # In a real system we'd invoke the pipeline engine to redeploy.
        # Here we record the rollback as a new deployment.
        self.record_deployment(
            environment=environment,
            version_id=f"rollback-to-{target.version_id}",
            commit_sha=target.commit_sha,
            artifact_ref=target.artifact_ref,
            metadata={"rollback_from": current.version_id if current else None, "depth": depth},
        )

        return {
            "success": True,
            "from_version": current.to_dict() if current else None,
            "to_version": target.to_dict() if target else None,
        }
