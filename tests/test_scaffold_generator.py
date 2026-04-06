"""Tests for personified_software.openclaw_scaffold.generator — end-to-end."""

from __future__ import annotations

from pathlib import Path

from personified_software.openclaw_scaffold.generator import generate_scaffold
from personified_software.openclaw_scaffold.models import ScaffoldOptions


def _make_repo(tmp_path: Path) -> Path:
    """Create a minimal Python repo for scaffold generation."""
    repo = tmp_path / "sample-repo"
    repo.mkdir()
    (repo / "main.py").write_text("print('hello')\n", encoding="utf-8")
    (repo / "src").mkdir()
    (repo / "src" / "core.py").write_text("x = 1\n", encoding="utf-8")
    (repo / "tests").mkdir()
    (repo / "tests" / "test_core.py").write_text("def test_x(): pass\n", encoding="utf-8")
    return repo


# ---------------------------------------------------------------------------
# Basic generation
# ---------------------------------------------------------------------------

def test_generate_scaffold_creates_all_default_files(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    options = ScaffoldOptions(target_repo=repo)
    result = generate_scaffold(options)

    expected_files = {"SOUL.md", "skills.md", "AGENTS.md", "TOOLS.md", "SKILL.md"}
    created = {Path(f).name for f in result.created_files}
    assert expected_files == created

    for filename in expected_files:
        assert (repo / filename).exists()
        assert (repo / filename).read_text(encoding="utf-8").strip() != ""


def test_generate_scaffold_without_skill_alias(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    options = ScaffoldOptions(target_repo=repo, include_skill_alias=False)
    result = generate_scaffold(options)

    created = {Path(f).name for f in result.created_files}
    assert "SKILL.md" not in created
    assert not (repo / "SKILL.md").exists()


# ---------------------------------------------------------------------------
# Dry run
# ---------------------------------------------------------------------------

def test_generate_scaffold_dry_run_does_not_write_files(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    options = ScaffoldOptions(target_repo=repo, dry_run=True)
    result = generate_scaffold(options)

    assert len(result.created_files) == 0
    assert len(result.skipped_files) > 0
    for artifact in result.artifacts:
        assert not artifact.written
        assert artifact.skipped_reason == "dry_run=True"
        assert not (repo / artifact.path.name).exists() or artifact.existed_before


# ---------------------------------------------------------------------------
# Overwrite behavior
# ---------------------------------------------------------------------------

def test_generate_scaffold_skips_existing_without_overwrite(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    # First pass: create files
    generate_scaffold(ScaffoldOptions(target_repo=repo))
    original_content = (repo / "SOUL.md").read_text(encoding="utf-8")

    # Second pass: no overwrite
    result = generate_scaffold(ScaffoldOptions(target_repo=repo))
    assert len(result.created_files) == 0
    assert all("exists" in (a.skipped_reason or "") for a in result.artifacts)
    assert (repo / "SOUL.md").read_text(encoding="utf-8") == original_content


def test_generate_scaffold_overwrites_existing_with_flag(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    generate_scaffold(ScaffoldOptions(target_repo=repo))
    result = generate_scaffold(ScaffoldOptions(target_repo=repo, overwrite=True))
    assert len(result.created_files) > 0
    assert all(a.written for a in result.artifacts)


# ---------------------------------------------------------------------------
# STYLE.md generation
# ---------------------------------------------------------------------------

def test_generate_scaffold_with_style(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    options = ScaffoldOptions(target_repo=repo, include_style=True)
    result = generate_scaffold(options)

    created = {Path(f).name for f in result.created_files}
    assert "STYLE.md" in created
    assert (repo / "STYLE.md").exists()
    content = (repo / "STYLE.md").read_text(encoding="utf-8")
    assert "Tone" in content


def test_generate_scaffold_without_style_by_default(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    options = ScaffoldOptions(target_repo=repo)
    result = generate_scaffold(options)

    created = {Path(f).name for f in result.created_files}
    assert "STYLE.md" not in created


# ---------------------------------------------------------------------------
# Custom output dir
# ---------------------------------------------------------------------------

def test_generate_scaffold_writes_to_custom_output_dir(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    output_dir = tmp_path / "custom-output"
    options = ScaffoldOptions(target_repo=repo, output_dir=output_dir)
    result = generate_scaffold(options)

    assert output_dir.exists()
    assert (output_dir / "SOUL.md").exists()
    assert len(result.created_files) > 0


# ---------------------------------------------------------------------------
# Profile correctness in generated content
# ---------------------------------------------------------------------------

def test_generated_content_reflects_repo_profile(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    options = ScaffoldOptions(target_repo=repo)
    generate_scaffold(options)

    soul_content = (repo / "SOUL.md").read_text(encoding="utf-8")
    assert "sample-repo" in soul_content
    assert "python" in soul_content.lower()

    agents_content = (repo / "AGENTS.md").read_text(encoding="utf-8")
    assert "sample-repo" in agents_content


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

def test_generate_scaffold_raises_for_nonexistent_target(tmp_path: Path) -> None:
    nonexistent = tmp_path / "does-not-exist"
    options = ScaffoldOptions(target_repo=nonexistent)
    try:
        generate_scaffold(options)
        raise AssertionError("Expected FileNotFoundError")
    except FileNotFoundError:
        pass


def test_generate_scaffold_raises_for_file_target(tmp_path: Path) -> None:
    file_path = tmp_path / "a-file.txt"
    file_path.write_text("not a directory", encoding="utf-8")
    options = ScaffoldOptions(target_repo=file_path)
    try:
        generate_scaffold(options)
        raise AssertionError("Expected NotADirectoryError")
    except NotADirectoryError:
        pass
