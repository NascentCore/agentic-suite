"""Tests for agentic_runtime.policy_engine — RBAC, approval, rate limiting."""

from __future__ import annotations

from agentic_runtime.models import (
    ActionRequest,
    ApprovalConfig,
    PolicyMatcher,
    PolicyRule,
    RateLimitConfig,
    ToolManifest,
)
from agentic_runtime.policy_engine import RuntimePolicyEngine
from agentic_runtime.tool_registry import ToolRegistry


def _make_registry() -> ToolRegistry:
    reg = ToolRegistry(app_name="test")
    reg.register(ToolManifest(tool_id="t_read", name="list_users", risk_level="read_only"))
    reg.register(ToolManifest(tool_id="t_write", name="create_user", risk_level="bounded_write"))
    reg.register(ToolManifest(tool_id="t_danger", name="delete_all", risk_level="high_impact"))
    return reg


class TestDefaultPolicy:
    def test_read_only_allowed_by_default(self) -> None:
        engine = RuntimePolicyEngine()
        reg = _make_registry()
        req = ActionRequest(tool_id="t_read")
        decision = engine.evaluate(req, reg)
        assert decision.allowed is True

    def test_high_impact_requires_approval_by_default(self) -> None:
        engine = RuntimePolicyEngine()
        reg = _make_registry()
        req = ActionRequest(tool_id="t_danger")
        decision = engine.evaluate(req, reg)
        assert decision.allowed is False
        assert decision.action == "require_approval"

    def test_unknown_tool_allowed(self) -> None:
        engine = RuntimePolicyEngine()
        req = ActionRequest(tool_id="unknown")
        decision = engine.evaluate(req)
        assert decision.allowed is True  # no tool info → default allow


class TestExplicitRules:
    def test_deny_rule(self) -> None:
        engine = RuntimePolicyEngine()
        engine.add_rule(PolicyRule(
            match=PolicyMatcher(tool_ids=["t_read"]),
            action="deny",
            priority=10,
        ))
        req = ActionRequest(tool_id="t_read")
        decision = engine.evaluate(req)
        assert decision.allowed is False
        assert decision.action == "deny"

    def test_allow_rule(self) -> None:
        engine = RuntimePolicyEngine()
        reg = _make_registry()
        engine.add_rule(PolicyRule(
            match=PolicyMatcher(tool_ids=["t_danger"]),
            action="allow",
            priority=10,
        ))
        req = ActionRequest(tool_id="t_danger")
        decision = engine.evaluate(req, reg)
        assert decision.allowed is True

    def test_require_approval_rule(self) -> None:
        engine = RuntimePolicyEngine()
        engine.add_rule(PolicyRule(
            match=PolicyMatcher(tool_ids=["t_write"]),
            action="require_approval",
            priority=10,
            approval_config=ApprovalConfig(timeout_seconds=60),
        ))
        req = ActionRequest(tool_id="t_write")
        decision = engine.evaluate(req)
        assert decision.allowed is False
        assert decision.action == "require_approval"
        assert decision.approval_token is not None

    def test_priority_ordering(self) -> None:
        engine = RuntimePolicyEngine()
        engine.add_rule(PolicyRule(
            match=PolicyMatcher(tool_ids=["t_read"]),
            action="deny",
            priority=1,
        ))
        engine.add_rule(PolicyRule(
            match=PolicyMatcher(tool_ids=["t_read"]),
            action="allow",
            priority=10,  # higher priority wins
        ))
        req = ActionRequest(tool_id="t_read")
        decision = engine.evaluate(req)
        assert decision.allowed is True

    def test_requester_did_filter(self) -> None:
        engine = RuntimePolicyEngine()
        engine.add_rule(PolicyRule(
            match=PolicyMatcher(requester_dids=["did:plc:admin"]),
            action="allow",
            priority=20,
        ))
        engine.add_rule(PolicyRule(
            match=PolicyMatcher(),
            action="deny",
            priority=10,
        ))
        admin_req = ActionRequest(tool_id="t_read", requester_did="did:plc:admin")
        user_req = ActionRequest(tool_id="t_read", requester_did="did:plc:user")
        assert engine.evaluate(admin_req).allowed is True
        assert engine.evaluate(user_req).allowed is False


class TestRateLimiting:
    def test_rate_limit_allows_within_budget(self) -> None:
        engine = RuntimePolicyEngine()
        engine.add_rule(PolicyRule(
            match=PolicyMatcher(tool_ids=["t_read"]),
            action="rate_limit",
            priority=10,
            rate_limit=RateLimitConfig(max_calls=3, window_seconds=60),
        ))
        req = ActionRequest(tool_id="t_read", requester_did="user1")
        for _ in range(3):
            decision = engine.evaluate(req)
            assert decision.allowed is True

    def test_rate_limit_denies_over_budget(self) -> None:
        engine = RuntimePolicyEngine()
        engine.add_rule(PolicyRule(
            match=PolicyMatcher(tool_ids=["t_read"]),
            action="rate_limit",
            priority=10,
            rate_limit=RateLimitConfig(max_calls=2, window_seconds=60),
        ))
        req = ActionRequest(tool_id="t_read", requester_did="user1")
        engine.evaluate(req)
        engine.evaluate(req)
        decision = engine.evaluate(req)
        assert decision.allowed is False
        assert decision.action == "rate_limit"


class TestApprovalFlow:
    def test_approve_pending(self) -> None:
        engine = RuntimePolicyEngine()
        engine.add_rule(PolicyRule(
            match=PolicyMatcher(tool_ids=["t_write"]),
            action="require_approval",
            priority=10,
            approval_config=ApprovalConfig(timeout_seconds=300),
        ))
        req = ActionRequest(tool_id="t_write")
        decision = engine.evaluate(req)
        assert decision.approval_token is not None

        approved = engine.approve(decision.approval_token, "did:plc:admin")
        assert approved.allowed is True

    def test_deny_pending(self) -> None:
        engine = RuntimePolicyEngine()
        engine.add_rule(PolicyRule(
            match=PolicyMatcher(tool_ids=["t_write"]),
            action="require_approval",
            priority=10,
        ))
        req = ActionRequest(tool_id="t_write")
        decision = engine.evaluate(req)
        denied = engine.deny_approval(decision.approval_token)
        assert denied.allowed is False

    def test_unknown_token(self) -> None:
        engine = RuntimePolicyEngine()
        result = engine.approve("nonexistent-token", "admin")
        assert result.allowed is False

    def test_remove_rule(self) -> None:
        engine = RuntimePolicyEngine()
        rule = engine.add_rule(PolicyRule(action="deny", priority=10))
        assert engine.remove_rule(rule.rule_id) is True
        assert engine.remove_rule(rule.rule_id) is False
