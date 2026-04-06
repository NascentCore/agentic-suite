"""Tests for personified_software.openclaw_scaffold.models."""

from __future__ import annotations

from pathlib import Path

from personified_software.openclaw_scaffold.models import (
    DEFAULT_OUTPUT_FILENAMES,
    RenderedArtifact,
    RepoProfile,
    ScaffoldOptions,
    ScaffoldResult,
)

# ---------------------------------------------------------------------------
# RepoProfile
# ---------------------------------------------------------------------------

def test_repo_profile_to_template_context_with_populated_fields() -> None:
    profile = RepoProfile(
        repo_name="my-repo",
        repo_path=Path("/tmp/my-repo"),
        primary_language="python",
        additional_languages=["javascript", "shell"],
        package_managers=["pip", "npm"],
        source_dirs=["src", "lib"],
        test_dirs=["tests"],
        docs_dirs=["docs"],
        entrypoint_candidates=["main.py"],
        test_commands=["pytest"],
        run_commands=["python main.py"],
        risk_notes=["Contains .env"],
    )
    ctx = profile.to_template_context()

    assert ctx["REPO_NAME"] == "my-repo"
    assert ctx["PRIMARY_LANGUAGE"] == "python"
    assert "javascript" in ctx["ADDITIONAL_LANGUAGES"]
    assert "pip" in ctx["PACKAGE_MANAGERS"]
    assert "- src" in ctx["SOURCE_DIRS"]
    assert "- lib" in ctx["SOURCE_DIRS"]
    assert "- tests" in ctx["TEST_DIRS"]
    assert "- docs" in ctx["DOCS_DIRS"]
    assert "- main.py" in ctx["ENTRYPOINT_CANDIDATES"]
    assert "- pytest" in ctx["TEST_COMMANDS"]
    assert "- python main.py" in ctx["RUN_COMMANDS"]
    assert "Contains .env" in ctx["RISK_NOTES"]


def test_repo_profile_to_template_context_with_empty_fields() -> None:
    profile = RepoProfile(
        repo_name="empty-repo",
        repo_path=Path("/tmp/empty-repo"),
        primary_language="unknown",
    )
    ctx = profile.to_template_context()

    assert ctx["REPO_NAME"] == "empty-repo"
    assert ctx["PRIMARY_LANGUAGE"] == "unknown"
    assert "unknown (profile manually)" in ctx["ADDITIONAL_LANGUAGES"]
    assert "Unknown" in ctx["SOURCE_DIRS"]
    assert "Unknown" in ctx["TEST_DIRS"]
    assert "Unknown" in ctx["DOCS_DIRS"]
    assert "Unknown" in ctx["ENTRYPOINT_CANDIDATES"]


# ---------------------------------------------------------------------------
# ScaffoldOptions
# ---------------------------------------------------------------------------

def test_scaffold_options_resolved_output_dir_defaults_to_target() -> None:
    opts = ScaffoldOptions(target_repo=Path("/tmp/repo"))
    assert opts.resolved_output_dir() == Path("/tmp/repo")


def test_scaffold_options_resolved_output_dir_uses_explicit_value() -> None:
    opts = ScaffoldOptions(target_repo=Path("/tmp/repo"), output_dir=Path("/tmp/output"))
    assert opts.resolved_output_dir() == Path("/tmp/output")


def test_scaffold_options_output_filenames_includes_skill_alias_by_default() -> None:
    opts = ScaffoldOptions(target_repo=Path("/tmp/repo"))
    filenames = opts.output_filenames()
    assert "SKILL.md" in filenames
    assert all(f in filenames for f in DEFAULT_OUTPUT_FILENAMES)


def test_scaffold_options_output_filenames_excludes_skill_alias_when_disabled() -> None:
    opts = ScaffoldOptions(target_repo=Path("/tmp/repo"), include_skill_alias=False)
    filenames = opts.output_filenames()
    assert "SKILL.md" not in filenames


# ---------------------------------------------------------------------------
# ScaffoldResult
# ---------------------------------------------------------------------------

def test_scaffold_result_created_and_skipped_files() -> None:
    artifacts = [
        RenderedArtifact(
            path=Path("/tmp/SOUL.md"),
            content="content",
            existed_before=False,
            written=True,
        ),
        RenderedArtifact(
            path=Path("/tmp/AGENTS.md"),
            content="content",
            existed_before=True,
            written=False,
            skipped_reason="exists and overwrite=False",
        ),
    ]
    profile = RepoProfile(
        repo_name="test",
        repo_path=Path("/tmp/test"),
        primary_language="python",
    )
    result = ScaffoldResult(profile=profile, artifacts=artifacts)

    assert len(result.created_files) == 1
    assert "/tmp/SOUL.md" in result.created_files[0]
    assert len(result.skipped_files) == 1
    assert "/tmp/AGENTS.md" in result.skipped_files[0]
