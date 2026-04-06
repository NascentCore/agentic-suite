"""Tests for agentic_runtime.executor — safe execution and saga."""

from __future__ import annotations

from agentic_runtime.executor import RuntimeExecutor
from agentic_runtime.models import (
    ActionRequest,
    PolicyMatcher,
    PolicyRule,
    SagaStep,
    ToolManifest,
)
from agentic_runtime.policy_engine import RuntimePolicyEngine
from agentic_runtime.tool_registry import ToolRegistry


def _setup() -> tuple[ToolRegistry, RuntimePolicyEngine, RuntimeExecutor]:
    reg = ToolRegistry(app_name="test")
    reg.register(ToolManifest(tool_id="t1", name="echo", risk_level="read_only"))
    reg.register(ToolManifest(tool_id="t2", name="fail_tool", risk_level="read_only"))
    reg.register(ToolManifest(tool_id="t3", name="dangerous", risk_level="high_impact"))

    policy = RuntimePolicyEngine()
    executor = RuntimeExecutor(registry=reg, policy_engine=policy)

    executor.register_handler("t1", lambda params: {"echo": params.get("msg", "")})
    executor.register_handler("t2", lambda _: (_ for _ in ()).throw(ValueError("boom")))

    return reg, policy, executor


class TestExecute:
    def test_success(self) -> None:
        _reg, _policy, executor = _setup()
        req = ActionRequest(tool_id="t1", parameters={"msg": "hello"})
        resp = executor.execute(req)
        assert resp.status == "success"
        assert resp.result == {"echo": "hello"}
        assert resp.execution_ms >= 0

    def test_tool_not_found(self) -> None:
        _reg, _policy, executor = _setup()
        req = ActionRequest(tool_id="nonexistent")
        resp = executor.execute(req)
        assert resp.status == "failed"
        assert "not found" in resp.error["message"].lower()

    def test_handler_error(self) -> None:
        _reg, _policy, executor = _setup()
        req = ActionRequest(tool_id="t2")
        resp = executor.execute(req)
        assert resp.status == "failed"
        assert "boom" in resp.error["message"]

    def test_no_handler(self) -> None:
        reg = ToolRegistry(app_name="test")
        reg.register(ToolManifest(tool_id="t_nohandler", name="ghost"))
        executor = RuntimeExecutor(registry=reg, policy_engine=RuntimePolicyEngine())
        req = ActionRequest(tool_id="t_nohandler")
        resp = executor.execute(req)
        assert resp.status == "failed"
        assert "no handler" in resp.error["message"].lower()

    def test_policy_blocks_high_impact(self) -> None:
        _reg, _policy, executor = _setup()
        req = ActionRequest(tool_id="t3")
        resp = executor.execute(req)
        assert resp.status in ("requires_approval", "failed")

    def test_policy_deny(self) -> None:
        _reg, policy, executor = _setup()
        policy.add_rule(PolicyRule(
            match=PolicyMatcher(tool_ids=["t1"]),
            action="deny",
            priority=100,
        ))
        req = ActionRequest(tool_id="t1")
        resp = executor.execute(req)
        assert resp.status == "failed"
        assert resp.error is not None

    def test_provenance_recorded(self) -> None:
        _reg, _policy, executor = _setup()
        req = ActionRequest(tool_id="t1", parameters={"msg": "hi"})
        resp = executor.execute(req)
        assert resp.provenance.tool_input == {"msg": "hi"}
        assert resp.provenance.tool_output == {"echo": "hi"}

    def test_execution_log(self) -> None:
        _reg, _policy, executor = _setup()
        executor.execute(ActionRequest(tool_id="t1", parameters={"msg": "a"}))
        executor.execute(ActionRequest(tool_id="t1", parameters={"msg": "b"}))
        assert len(executor.execution_log) == 2


class TestSaga:
    def test_all_succeed(self) -> None:
        _reg, _policy, executor = _setup()
        steps = [
            SagaStep(forward=ActionRequest(tool_id="t1", parameters={"msg": "step1"})),
            SagaStep(forward=ActionRequest(tool_id="t1", parameters={"msg": "step2"})),
        ]
        results = executor.execute_saga(steps)
        assert all(s.status == "succeeded" for s in results)

    def test_failure_triggers_compensation(self) -> None:
        _reg, _policy, executor = _setup()
        compensated = []

        def comp_handler(params: dict) -> dict:
            compensated.append(params)
            return {"compensated": True}

        executor.register_handler("comp1", comp_handler)
        _reg.register(ToolManifest(tool_id="comp1", name="comp"))

        steps = [
            SagaStep(
                forward=ActionRequest(tool_id="t1", parameters={"msg": "ok"}),
                compensator=ActionRequest(tool_id="comp1", parameters={"step": "1"}),
            ),
            SagaStep(
                forward=ActionRequest(tool_id="t2", parameters={}),  # will fail
            ),
        ]
        results = executor.execute_saga(steps)
        assert results[0].status == "compensated"
        assert results[1].status == "failed"
        assert len(compensated) == 1

    def test_no_compensator_skipped(self) -> None:
        _reg, _policy, executor = _setup()
        steps = [
            SagaStep(forward=ActionRequest(tool_id="t1", parameters={"msg": "ok"})),
            SagaStep(forward=ActionRequest(tool_id="t2", parameters={})),  # will fail
        ]
        results = executor.execute_saga(steps)
        # step 0 has no compensator so stays succeeded (not compensated)
        assert results[0].status == "succeeded"
        assert results[1].status == "failed"
