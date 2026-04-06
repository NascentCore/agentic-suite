"""Runtime Policy Engine — RBAC, approval gates, rate limiting.

Implements the *Policy Engine* (§4.3) and *Human Approval Gate* (§2.G)
patterns from ``BRAIN_STORM.md``.

Decision semantics mirror AMCP's ``MemoryCustodian.evaluate_access``:
a deterministic, auditable function that returns a ``PolicyDecision``.
"""

from __future__ import annotations

import time
from collections import defaultdict

from .models import (
    ActionRequest,
    ApprovalConfig,
    PolicyDecision,
    PolicyMatcher,
    PolicyRule,
    ToolManifest,
    _new_id,
    _utc_now,
)
from .tool_registry import ToolRegistry


class RuntimePolicyEngine:
    """Stateful policy engine that evaluates ``ActionRequest`` against rules."""

    def __init__(self) -> None:
        self._rules: list[PolicyRule] = []
        # rate-limit tracking: key → list[timestamp_seconds]
        self._rate_counters: dict[str, list[float]] = defaultdict(list)
        # pending approval tokens: token → (request, rule, created_at_seconds)
        self._pending_approvals: dict[str, tuple[ActionRequest, PolicyRule, float]] = {}

    # -- rule management ----------------------------------------------------

    def add_rule(self, rule: PolicyRule) -> PolicyRule:
        """Add a policy rule (higher priority wins)."""
        self._rules.append(rule)
        self._rules.sort(key=lambda r: r.priority, reverse=True)
        return rule

    def remove_rule(self, rule_id: str) -> bool:
        before = len(self._rules)
        self._rules = [r for r in self._rules if r.rule_id != rule_id]
        return len(self._rules) < before

    @property
    def rules(self) -> list[PolicyRule]:
        return list(self._rules)

    # -- evaluation ---------------------------------------------------------

    def evaluate(
        self,
        request: ActionRequest,
        registry: ToolRegistry | None = None,
    ) -> PolicyDecision:
        """Evaluate policy for an ``ActionRequest``.

        Resolution order (first matching rule wins):
        1. Explicit deny
        2. Require approval
        3. Rate limit check
        4. Allow

        If no rule matches, default is **allow** for ``read_only`` tools
        and **require_approval** for ``high_impact`` tools.
        """

        tool: ToolManifest | None = registry.get(request.tool_id) if registry else None

        for rule in self._rules:
            if not _matches(rule.match, request, tool):
                continue

            if rule.action == "deny":
                return PolicyDecision(
                    allowed=False,
                    action="deny",
                    reason=f"Denied by rule {rule.rule_id}.",
                )

            if rule.action == "require_approval":
                token = _new_id()
                self._pending_approvals[token] = (request, rule, time.time())
                return PolicyDecision(
                    allowed=False,
                    action="require_approval",
                    reason=f"Approval required by rule {rule.rule_id}.",
                    approval_token=token,
                )

            if rule.action == "rate_limit" and rule.rate_limit:
                rl = rule.rate_limit
                key = f"{request.requester_did}:{request.tool_id}"
                now = time.time()
                window_start = now - rl.window_seconds
                self._rate_counters[key] = [
                    ts for ts in self._rate_counters[key] if ts > window_start
                ]
                if len(self._rate_counters[key]) >= rl.max_calls:
                    return PolicyDecision(
                        allowed=False,
                        action="rate_limit",
                        reason=f"Rate limit exceeded: {rl.max_calls}/{rl.window_seconds}s.",
                    )
                self._rate_counters[key].append(now)
                return PolicyDecision(
                    allowed=True,
                    action="allow",
                    reason=f"Allowed (within rate limit {rl.max_calls}/{rl.window_seconds}s).",
                )

            # action == "allow"
            return PolicyDecision(
                allowed=True,
                action="allow",
                reason=f"Allowed by rule {rule.rule_id}.",
            )

        # -- default policy (no matching rule) --
        return _default_decision(request, tool)

    # -- approval -----------------------------------------------------------

    def approve(self, approval_token: str, approver_did: str) -> PolicyDecision:
        """Approve a pending action that required human approval."""

        pending = self._pending_approvals.pop(approval_token, None)
        if pending is None:
            return PolicyDecision(
                allowed=False,
                action="deny",
                reason="Unknown or expired approval token.",
            )

        _request, rule, created_at = pending
        # Check timeout
        if rule.approval_config and rule.approval_config.timeout_seconds:
            elapsed = time.time() - created_at
            if elapsed > rule.approval_config.timeout_seconds:
                return PolicyDecision(
                    allowed=False,
                    action="deny",
                    reason="Approval timed out.",
                )

        return PolicyDecision(
            allowed=True,
            action="allow",
            reason=f"Approved by {approver_did}.",
        )

    def deny_approval(self, approval_token: str) -> PolicyDecision:
        """Explicitly deny a pending approval."""
        self._pending_approvals.pop(approval_token, None)
        return PolicyDecision(
            allowed=False,
            action="deny",
            reason="Approval explicitly denied.",
        )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _matches(matcher: PolicyMatcher, request: ActionRequest, tool: ToolManifest | None) -> bool:
    """Check whether a request/tool pair satisfies a policy matcher."""

    if matcher.tool_ids and request.tool_id not in matcher.tool_ids:
        return False

    if matcher.requester_dids and request.requester_did not in matcher.requester_dids:
        return False

    if matcher.risk_levels and tool:
        if tool.risk_level not in matcher.risk_levels:
            return False

    if matcher.categories and tool:
        # categories match against tags as a proxy
        if not (set(matcher.categories) & set(tool.tags)):
            return False

    return True


def _default_decision(request: ActionRequest, tool: ToolManifest | None) -> PolicyDecision:
    """Fallback policy when no explicit rule matches."""

    if tool and tool.risk_level == "high_impact":
        return PolicyDecision(
            allowed=False,
            action="require_approval",
            reason="Default policy: high_impact tools require explicit approval.",
        )
    return PolicyDecision(
        allowed=True,
        action="allow",
        reason="Default policy: allowed (no matching rule, risk not high_impact).",
    )
