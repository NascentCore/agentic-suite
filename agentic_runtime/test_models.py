"""Tests for agentic_runtime.models — all core data models."""

from __future__ import annotations

from datetime import datetime, timezone

from agentic_runtime.models import (
    ActionRequest,
    ActionResponse,
    ApprovalConfig,
    ExecutionProvenance,
    PolicyDecision,
    PolicyMatcher,
    PolicyRule,
    RateLimitConfig,
    RuntimeCapability,
    RuntimeDetectorConfig,
    RuntimeProfile,
    RuntimeSession,
    SagaStep,
    ToolManifest,
    ToolRegistryState,
)


class TestRuntimeCapability:
    def test_defaults(self) -> None:
        cap = RuntimeCapability(name="get_users")
        assert cap.name == "get_users"
        assert cap.category == "api"
        assert cap.risk_level == "read_only"
        assert cap.requires_approval is False
        assert cap.idempotent is True
        assert cap.capability_id  # auto-generated UUID

    def test_full_construction(self) -> None:
        cap = RuntimeCapability(
            name="delete_user",
            description="Delete a user account",
            category="api",
            input_schema={"type": "object", "properties": {"user_id": {"type": "string"}}},
            output_schema={"type": "object"},
            risk_level="high_impact",
            requires_approval=True,
            idempotent=False,
            estimated_duration_ms=500,
            tags=["admin", "destructive"],
        )
        assert cap.risk_level == "high_impact"
        assert cap.requires_approval is True
        assert "admin" in cap.tags


class TestRuntimeProfile:
    def test_empty_profile(self) -> None:
        profile = RuntimeProfile(app_name="test-app")
        assert profile.app_name == "test-app"
        assert profile.capabilities == []
        assert profile.app_type == "web_service"

    def test_template_context(self) -> None:
        profile = RuntimeProfile(
            app_name="my-api",
            app_type="web_service",
            base_url="http://localhost:8000",
            capabilities=[
                RuntimeCapability(name="list_users", description="List all users"),
            ],
        )
        ctx = profile.to_template_context()
        assert ctx["APP_NAME"] == "my-api"
        assert ctx["CAPABILITY_COUNT"] == "1"
        assert "list_users" in ctx["CAPABILITY_LIST"]

    def test_serialization_roundtrip(self) -> None:
        profile = RuntimeProfile(
            app_name="roundtrip-app",
            capabilities=[RuntimeCapability(name="ping")],
        )
        json_str = profile.model_dump_json()
        restored = RuntimeProfile.model_validate_json(json_str)
        assert restored.app_name == "roundtrip-app"
        assert len(restored.capabilities) == 1


class TestToolManifest:
    def test_defaults(self) -> None:
        manifest = ToolManifest(name="get_status")
        assert manifest.version == "0.1.0"
        assert manifest.risk_level == "read_only"
        assert manifest.idempotent is True


class TestActionRequestResponse:
    def test_request_creation(self) -> None:
        req = ActionRequest(tool_id="tool-123", parameters={"q": "hello"})
        assert req.tool_id == "tool-123"
        assert req.parameters == {"q": "hello"}
        assert req.request_id  # auto-generated

    def test_response_success(self) -> None:
        resp = ActionResponse(
            request_id="req-1",
            status="success",
            result={"data": [1, 2, 3]},
            execution_ms=42,
        )
        assert resp.status == "success"
        assert resp.execution_ms == 42

    def test_response_requires_approval(self) -> None:
        resp = ActionResponse(
            request_id="req-2",
            status="requires_approval",
            approval_token="token-abc",
        )
        assert resp.approval_token == "token-abc"


class TestPolicyModels:
    def test_policy_rule_defaults(self) -> None:
        rule = PolicyRule()
        assert rule.action == "allow"
        assert rule.priority == 0

    def test_rate_limit_config(self) -> None:
        rl = RateLimitConfig(max_calls=10, window_seconds=30)
        assert rl.max_calls == 10

    def test_approval_config(self) -> None:
        ac = ApprovalConfig(approver_dids=["did:plc:admin"], timeout_seconds=60)
        assert ac.auto_deny_on_timeout is True


class TestRuntimeSession:
    def test_session_creation(self) -> None:
        session = RuntimeSession(user_did="did:plc:alice", app_name="test-app")
        assert session.user_did == "did:plc:alice"
        assert session.history == []
        assert session.checkpoint is None


class TestSagaStep:
    def test_saga_step(self) -> None:
        forward = ActionRequest(tool_id="t1")
        comp = ActionRequest(tool_id="t1_rollback")
        step = SagaStep(forward=forward, compensator=comp)
        assert step.status == "pending"
        assert step.compensator is not None
