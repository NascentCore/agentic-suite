"""Pipeline orchestration engine — Planner-Executor + Saga pattern.

Implements the *Planner-Executor Separation* (§2.C) and *Saga with Compensating
Actions* (§2.F) patterns from ``BRAIN_STORM.md``.

The engine:
1. Topologically sorts stages by ``depends_on``.
2. Evaluates policy before each stage.
3. Executes stage commands (via pluggable command runner).
4. On failure, runs compensators in reverse dependency order.
5. Records provenance for the full run.
"""

from __future__ import annotations

import subprocess
import time
from typing import Callable

from .models import (
    PipelineDefinition,
    PipelineProvenance,
    PipelineRun,
    PipelineStage,
    StageExecution,
    _new_id,
    _utc_now,
)
from .policy_engine import DevOpsPolicyEngine


# Type alias for a command runner.
CommandRunner = Callable[[list[str]], tuple[int, str, str]]


def _default_command_runner(commands: list[str]) -> tuple[int, str, str]:
    """Run commands sequentially via subprocess. Returns (exit_code, stdout, stderr)."""
    all_stdout: list[str] = []
    all_stderr: list[str] = []
    for cmd in commands:
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=300,
            )
            all_stdout.append(result.stdout)
            all_stderr.append(result.stderr)
            if result.returncode != 0:
                return result.returncode, "\n".join(all_stdout), "\n".join(all_stderr)
        except subprocess.TimeoutExpired:
            return -1, "\n".join(all_stdout), "Command timed out"
        except Exception as exc:
            return -1, "\n".join(all_stdout), str(exc)
    return 0, "\n".join(all_stdout), "\n".join(all_stderr)


class PipelineEngine:
    """Pipeline orchestration engine with saga support."""

    def __init__(
        self,
        policy_engine: DevOpsPolicyEngine | None = None,
        command_runner: CommandRunner | None = None,
    ) -> None:
        self._policy = policy_engine or DevOpsPolicyEngine()
        self._runner = command_runner or _default_command_runner
        self._runs: list[PipelineRun] = []

    # -- execution ----------------------------------------------------------

    def execute_pipeline(
        self,
        definition: PipelineDefinition,
        environment: str = "",
        requester_did: str = "",
        provenance: PipelineProvenance | None = None,
    ) -> PipelineRun:
        """Execute a pipeline definition through the full saga-enabled flow."""

        run = PipelineRun(
            pipeline_id=definition.pipeline_id,
            trigger_event=definition.trigger.trigger_type,
            status="running",
            provenance=provenance or PipelineProvenance(),
        )

        # Build ordered execution list
        ordered_stages = _topological_sort(definition.stages)
        stage_execs: list[StageExecution] = []
        succeeded_stages: list[tuple[PipelineStage, StageExecution]] = []

        for stage in ordered_stages:
            stage_exec = StageExecution(
                stage_id=stage.stage_id,
                stage_name=stage.name,
                status="running",
                started_at=_utc_now(),
            )

            # Policy check
            decision = self._policy.evaluate_stage(stage, environment, requester_did)
            run.provenance.policy_decisions.append(
                f"{stage.name}: {decision.action} — {decision.reason}"
            )

            if not decision.allowed:
                stage_exec.status = "failed"
                stage_exec.error = f"Policy: {decision.reason}"
                stage_exec.finished_at = _utc_now()
                stage_execs.append(stage_exec)
                # Trigger saga compensation
                self._compensate(succeeded_stages)
                run.status = "failed"
                run.stages = stage_execs
                run.finished_at = _utc_now()
                self._runs.append(run)
                return run

            # Execute commands
            if stage.commands:
                exit_code, stdout, stderr = self._runner(stage.commands)
                stage_exec.output = stdout
                stage_exec.error = stderr

                if exit_code != 0:
                    stage_exec.status = "failed"
                    stage_exec.finished_at = _utc_now()
                    stage_execs.append(stage_exec)
                    # Trigger saga compensation
                    self._compensate(succeeded_stages)
                    run.status = "failed"
                    run.stages = stage_execs
                    run.finished_at = _utc_now()
                    self._runs.append(run)
                    return run

            stage_exec.status = "succeeded"
            stage_exec.finished_at = _utc_now()
            stage_execs.append(stage_exec)
            succeeded_stages.append((stage, stage_exec))

        run.status = "succeeded"
        run.stages = stage_execs
        run.finished_at = _utc_now()
        self._runs.append(run)
        return run

    # -- rollback -----------------------------------------------------------

    def rollback_pipeline(self, run: PipelineRun, definition: PipelineDefinition) -> PipelineRun:
        """Roll back a pipeline run using stage compensator commands."""

        run.status = "rolling_back"

        # Map stage_id to definition stage
        stage_map = {s.stage_id: s for s in definition.stages}

        succeeded = [
            (stage_map[se.stage_id], se)
            for se in run.stages
            if se.status == "succeeded" and se.stage_id in stage_map
        ]

        self._compensate(succeeded)

        run.status = "failed"
        run.finished_at = _utc_now()
        return run

    # -- observability ------------------------------------------------------

    @property
    def runs(self) -> list[PipelineRun]:
        return list(self._runs)

    def get_run(self, run_id: str) -> PipelineRun | None:
        for run in self._runs:
            if run.run_id == run_id:
                return run
        return None

    # -- internal -----------------------------------------------------------

    def _compensate(self, succeeded: list[tuple[PipelineStage, StageExecution]]) -> None:
        """Run compensator commands for succeeded stages in reverse order."""
        for stage, stage_exec in reversed(succeeded):
            if stage.compensator_commands:
                exit_code, stdout, stderr = self._runner(stage.compensator_commands)
                stage_exec.status = "compensated"
                stage_exec.output += f"\n[COMPENSATE] {stdout}"
                stage_exec.error += f"\n[COMPENSATE] {stderr}" if stderr else ""


def _topological_sort(stages: list[PipelineStage]) -> list[PipelineStage]:
    """Sort stages by dependency order (``depends_on``)."""

    stage_map = {s.stage_id: s for s in stages}
    name_to_id = {s.name: s.stage_id for s in stages}

    visited: set[str] = set()
    result: list[PipelineStage] = []

    def visit(stage_id: str) -> None:
        if stage_id in visited:
            return
        visited.add(stage_id)
        stage = stage_map.get(stage_id)
        if stage is None:
            return
        for dep in stage.depends_on:
            dep_id = name_to_id.get(dep, dep)
            visit(dep_id)
        result.append(stage)

    for stage in stages:
        visit(stage.stage_id)

    return result
