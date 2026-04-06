"""Core data models for the Agentic Runtime layer.

Design reference
----------------
- **RuntimeCapability / RuntimeProfile** mirror ``personified_software.openclaw_scaffold.models.RepoProfile``
  but describe a *running* application rather than a static code repository.
- **ToolManifest / ToolRegistry** implement the *Typed Tool Invocation* pattern from ``BRAIN_STORM.md``.
- **ActionRequest / ActionResponse / ExecutionProvenance** implement the *Execution Runtime* +
  *Provenance and Attestation* patterns.
- **RuntimeSession** supports multi-turn conversational interaction with checkpoint/resume.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# Runtime Capability Discovery
# ---------------------------------------------------------------------------

class RuntimeCapability(BaseModel):
    """A single invocable capability exposed by a running application."""

    model_config = ConfigDict(extra="forbid")

    capability_id: str = Field(default_factory=_new_id)
    name: str
    description: str = ""
    category: Literal["api", "cli", "db", "file", "message", "custom"] = "api"
    input_schema: dict[str, Any] = Field(default_factory=dict)
    output_schema: dict[str, Any] = Field(default_factory=dict)
    risk_level: Literal["read_only", "bounded_write", "high_impact"] = "read_only"
    requires_approval: bool = False
    idempotent: bool = True
    estimated_duration_ms: int | None = None
    tags: list[str] = Field(default_factory=list)


class RuntimeDetectorConfig(BaseModel):
    """Configuration for the runtime capability discovery process."""

    model_config = ConfigDict(extra="forbid")

    app_name: str
    app_type: Literal["web_service", "cli_tool", "desktop_app", "library", "daemon"] = "web_service"
    # OpenAPI / Swagger
    openapi_url: str | None = None
    openapi_path: str | None = None
    # CLI introspection
    cli_command: str | None = None
    # Manual manifest (YAML/JSON)
    manifest_path: str | None = None
    # Base URL for web services
    base_url: str | None = None
    # Health endpoint
    health_endpoint: str | None = None
    # Auth method hint
    auth_method: str | None = None


class RuntimeProfile(BaseModel):
    """A discovered profile for a running application — analogous to ``RepoProfile``."""

    model_config = ConfigDict(extra="forbid")

    app_name: str
    app_type: Literal["web_service", "cli_tool", "desktop_app", "library", "daemon"] = "web_service"
    base_url: str | None = None
    capabilities: list[RuntimeCapability] = Field(default_factory=list)
    health_endpoint: str | None = None
    auth_method: str | None = None
    discovered_at: datetime = Field(default_factory=_utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)

    # ---- template context (mirrors RepoProfile.to_template_context) ----

    def to_template_context(self) -> dict[str, str]:
        cap_bullets = "\n".join(
            f"- **{c.name}** (`{c.category}`, risk={c.risk_level}): {c.description}"
            for c in self.capabilities
        ) or "- No capabilities discovered yet."
        return {
            "APP_NAME": self.app_name,
            "APP_TYPE": self.app_type,
            "BASE_URL": self.base_url or "N/A",
            "HEALTH_ENDPOINT": self.health_endpoint or "N/A",
            "AUTH_METHOD": self.auth_method or "none",
            "CAPABILITY_COUNT": str(len(self.capabilities)),
            "CAPABILITY_LIST": cap_bullets,
        }


# ---------------------------------------------------------------------------
# Tool Registry (Typed Tool Invocation pattern)
# ---------------------------------------------------------------------------

class ToolManifest(BaseModel):
    """Typed tool manifest — one entry per registered runtime capability."""

    model_config = ConfigDict(extra="forbid")

    tool_id: str = Field(default_factory=_new_id)
    name: str
    version: str = "0.1.0"
    description: str = ""
    input_schema: dict[str, Any] = Field(default_factory=dict)
    output_schema: dict[str, Any] = Field(default_factory=dict)
    auth_scope: str = "default"
    risk_level: Literal["read_only", "bounded_write", "high_impact"] = "read_only"
    requires_approval: bool = False
    idempotent: bool = True
    cost_hint: str | None = None
    sla_hint_ms: int | None = None
    tags: list[str] = Field(default_factory=list)


class ToolRegistryState(BaseModel):
    """Central index of all registered tools for a running application."""

    model_config = ConfigDict(extra="forbid")

    app_name: str
    tools: list[ToolManifest] = Field(default_factory=list)
    last_refreshed: datetime = Field(default_factory=_utc_now)


# ---------------------------------------------------------------------------
# Execution Model
# ---------------------------------------------------------------------------

class ExecutionProvenance(BaseModel):
    """Provenance record attached to every action execution (BRAIN_STORM §H)."""

    model_config = ConfigDict(extra="forbid")

    prompt_hash: str | None = None
    model_version: str | None = None
    tool_input: dict[str, Any] = Field(default_factory=dict)
    tool_output: dict[str, Any] = Field(default_factory=dict)
    policy_decisions: list[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=_utc_now)


class ActionRequest(BaseModel):
    """A typed invocation request against a registered tool."""

    model_config = ConfigDict(extra="forbid")

    request_id: str = Field(default_factory=_new_id)
    trace_id: str = Field(default_factory=_new_id)
    idempotency_key: str = Field(default_factory=_new_id)
    tool_id: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    requester_did: str = ""
    purpose: str = ""
    deadline_ms: int | None = None
    created_at: datetime = Field(default_factory=_utc_now)


class ActionResponse(BaseModel):
    """The result of executing an ``ActionRequest``."""

    model_config = ConfigDict(extra="forbid")

    request_id: str
    status: Literal["success", "failed", "requires_approval", "timeout", "cancelled"]
    result: dict[str, Any] | None = None
    error: dict[str, Any] | None = None
    execution_ms: int = 0
    provenance: ExecutionProvenance = Field(default_factory=ExecutionProvenance)
    approval_token: str | None = None


# ---------------------------------------------------------------------------
# Policy (runtime subset — full engine in policy_engine.py)
# ---------------------------------------------------------------------------

class PolicyMatcher(BaseModel):
    """Matching predicate for a policy rule."""

    model_config = ConfigDict(extra="forbid")

    tool_ids: list[str] | None = None
    risk_levels: list[Literal["read_only", "bounded_write", "high_impact"]] | None = None
    requester_dids: list[str] | None = None
    categories: list[str] | None = None


class RateLimitConfig(BaseModel):
    """Rate-limiting parameters."""

    model_config = ConfigDict(extra="forbid")

    max_calls: int = 60
    window_seconds: int = 60


class ApprovalConfig(BaseModel):
    """Parameters for the Human Approval Gate pattern."""

    model_config = ConfigDict(extra="forbid")

    approver_dids: list[str] = Field(default_factory=list)
    timeout_seconds: int = 300
    auto_deny_on_timeout: bool = True


class PolicyRule(BaseModel):
    """A single policy rule evaluated by the RuntimePolicyEngine."""

    model_config = ConfigDict(extra="forbid")

    rule_id: str = Field(default_factory=_new_id)
    match: PolicyMatcher = Field(default_factory=PolicyMatcher)
    action: Literal["allow", "deny", "require_approval", "rate_limit"] = "allow"
    priority: int = 0
    rate_limit: RateLimitConfig | None = None
    approval_config: ApprovalConfig | None = None


class PolicyDecision(BaseModel):
    """Result of evaluating policy for an ``ActionRequest``."""

    model_config = ConfigDict(extra="forbid")

    allowed: bool
    action: Literal["allow", "deny", "require_approval", "rate_limit"]
    reason: str
    approval_token: str | None = None


# ---------------------------------------------------------------------------
# Session State
# ---------------------------------------------------------------------------

class RuntimeSession(BaseModel):
    """Multi-turn conversational session with a running application."""

    model_config = ConfigDict(extra="forbid")

    session_id: str = Field(default_factory=_new_id)
    user_did: str = ""
    app_name: str = ""
    started_at: datetime = Field(default_factory=_utc_now)
    last_active: datetime = Field(default_factory=_utc_now)
    history: list[dict[str, Any]] = Field(default_factory=list)
    context: dict[str, Any] = Field(default_factory=dict)
    checkpoint: str | None = None


# ---------------------------------------------------------------------------
# Saga Step (for multi-step execution with compensation)
# ---------------------------------------------------------------------------

class SagaStep(BaseModel):
    """One step in a saga — pairs a forward action with its compensating action."""

    model_config = ConfigDict(extra="forbid")

    step_id: str = Field(default_factory=_new_id)
    forward: ActionRequest
    compensator: ActionRequest | None = None
    status: Literal["pending", "succeeded", "failed", "compensated"] = "pending"
    response: ActionResponse | None = None
