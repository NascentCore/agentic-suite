"""Tests for personified_software.openclaw_scaffold.templates."""

from __future__ import annotations

from pathlib import Path

from personified_software.openclaw_scaffold.models import RepoProfile
from personified_software.openclaw_scaffold.templates import (
    render_agents,
    render_skill_alias,
    render_skills,
    render_soul,
    render_tools,
)


def _make_profile() -> RepoProfile:
    return RepoProfile(
        repo_name="test-repo",
        repo_path=Path("/tmp/test-repo"),
        primary_language="python",
        additional_languages=["shell"],
        package_managers=["pip"],
        source_dirs=["src"],
        test_dirs=["tests"],
        docs_dirs=["docs"],
        entrypoint_candidates=["main.py"],
        test_commands=["python3 -m pytest -q"],
        run_commands=["python3 main.py"],
        risk_notes=["Contains .env"],
    )


# ---------------------------------------------------------------------------
# SOUL.md
# ---------------------------------------------------------------------------

def test_render_soul_contains_repo_name() -> None:
    content = render_soul(_make_profile())
    assert "test-repo" in content


def test_render_soul_contains_primary_language() -> None:
    content = render_soul(_make_profile())
    assert "python" in content


def test_render_soul_contains_risk_notes() -> None:
    content = render_soul(_make_profile())
    assert "Contains .env" in content


def test_render_soul_contains_reading_order() -> None:
    content = render_soul(_make_profile())
    assert "SOUL.md" in content
    assert "skills.md" in content
    assert "AGENTS.md" in content
    assert "TOOLS.md" in content


# ---------------------------------------------------------------------------
# skills.md
# ---------------------------------------------------------------------------

def test_render_skills_contains_repo_name() -> None:
    content = render_skills(_make_profile())
    assert "test-repo" in content


def test_render_skills_contains_test_commands() -> None:
    content = render_skills(_make_profile())
    assert "pytest" in content


def test_render_skills_contains_guardrails() -> None:
    content = render_skills(_make_profile())
    assert "Hard Guardrails" in content


# ---------------------------------------------------------------------------
# AGENTS.md
# ---------------------------------------------------------------------------

def test_render_agents_contains_boot_sequence() -> None:
    content = render_agents(_make_profile())
    assert "Boot Sequence" in content


def test_render_agents_contains_repo_facts() -> None:
    content = render_agents(_make_profile())
    assert "test-repo" in content
    assert "python" in content


def test_render_agents_contains_safety_rules() -> None:
    content = render_agents(_make_profile())
    assert "Safety Rules" in content


# ---------------------------------------------------------------------------
# TOOLS.md
# ---------------------------------------------------------------------------

def test_render_tools_contains_test_commands() -> None:
    content = render_tools(_make_profile())
    assert "pytest" in content


def test_render_tools_contains_run_commands() -> None:
    content = render_tools(_make_profile())
    assert "python3 main.py" in content


def test_render_tools_contains_troubleshooting() -> None:
    content = render_tools(_make_profile())
    assert "Troubleshooting" in content


# ---------------------------------------------------------------------------
# SKILL.md alias
# ---------------------------------------------------------------------------

def test_render_skill_alias_points_to_skills_md() -> None:
    content = render_skill_alias()
    assert "skills.md" in content


# ---------------------------------------------------------------------------
# Empty profile fallbacks
# ---------------------------------------------------------------------------

def test_render_soul_with_empty_profile_uses_fallbacks() -> None:
    profile = RepoProfile(
        repo_name="empty",
        repo_path=Path("/tmp/empty"),
        primary_language="unknown",
    )
    content = render_soul(profile)
    assert "empty" in content
    assert "unknown" in content
    # Fallback placeholders should be present
    assert "profile manually" in content.lower() or "Unknown" in content
