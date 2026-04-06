"""Tests for agentic_devops.pipeline_engine — saga-based orchestration."""

from __future__ import annotations

from agentic_devops.models import (
    DeployPolicyMatcher,
    DeployPolicyRule,
    PipelineDefinition,
    PipelineStage,
)
from agentic_devops.pipeline_engine import PipelineEngine, _topological_sort
from agentic_devops.policy_engine import DevOpsPolicyEngine


def _ok_runner(commands: list[str]) -> tuple[int, str, str]:
    """Command runner that always succeeds."""
    return 0, "ok", ""


def _fail_runner(commands: list[str]) -> tuple[int, str, str]:
    """Command runner that always fails."""
    return 1, "", "fail"


def _selective_runner(fail_commands: set[str]):
    """Command runner that fails on specific commands."""
    def runner(commands: list[str]) -> tuple[int, str, str]:
        for cmd in commands:
            if cmd in fail_commands:
                return 1, "", f"failed: {cmd}"
        return 0, "ok", ""
    return runner


class TestPipelineEngine:
    def test_all_stages_succeed(self) -> None:
        pipeline = PipelineDefinition(
            name="test-pipeline",
            stages=[
                PipelineStage(name="build", stage_type="build", commands=["make build"]),
                PipelineStage(name="test", stage_type="test", commands=["make test"]),
            ],
        )
        engine = PipelineEngine(command_runner=_ok_runner)
        run = engine.execute_pipeline(pipeline)
        assert run.status == "succeeded"
        assert len(run.stages) == 2
        assert all(s.status == "succeeded" for s in run.stages)

    def test_failure_stops_pipeline(self) -> None:
        pipeline = PipelineDefinition(
            name="test-pipeline",
            stages=[
                PipelineStage(name="build", stage_type="build", commands=["make build"]),
                PipelineStage(name="test", stage_type="test", commands=["make test"]),
                PipelineStage(name="deploy", stage_type="deploy", commands=["deploy"]),
            ],
        )
        engine = PipelineEngine(command_runner=_selective_runner({"make test"}))
        run = engine.execute_pipeline(pipeline)
        assert run.status == "failed"
        assert run.stages[0].status in ("succeeded", "compensated")
        assert run.stages[1].status == "failed"
        # deploy should not have been attempted
        assert len([s for s in run.stages if s.status == "running"]) == 0

    def test_saga_compensation(self) -> None:
        compensated_cmds: list[str] = []

        def tracking_runner(commands: list[str]) -> tuple[int, str, str]:
            for cmd in commands:
                compensated_cmds.append(cmd)
                if cmd == "deploy_fail":
                    return 1, "", "fail"
            return 0, "ok", ""

        pipeline = PipelineDefinition(
            name="saga-pipeline",
            stages=[
                PipelineStage(
                    name="build", stage_type="build",
                    commands=["build_ok"],
                    compensator_commands=["build_rollback"],
                ),
                PipelineStage(
                    name="deploy", stage_type="deploy",
                    commands=["deploy_fail"],
                ),
            ],
        )
        engine = PipelineEngine(command_runner=tracking_runner)
        run = engine.execute_pipeline(pipeline)
        assert run.status == "failed"
        # build_rollback should have been called as compensation
        assert "build_rollback" in compensated_cmds

    def test_policy_blocks_stage(self) -> None:
        policy = DevOpsPolicyEngine()
        policy.add_rule(DeployPolicyRule(
            match=DeployPolicyMatcher(stage_types=["deploy"]),
            action="deny",
            priority=10,
        ))
        pipeline = PipelineDefinition(
            name="test-pipeline",
            stages=[
                PipelineStage(name="build", stage_type="build", commands=["build"]),
                PipelineStage(name="deploy", stage_type="deploy", commands=["deploy"]),
            ],
        )
        engine = PipelineEngine(policy_engine=policy, command_runner=_ok_runner)
        run = engine.execute_pipeline(pipeline)
        assert run.status == "failed"
        # build succeeded, deploy was denied
        deploy_stage = [s for s in run.stages if s.stage_name == "deploy"][0]
        assert "Policy" in deploy_stage.error

    def test_provenance_recorded(self) -> None:
        pipeline = PipelineDefinition(
            name="test-pipeline",
            stages=[PipelineStage(name="build", stage_type="build", commands=["build"])],
        )
        engine = PipelineEngine(command_runner=_ok_runner)
        run = engine.execute_pipeline(pipeline)
        assert len(run.provenance.policy_decisions) > 0

    def test_run_tracking(self) -> None:
        pipeline = PipelineDefinition(
            name="test-pipeline",
            stages=[PipelineStage(name="build", stage_type="build", commands=["build"])],
        )
        engine = PipelineEngine(command_runner=_ok_runner)
        run = engine.execute_pipeline(pipeline)
        assert engine.get_run(run.run_id) is not None
        assert len(engine.runs) == 1


class TestTopologicalSort:
    def test_no_dependencies(self) -> None:
        stages = [
            PipelineStage(stage_id="a", name="a"),
            PipelineStage(stage_id="b", name="b"),
        ]
        sorted_stages = _topological_sort(stages)
        assert len(sorted_stages) == 2

    def test_linear_dependency(self) -> None:
        stages = [
            PipelineStage(stage_id="c", name="c", depends_on=["b"]),
            PipelineStage(stage_id="b", name="b", depends_on=["a"]),
            PipelineStage(stage_id="a", name="a"),
        ]
        sorted_stages = _topological_sort(stages)
        names = [s.name for s in sorted_stages]
        assert names.index("a") < names.index("b") < names.index("c")

    def test_diamond_dependency(self) -> None:
        stages = [
            PipelineStage(stage_id="d", name="d", depends_on=["b", "c"]),
            PipelineStage(stage_id="b", name="b", depends_on=["a"]),
            PipelineStage(stage_id="c", name="c", depends_on=["a"]),
            PipelineStage(stage_id="a", name="a"),
        ]
        sorted_stages = _topological_sort(stages)
        names = [s.name for s in sorted_stages]
        assert names.index("a") < names.index("b")
        assert names.index("a") < names.index("c")
        assert names.index("b") < names.index("d")
        assert names.index("c") < names.index("d")
