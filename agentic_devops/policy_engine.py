"""DevOps Policy Engine — deployment approval gates and environment protection.

Applies the *Policy Engine* (§4.3) and *Human Approval Gate* (§2.G) patterns
from ``BRAIN_STORM.md`` to deployment operations.

Key semantics:
- Production deployments always require approval by default.
- Pipeline stages with ``requires_approval=True`` must be explicitly approved.
- Incident remediation actions are gated by severity and risk level.
"""

from __future__ import annotations

import time

from .models import (
    DeployApprovalConfig,
    DeployPolicyDecision,
    DeployPolicyMatcher,
    DeployPolicyRule,
    PipelineStage,
    RemediationAction,
    _new_id,
)


class DevOpsPolicyEngine:
    """Stateful policy engine for DevOps operations."""

    def __init__(self) -> None:
        self._rules: list[DeployPolicyRule] = []
        self._pending_approvals: dict[str, tuple[str, DeployPolicyRule, float]] = {}

    # -- rule management ----------------------------------------------------

    def add_rule(self, rule: DeployPolicyRule) -> DeployPolicyRule:
        self._rules.append(rule)
        self._rules.sort(key=lambda r: r.priority, reverse=True)
        return rule

    def remove_rule(self, rule_id: str) -> bool:
        before = len(self._rules)
        self._rules = [r for r in self._rules if r.rule_id != rule_id]
        return len(self._rules) < before

    @property
    def rules(self) -> list[DeployPolicyRule]:
        return list(self._rules)

    # -- stage evaluation ---------------------------------------------------

    def evaluate_stage(
        self,
        stage: PipelineStage,
        environment: str = "",
        requester_did: str = "",
    ) -> DeployPolicyDecision:
        """Evaluate policy for a pipeline stage execution."""

        for rule in self._rules:
            if not _stage_matches(rule.match, stage, environment, requester_did):
                continue

            if rule.action == "deny":
                return DeployPolicyDecision(
                    allowed=False, action="deny",
                    reason=f"Denied by rule {rule.rule_id}.",
                )

            if rule.action == "require_approval":
                token = _new_id()
                self._pending_approvals[token] = (stage.stage_id, rule, time.time())
                return DeployPolicyDecision(
                    allowed=False, action="require_approval",
                    reason=f"Approval required by rule {rule.rule_id}.",
                    approval_token=token,
                )

            return DeployPolicyDecision(
                allowed=True, action="allow",
                reason=f"Allowed by rule {rule.rule_id}.",
            )

        # Default: deploy stages to production require approval
        if stage.requires_approval:
            token = _new_id()
            self._pending_approvals[token] = (stage.stage_id, DeployPolicyRule(), time.time())
            return DeployPolicyDecision(
                allowed=False, action="require_approval",
                reason="Default policy: stage requires explicit approval.",
                approval_token=token,
            )

        if stage.stage_type == "deploy" and environment in ("production", "prod"):
            token = _new_id()
            self._pending_approvals[token] = (stage.stage_id, DeployPolicyRule(), time.time())
            return DeployPolicyDecision(
                allowed=False, action="require_approval",
                reason="Default policy: production deployments require approval.",
                approval_token=token,
            )

        return DeployPolicyDecision(
            allowed=True, action="allow",
            reason="Default policy: allowed.",
        )

    # -- remediation evaluation ---------------------------------------------

    def evaluate_remediation(
        self,
        action: RemediationAction,
        requester_did: str = "",
    ) -> DeployPolicyDecision:
        """Evaluate policy for an incident remediation action."""

        if action.risk_level == "high" or action.requires_approval:
            token = _new_id()
            self._pending_approvals[token] = (action.action_id, DeployPolicyRule(), time.time())
            return DeployPolicyDecision(
                allowed=False, action="require_approval",
                reason=f"Remediation action '{action.description}' requires approval (risk={action.risk_level}).",
                approval_token=token,
            )

        return DeployPolicyDecision(
            allowed=True, action="allow",
            reason=f"Remediation action '{action.description}' auto-approved (risk={action.risk_level}).",
        )

    # -- approval -----------------------------------------------------------

    def approve(self, approval_token: str, approver_did: str) -> DeployPolicyDecision:
        pending = self._pending_approvals.pop(approval_token, None)
        if pending is None:
            return DeployPolicyDecision(
                allowed=False, action="deny",
                reason="Unknown or expired approval token.",
            )
        _entity_id, rule, created_at = pending
        if rule.approval_config and rule.approval_config.timeout_seconds:
            if time.time() - created_at > rule.approval_config.timeout_seconds:
                return DeployPolicyDecision(
                    allowed=False, action="deny",
                    reason="Approval timed out.",
                )
        return DeployPolicyDecision(
            allowed=True, action="allow",
            reason=f"Approved by {approver_did}.",
        )

    def deny_approval(self, approval_token: str) -> DeployPolicyDecision:
        self._pending_approvals.pop(approval_token, None)
        return DeployPolicyDecision(
            allowed=False, action="deny",
            reason="Approval explicitly denied.",
        )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _stage_matches(
    matcher: DeployPolicyMatcher,
    stage: PipelineStage,
    environment: str,
    requester_did: str,
) -> bool:
    if matcher.environments and environment not in matcher.environments:
        return False
    if matcher.stage_types and stage.stage_type not in matcher.stage_types:
        return False
    if matcher.requester_dids and requester_did not in matcher.requester_dids:
        return False
    return True
