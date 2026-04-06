"""Tests for agentic_devops.monitor — health checks and status evaluation."""

from __future__ import annotations

from agentic_devops.models import HealthCheck
from agentic_devops.monitor import MonitorEngine, _check_command


class TestMonitorEngine:
    def test_command_check_success(self) -> None:
        check = HealthCheck(
            name="echo_test",
            check_type="command",
            target="echo healthy",
            timeout_seconds=5,
            failure_threshold=3,
        )
        engine = MonitorEngine(checks=[check])
        statuses = engine.run_health_checks()
        assert len(statuses) == 1
        assert statuses[0].status == "healthy"
        assert statuses[0].consecutive_failures == 0

    def test_command_check_failure(self) -> None:
        check = HealthCheck(
            name="fail_test",
            check_type="command",
            target="false",
            timeout_seconds=5,
            failure_threshold=3,
        )
        engine = MonitorEngine(checks=[check])
        statuses = engine.run_health_checks()
        assert len(statuses) == 1
        # First failure → degraded (below threshold)
        assert statuses[0].status == "degraded"

    def test_failure_threshold_escalation(self) -> None:
        check = HealthCheck(
            name="threshold_test",
            check_type="command",
            target="false",
            timeout_seconds=5,
            failure_threshold=2,
        )
        engine = MonitorEngine(checks=[check])
        # First check: 1 failure → degraded
        engine.run_health_checks()
        # Second check: 2 failures → unhealthy (threshold reached)
        statuses = engine.run_health_checks()
        assert statuses[0].status == "unhealthy"
        assert statuses[0].consecutive_failures == 2

    def test_overall_healthy(self) -> None:
        engine = MonitorEngine(checks=[
            HealthCheck(name="a", check_type="command", target="true"),
            HealthCheck(name="b", check_type="command", target="true"),
        ])
        assert engine.evaluate_overall_health() == "healthy"

    def test_overall_degraded(self) -> None:
        engine = MonitorEngine(checks=[
            HealthCheck(name="a", check_type="command", target="true"),
            HealthCheck(name="b", check_type="command", target="false", failure_threshold=5),
        ])
        assert engine.evaluate_overall_health() == "degraded"

    def test_overall_unhealthy(self) -> None:
        engine = MonitorEngine(checks=[
            HealthCheck(name="a", check_type="command", target="false", failure_threshold=1),
        ])
        assert engine.evaluate_overall_health() == "unhealthy"

    def test_add_and_remove_check(self) -> None:
        engine = MonitorEngine()
        check = HealthCheck(check_id="c1", name="test", check_type="command", target="true")
        engine.add_check(check)
        assert len(engine.checks) == 1
        engine.remove_check("c1")
        assert len(engine.checks) == 0

    def test_monitoring_loop(self) -> None:
        check = HealthCheck(name="loop_test", check_type="command", target="true", interval_seconds=1)
        engine = MonitorEngine(checks=[check])
        results: list[str] = []
        engine.run_monitoring_loop(
            callback=lambda s: results.append(s.status),
            max_iterations=2,
        )
        assert len(results) == 2
        assert all(r == "healthy" for r in results)

    def test_empty_checks(self) -> None:
        engine = MonitorEngine()
        assert engine.evaluate_overall_health() == "unknown"

    def test_run_single_check(self) -> None:
        check = HealthCheck(check_id="c1", name="single", check_type="command", target="true")
        engine = MonitorEngine(checks=[check])
        result = engine.run_single_check("c1")
        assert result is not None
        assert result.status == "healthy"
        assert engine.run_single_check("nonexistent") is None


class TestCheckCommand:
    def test_success(self) -> None:
        status, details = _check_command("echo hello", 5)
        assert status == "healthy"
        assert details["returncode"] == 0

    def test_failure(self) -> None:
        status, details = _check_command("false", 5)
        assert status == "unhealthy"
        assert details["returncode"] != 0
