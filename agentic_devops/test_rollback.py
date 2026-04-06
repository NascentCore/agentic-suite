"""Tests for agentic_devops.rollback — version tracking and rollback."""

from __future__ import annotations

from agentic_devops.models import RollbackStrategy
from agentic_devops.rollback import RollbackEngine


class TestVersionTracking:
    def test_record_and_retrieve(self) -> None:
        engine = RollbackEngine()
        v1 = engine.record_deployment("staging", "v1.0.0", commit_sha="abc123")
        assert v1.version_id == "v1.0.0"
        current = engine.current_version("staging")
        assert current is not None
        assert current.version_id == "v1.0.0"

    def test_version_ordering(self) -> None:
        engine = RollbackEngine()
        engine.record_deployment("prod", "v1.0.0")
        engine.record_deployment("prod", "v1.1.0")
        engine.record_deployment("prod", "v1.2.0")
        current = engine.current_version("prod")
        assert current.version_id == "v1.2.0"
        previous = engine.previous_version("prod")
        assert previous.version_id == "v1.1.0"

    def test_history(self) -> None:
        engine = RollbackEngine()
        engine.record_deployment("dev", "v1")
        engine.record_deployment("dev", "v2")
        engine.record_deployment("dev", "v3")
        history = engine.version_history("dev")
        assert len(history) == 3
        assert history[0].version_id == "v3"  # newest first

    def test_empty_environment(self) -> None:
        engine = RollbackEngine()
        assert engine.current_version("prod") is None
        assert engine.previous_version("prod") is None
        assert engine.version_history("prod") == []


class TestRollback:
    def test_can_rollback(self) -> None:
        engine = RollbackEngine()
        engine.record_deployment("prod", "v1")
        engine.record_deployment("prod", "v2")
        assert engine.can_rollback("prod", depth=1) is True
        assert engine.can_rollback("prod", depth=2) is False  # only 2 versions

    def test_cannot_rollback_empty(self) -> None:
        engine = RollbackEngine()
        assert engine.can_rollback("prod") is False

    def test_depth_exceeds_max(self) -> None:
        engine = RollbackEngine(rollback_strategy=RollbackStrategy(max_rollback_depth=1))
        engine.record_deployment("prod", "v1")
        engine.record_deployment("prod", "v2")
        engine.record_deployment("prod", "v3")
        assert engine.can_rollback("prod", depth=1) is True
        assert engine.can_rollback("prod", depth=2) is False

    def test_get_rollback_target(self) -> None:
        engine = RollbackEngine()
        engine.record_deployment("prod", "v1")
        engine.record_deployment("prod", "v2")
        engine.record_deployment("prod", "v3")
        target = engine.get_rollback_target("prod", depth=2)
        assert target is not None
        assert target.version_id == "v1"

    def test_execute_rollback_success(self) -> None:
        engine = RollbackEngine()
        engine.record_deployment("prod", "v1.0.0", commit_sha="aaa")
        engine.record_deployment("prod", "v1.1.0", commit_sha="bbb")
        result = engine.execute_rollback("prod", depth=1)
        assert result["success"] is True
        assert result["to_version"]["version_id"] == "v1.0.0"
        assert result["from_version"]["version_id"] == "v1.1.0"
        # Current version should now be the rollback
        current = engine.current_version("prod")
        assert "rollback" in current.version_id

    def test_execute_rollback_insufficient_history(self) -> None:
        engine = RollbackEngine()
        engine.record_deployment("prod", "v1.0.0")
        result = engine.execute_rollback("prod", depth=1)
        assert result["success"] is False

    def test_version_metadata(self) -> None:
        engine = RollbackEngine()
        v = engine.record_deployment("prod", "v1", metadata={"deployer": "alice"})
        assert v.metadata["deployer"] == "alice"
        d = v.to_dict()
        assert d["metadata"]["deployer"] == "alice"
