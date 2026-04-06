"""Monitoring engine — health checks, status evaluation, and continuous monitoring.

Implements the *Observability Layer* (§4.6) from ``BRAIN_STORM.md``.

The engine:
1. Executes defined health check probes (HTTP, TCP, command, metric threshold).
2. Tracks consecutive failures per check.
3. Evaluates overall system health.
4. Provides a callback-based monitoring loop interface.
"""

from __future__ import annotations

import subprocess
import time
import urllib.request
import socket
from typing import Any, Callable

from .models import HealthCheck, HealthStatus, _utc_now


class MonitorEngine:
    """Health monitoring engine with pluggable check executors."""

    def __init__(self, checks: list[HealthCheck] | None = None) -> None:
        self._checks: list[HealthCheck] = list(checks or [])
        # Persistent state: consecutive failures per check_id
        self._failure_counts: dict[str, int] = {}

    # -- check management ---------------------------------------------------

    def add_check(self, check: HealthCheck) -> None:
        self._checks.append(check)

    def remove_check(self, check_id: str) -> bool:
        before = len(self._checks)
        self._checks = [c for c in self._checks if c.check_id != check_id]
        return len(self._checks) < before

    @property
    def checks(self) -> list[HealthCheck]:
        return list(self._checks)

    # -- single-pass execution ----------------------------------------------

    def run_health_checks(self) -> list[HealthStatus]:
        """Execute all registered health checks and return statuses."""
        return [self._execute_check(check) for check in self._checks]

    def run_single_check(self, check_id: str) -> HealthStatus | None:
        """Execute a single check by ID."""
        for check in self._checks:
            if check.check_id == check_id:
                return self._execute_check(check)
        return None

    # -- evaluation ---------------------------------------------------------

    def evaluate_overall_health(
        self, statuses: list[HealthStatus] | None = None,
    ) -> str:
        """Evaluate aggregate system health from individual check statuses.

        Returns ``"healthy"``, ``"degraded"``, or ``"unhealthy"``.
        """
        if statuses is None:
            statuses = self.run_health_checks()

        if not statuses:
            return "unknown"

        unhealthy_count = sum(1 for s in statuses if s.status == "unhealthy")
        degraded_count = sum(1 for s in statuses if s.status == "degraded")

        if unhealthy_count > 0:
            return "unhealthy"
        if degraded_count > 0:
            return "degraded"
        return "healthy"

    # -- continuous monitoring (synchronous, single-threaded) ----------------

    def run_monitoring_loop(
        self,
        callback: Callable[[HealthStatus], None],
        max_iterations: int | None = None,
    ) -> None:
        """Run health checks in a loop, invoking ``callback`` for each result.

        If ``max_iterations`` is None, runs indefinitely.
        The interval between iterations is the minimum ``interval_seconds`` across checks.
        """
        if not self._checks:
            return

        interval = min(c.interval_seconds for c in self._checks)
        iterations = 0

        while max_iterations is None or iterations < max_iterations:
            statuses = self.run_health_checks()
            for status in statuses:
                callback(status)
            iterations += 1
            if max_iterations is not None and iterations >= max_iterations:
                break
            time.sleep(interval)

    # -- internal -----------------------------------------------------------

    def _execute_check(self, check: HealthCheck) -> HealthStatus:
        """Execute a single health check probe."""
        check_id = check.check_id

        try:
            if check.check_type == "http":
                status, details = _check_http(check.target, check.timeout_seconds)
            elif check.check_type == "tcp":
                status, details = _check_tcp(check.target, check.timeout_seconds)
            elif check.check_type == "command":
                status, details = _check_command(check.target, check.timeout_seconds)
            elif check.check_type == "metric_threshold":
                status, details = "unknown", {"note": "metric_threshold not yet implemented"}
            else:
                status, details = "unknown", {"note": f"unsupported check type: {check.check_type}"}
        except Exception as exc:
            status = "unhealthy"
            details = {"error": str(exc)}

        if status == "healthy":
            self._failure_counts[check_id] = 0
        else:
            self._failure_counts[check_id] = self._failure_counts.get(check_id, 0) + 1

        consecutive = self._failure_counts.get(check_id, 0)

        # Apply failure threshold: only escalate to unhealthy after threshold
        final_status = status
        if consecutive > 0 and consecutive < check.failure_threshold:
            final_status = "degraded"
        elif consecutive >= check.failure_threshold:
            final_status = "unhealthy"

        return HealthStatus(
            check_id=check_id,
            name=check.name,
            status=final_status,
            last_checked=_utc_now(),
            consecutive_failures=consecutive,
            details=details,
        )


# ---------------------------------------------------------------------------
# Check executors
# ---------------------------------------------------------------------------

def _check_http(url: str, timeout: int) -> tuple[str, dict[str, Any]]:
    """HTTP health check — expects 2xx status."""
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            code = resp.getcode()
            if 200 <= code < 300:
                return "healthy", {"status_code": code}
            return "unhealthy", {"status_code": code}
    except Exception as exc:
        return "unhealthy", {"error": str(exc)}


def _check_tcp(target: str, timeout: int) -> tuple[str, dict[str, Any]]:
    """TCP connectivity check — expects successful connection."""
    try:
        host, port_str = target.rsplit(":", 1)
        port = int(port_str)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        if result == 0:
            return "healthy", {"host": host, "port": port}
        return "unhealthy", {"host": host, "port": port, "error_code": result}
    except Exception as exc:
        return "unhealthy", {"error": str(exc)}


def _check_command(command: str, timeout: int) -> tuple[str, dict[str, Any]]:
    """Command health check — expects exit code 0."""
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=timeout,
        )
        if result.returncode == 0:
            return "healthy", {"stdout": result.stdout.strip(), "returncode": 0}
        return "unhealthy", {"stdout": result.stdout.strip(), "stderr": result.stderr.strip(), "returncode": result.returncode}
    except subprocess.TimeoutExpired:
        return "unhealthy", {"error": "command timed out"}
    except Exception as exc:
        return "unhealthy", {"error": str(exc)}
