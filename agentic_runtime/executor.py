"""Safe Execution Engine — policy-gated tool execution with saga support.

Implements the *Execution Runtime* (§4.4) and *Saga with Compensating Actions*
(§2.F) patterns from ``BRAIN_STORM.md``.

Flow per request:
    1. Resolve tool manifest from registry.
    2. Evaluate policy.
    3. If ``require_approval`` → return early with approval token.
    4. Invoke the tool handler.
    5. Record provenance.
    6. Return ``ActionResponse``.

For multi-step operations, ``execute_saga`` runs steps in order and executes
compensators in reverse on failure.
"""

from __future__ import annotations

import time
import traceback
from typing import Any, Callable

from .models import (
    ActionRequest,
    ActionResponse,
    ExecutionProvenance,
    SagaStep,
    _new_id,
    _utc_now,
)
from .policy_engine import RuntimePolicyEngine
from .tool_registry import ToolRegistry


# Type alias for a tool handler function.
ToolHandler = Callable[[dict[str, Any]], dict[str, Any]]


class RuntimeExecutor:
    """Policy-gated, provenance-recording execution engine."""

    def __init__(
        self,
        registry: ToolRegistry,
        policy_engine: RuntimePolicyEngine,
    ) -> None:
        self._registry = registry
        self._policy = policy_engine
        # tool_id → handler callable
        self._handlers: dict[str, ToolHandler] = {}
        # execution log (append-only, for audit / observability)
        self._log: list[ActionResponse] = []

    # -- handler registration -----------------------------------------------

    def register_handler(self, tool_id: str, handler: ToolHandler) -> None:
        """Bind a concrete handler function to a registered tool."""
        self._handlers[tool_id] = handler

    # -- single-step execution ----------------------------------------------

    def execute(self, request: ActionRequest) -> ActionResponse:
        """Execute a single action request through the full pipeline."""

        start_ns = time.monotonic_ns()

        # 1. resolve tool
        tool = self._registry.get(request.tool_id)
        if tool is None:
            return self._fail(request, start_ns, f"Tool not found: {request.tool_id}")

        # 2. evaluate policy
        decision = self._policy.evaluate(request, self._registry)
        if not decision.allowed:
            return ActionResponse(
                request_id=request.request_id,
                status="requires_approval" if decision.action == "require_approval" else "failed",
                error={"policy": decision.reason},
                execution_ms=self._elapsed_ms(start_ns),
                provenance=ExecutionProvenance(
                    tool_input=request.parameters,
                    tool_output={},
                    policy_decisions=[decision.reason],
                ),
                approval_token=decision.approval_token,
            )

        # 3. invoke handler
        handler = self._handlers.get(request.tool_id)
        if handler is None:
            return self._fail(request, start_ns, f"No handler for tool: {request.tool_id}")

        try:
            result = handler(request.parameters)
        except Exception as exc:
            return self._fail(request, start_ns, f"Handler error: {exc}")

        # 4. build provenance & response
        response = ActionResponse(
            request_id=request.request_id,
            status="success",
            result=result,
            execution_ms=self._elapsed_ms(start_ns),
            provenance=ExecutionProvenance(
                tool_input=request.parameters,
                tool_output=result,
                policy_decisions=[decision.reason],
            ),
        )
        self._log.append(response)
        return response

    # -- saga execution -----------------------------------------------------

    def execute_saga(self, steps: list[SagaStep]) -> list[SagaStep]:
        """Execute an ordered list of saga steps with compensation on failure.

        On any step failure the engine runs compensators for all previously
        succeeded steps **in reverse order** (Saga pattern from BRAIN_STORM §2.F).

        Returns the steps with updated status and response fields.
        """

        succeeded: list[SagaStep] = []

        for step in steps:
            resp = self.execute(step.forward)
            step.response = resp

            if resp.status == "success":
                step.status = "succeeded"
                succeeded.append(step)
            else:
                step.status = "failed"
                # compensate in reverse
                for prev in reversed(succeeded):
                    if prev.compensator is not None:
                        comp_resp = self.execute(prev.compensator)
                        prev.status = "compensated"
                        prev.response = comp_resp
                break  # stop executing further steps

        return steps

    # -- observability ------------------------------------------------------

    @property
    def execution_log(self) -> list[ActionResponse]:
        return list(self._log)

    # -- internal helpers ---------------------------------------------------

    @staticmethod
    def _elapsed_ms(start_ns: int) -> int:
        return int((time.monotonic_ns() - start_ns) / 1_000_000)

    def _fail(self, request: ActionRequest, start_ns: int, reason: str) -> ActionResponse:
        resp = ActionResponse(
            request_id=request.request_id,
            status="failed",
            error={"message": reason},
            execution_ms=self._elapsed_ms(start_ns),
            provenance=ExecutionProvenance(
                tool_input=request.parameters,
                tool_output={},
                policy_decisions=[],
            ),
        )
        self._log.append(resp)
        return resp
