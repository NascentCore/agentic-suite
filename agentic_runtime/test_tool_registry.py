"""Tests for agentic_runtime.tool_registry — tool registration and lookup."""

from __future__ import annotations

from agentic_runtime.models import RuntimeCapability, RuntimeProfile, ToolManifest
from agentic_runtime.tool_registry import ToolRegistry, capability_to_manifest


class TestCapabilityToManifest:
    def test_conversion(self) -> None:
        cap = RuntimeCapability(
            capability_id="cap-1",
            name="get_users",
            description="List users",
            risk_level="read_only",
            tags=["users"],
        )
        manifest = capability_to_manifest(cap)
        assert manifest.tool_id == "cap-1"
        assert manifest.name == "get_users"
        assert manifest.risk_level == "read_only"
        assert manifest.tags == ["users"]


class TestToolRegistry:
    def test_register_and_get(self) -> None:
        reg = ToolRegistry(app_name="test")
        manifest = ToolManifest(tool_id="t1", name="ping")
        reg.register(manifest)
        assert reg.get("t1") is not None
        assert reg.get("t1").name == "ping"

    def test_get_by_name(self) -> None:
        reg = ToolRegistry(app_name="test")
        reg.register(ToolManifest(tool_id="t1", name="ping"))
        assert reg.get_by_name("ping") is not None
        assert reg.get_by_name("nonexistent") is None

    def test_unregister(self) -> None:
        reg = ToolRegistry(app_name="test")
        reg.register(ToolManifest(tool_id="t1", name="ping"))
        assert reg.unregister("t1") is True
        assert reg.get("t1") is None
        assert reg.unregister("t1") is False

    def test_search_by_tags(self) -> None:
        reg = ToolRegistry(app_name="test")
        reg.register(ToolManifest(tool_id="t1", name="a", tags=["admin"]))
        reg.register(ToolManifest(tool_id="t2", name="b", tags=["user"]))
        reg.register(ToolManifest(tool_id="t3", name="c", tags=["admin", "user"]))
        results = reg.search(tags=["admin"])
        assert len(results) == 2

    def test_search_by_risk(self) -> None:
        reg = ToolRegistry(app_name="test")
        reg.register(ToolManifest(tool_id="t1", name="a", risk_level="read_only"))
        reg.register(ToolManifest(tool_id="t2", name="b", risk_level="high_impact"))
        results = reg.search(risk_level="high_impact")
        assert len(results) == 1
        assert results[0].name == "b"

    def test_refresh_from_profile(self) -> None:
        profile = RuntimeProfile(
            app_name="api",
            capabilities=[
                RuntimeCapability(capability_id="c1", name="list"),
                RuntimeCapability(capability_id="c2", name="create"),
            ],
        )
        reg = ToolRegistry(app_name="api")
        count = reg.refresh_from_profile(profile)
        assert count == 2
        assert len(reg.tools) == 2

    def test_replace_on_duplicate_id(self) -> None:
        reg = ToolRegistry(app_name="test")
        reg.register(ToolManifest(tool_id="t1", name="old"))
        reg.register(ToolManifest(tool_id="t1", name="new"))
        assert len(reg.tools) == 1
        assert reg.get("t1").name == "new"

    def test_clear(self) -> None:
        reg = ToolRegistry(app_name="test")
        reg.register(ToolManifest(tool_id="t1", name="a"))
        reg.clear()
        assert len(reg.tools) == 0

    def test_export_state(self) -> None:
        reg = ToolRegistry(app_name="test")
        reg.register(ToolManifest(tool_id="t1", name="a"))
        state = reg.export_state()
        assert state.app_name == "test"
        assert len(state.tools) == 1
