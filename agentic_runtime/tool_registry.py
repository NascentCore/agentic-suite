"""Tool Registry — central index of typed tool manifests for a running application.

Implements the *Tool Registry* component from ``BRAIN_STORM.md §4.1``.

The registry converts discovered ``RuntimeCapability`` instances into
``ToolManifest`` entries that agents can invoke via the executor.
"""

from __future__ import annotations

from datetime import datetime

from .models import (
    RuntimeCapability,
    RuntimeProfile,
    ToolManifest,
    ToolRegistryState,
    _new_id,
    _utc_now,
)


class ToolRegistry:
    """In-memory tool registry backed by ``ToolRegistryState``."""

    def __init__(self, app_name: str) -> None:
        self._state = ToolRegistryState(app_name=app_name)

    # -- public API ---------------------------------------------------------

    @property
    def app_name(self) -> str:
        return self._state.app_name

    @property
    def tools(self) -> list[ToolManifest]:
        return list(self._state.tools)

    @property
    def last_refreshed(self) -> datetime:
        return self._state.last_refreshed

    def register(self, manifest: ToolManifest) -> ToolManifest:
        """Register a single tool manifest. Replaces existing entry with same ``tool_id``."""
        self._state.tools = [t for t in self._state.tools if t.tool_id != manifest.tool_id]
        self._state.tools.append(manifest)
        self._state.last_refreshed = _utc_now()
        return manifest

    def unregister(self, tool_id: str) -> bool:
        """Remove a tool by ID. Returns True if found and removed."""
        before = len(self._state.tools)
        self._state.tools = [t for t in self._state.tools if t.tool_id != tool_id]
        return len(self._state.tools) < before

    def get(self, tool_id: str) -> ToolManifest | None:
        """Look up a tool by ID."""
        for tool in self._state.tools:
            if tool.tool_id == tool_id:
                return tool
        return None

    def get_by_name(self, name: str) -> ToolManifest | None:
        """Look up a tool by name (first match)."""
        for tool in self._state.tools:
            if tool.name == name:
                return tool
        return None

    def search(self, *, tags: list[str] | None = None, risk_level: str | None = None) -> list[ToolManifest]:
        """Filter tools by tags and/or risk level."""
        results = self._state.tools
        if tags:
            tag_set = set(tags)
            results = [t for t in results if tag_set & set(t.tags)]
        if risk_level:
            results = [t for t in results if t.risk_level == risk_level]
        return results

    def refresh_from_profile(self, profile: RuntimeProfile) -> int:
        """Bulk-import capabilities from a ``RuntimeProfile``, converting each to a
        ``ToolManifest``. Returns number of tools registered."""

        count = 0
        for cap in profile.capabilities:
            manifest = capability_to_manifest(cap)
            self.register(manifest)
            count += 1
        self._state.last_refreshed = _utc_now()
        return count

    def export_state(self) -> ToolRegistryState:
        """Return a serialisable snapshot of registry state."""
        return self._state.model_copy(deep=True)

    def clear(self) -> None:
        """Remove all tools."""
        self._state.tools.clear()
        self._state.last_refreshed = _utc_now()


# ---------------------------------------------------------------------------
# Conversion helpers
# ---------------------------------------------------------------------------

def capability_to_manifest(cap: RuntimeCapability) -> ToolManifest:
    """Convert a discovered ``RuntimeCapability`` into a ``ToolManifest``."""

    return ToolManifest(
        tool_id=cap.capability_id,
        name=cap.name,
        description=cap.description,
        input_schema=cap.input_schema,
        output_schema=cap.output_schema,
        risk_level=cap.risk_level,
        requires_approval=cap.requires_approval,
        idempotent=cap.idempotent,
        sla_hint_ms=cap.estimated_duration_ms,
        tags=list(cap.tags),
    )
