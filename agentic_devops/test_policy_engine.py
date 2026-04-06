"""Tests for agentic_devops.policy_engine — deployment gates."""

from __future__ import annotations

from agentic_devops.models import (
    DeployPolicyMatcher,
    DeployPolicyRule,
    PipelineStage,
    RemediationAction,
)
from agentic_devops.policy_engine import DevOpsPolicyEngine


class TestStageEvaluation:
    def test_default_allows_build(self) -> None:
        engine = DevOpsPolicyEngine()
        stage = PipelineStage(name="build", stage_type="build")
        decision = engine.evaluate_stage(stage)
        assert decision.allowed is True

    def test_default_blocks_production_deploy(self) -> None:
        engine = DevOpsPolicyEngine()
        stage = PipelineStage(name="deploy", stage_type="deploy")
        decision = engine.evaluate_stage(stage, environment="production")
        assert decision.allowed is False
        assert decision.action == "require_approval"

    def test_requires_approval_flag(self) -> None:
        engine = DevOpsPolicyEngine()
        stage = PipelineStage(name="test", stage_type="test", requires_approval=True)
        decision = engine.evaluate_stage(stage)
        assert decision.allowed is False
        assert decision.approval_token is not None

    def test_explicit_deny_rule(self) -> None:
        engine = DevOpsPolicyEngine()
        engine.add_rule(DeployPolicyRule(
            match=DeployPolicyMatcher(stage_types=["deploy"]),
            action="deny",
            priority=10,
        ))
        stage = PipelineStage(name="deploy", stage_type="deploy")
        decision = engine.evaluate_stage(stage)
        assert decision.allowed is False
        assert decision.action == "deny"

    def test_explicit_allow_rule(self) -> None:
        engine = DevOpsPolicyEngine()
        engine.add_rule(DeployPolicyRule(
            match=DeployPolicyMatcher(environments=["staging"]),
            action="allow",
            priority=10,
        ))
        stage = PipelineStage(name="deploy", stage_type="deploy")
        decision = engine.evaluate_stage(stage, environment="staging")
        assert decision.allowed is True

    def test_environment_matcher(self) -> None:
        engine = DevOpsPolicyEngine()
        engine.add_rule(DeployPolicyRule(
            match=DeployPolicyMatcher(environments=["production"]),
            action="require_approval",
            priority=10,
        ))
        stage = PipelineStage(name="deploy", stage_type="deploy")
        # staging not in matcher → no match → default
        staging_decision = engine.evaluate_stage(stage, environment="staging")
        assert staging_decision.allowed is True
        # production matches
        prod_decision = engine.evaluate_stage(stage, environment="production")
        assert prod_decision.allowed is False

    def test_priority_ordering(self) -> None:
        engine = DevOpsPolicyEngine()
        engine.add_rule(DeployPolicyRule(
            match=DeployPolicyMatcher(stage_types=["deploy"]),
            action="deny",
            priority=1,
        ))
        engine.add_rule(DeployPolicyRule(
            match=DeployPolicyMatcher(stage_types=["deploy"]),
            action="allow",
            priority=10,
        ))
        stage = PipelineStage(name="deploy", stage_type="deploy")
        decision = engine.evaluate_stage(stage)
        assert decision.allowed is True  # higher priority wins


class TestRemediationEvaluation:
    def test_low_risk_auto_approved(self) -> None:
        engine = DevOpsPolicyEngine()
        action = RemediationAction(
            description="Restart",
            action_type="restart",
            risk_level="low",
            requires_approval=False,
        )
        decision = engine.evaluate_remediation(action)
        assert decision.allowed is True

    def test_high_risk_requires_approval(self) -> None:
        engine = DevOpsPolicyEngine()
        action = RemediationAction(
            description="Rollback",
            action_type="rollback",
            risk_level="high",
            requires_approval=True,
        )
        decision = engine.evaluate_remediation(action)
        assert decision.allowed is False
        assert decision.approval_token is not None


class TestApprovalFlow:
    def test_approve(self) -> None:
        engine = DevOpsPolicyEngine()
        stage = PipelineStage(name="deploy", stage_type="deploy", requires_approval=True)
        decision = engine.evaluate_stage(stage)
        assert decision.approval_token is not None
        approved = engine.approve(decision.approval_token, "admin")
        assert approved.allowed is True

    def test_deny_approval(self) -> None:
        engine = DevOpsPolicyEngine()
        stage = PipelineStage(name="deploy", stage_type="deploy", requires_approval=True)
        decision = engine.evaluate_stage(stage)
        denied = engine.deny_approval(decision.approval_token)
        assert denied.allowed is False

    def test_unknown_token(self) -> None:
        engine = DevOpsPolicyEngine()
        result = engine.approve("fake-token", "admin")
        assert result.allowed is False

    def test_remove_rule(self) -> None:
        engine = DevOpsPolicyEngine()
        rule = engine.add_rule(DeployPolicyRule(action="deny"))
        assert engine.remove_rule(rule.rule_id) is True
        assert engine.remove_rule(rule.rule_id) is False
