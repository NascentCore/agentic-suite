"""Tests for personified_software.openclaw_scaffold.detector."""

from __future__ import annotations

from pathlib import Path

from personified_software.openclaw_scaffold.detector import detect_repo_profile


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_file(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("", encoding="utf-8")


# ---------------------------------------------------------------------------
# Language detection
# ---------------------------------------------------------------------------

def test_detect_primary_language_python(tmp_path: Path) -> None:
    _make_file(tmp_path / "main.py")
    _make_file(tmp_path / "utils.py")
    profile = detect_repo_profile(tmp_path)
    assert profile.primary_language == "python"


def test_detect_primary_language_javascript(tmp_path: Path) -> None:
    _make_file(tmp_path / "index.js")
    _make_file(tmp_path / "app.js")
    _make_file(tmp_path / "helper.py")
    profile = detect_repo_profile(tmp_path)
    assert profile.primary_language == "javascript"
    assert "python" in profile.additional_languages


def test_detect_unknown_language_for_empty_repo(tmp_path: Path) -> None:
    profile = detect_repo_profile(tmp_path)
    assert profile.primary_language == "unknown"
    assert profile.additional_languages == []


# ---------------------------------------------------------------------------
# Package manager detection
# ---------------------------------------------------------------------------

def test_detect_package_manager_pip(tmp_path: Path) -> None:
    _make_file(tmp_path / "requirements.txt")
    profile = detect_repo_profile(tmp_path)
    assert "pip" in profile.package_managers


def test_detect_package_manager_npm(tmp_path: Path) -> None:
    _make_file(tmp_path / "package.json")
    profile = detect_repo_profile(tmp_path)
    assert "npm" in profile.package_managers


def test_detect_package_manager_cargo(tmp_path: Path) -> None:
    _make_file(tmp_path / "Cargo.toml")
    profile = detect_repo_profile(tmp_path)
    assert "cargo" in profile.package_managers


def test_detect_package_manager_go(tmp_path: Path) -> None:
    _make_file(tmp_path / "go.mod")
    profile = detect_repo_profile(tmp_path)
    assert "go" in profile.package_managers


def test_detect_package_manager_pyproject(tmp_path: Path) -> None:
    _make_file(tmp_path / "pyproject.toml")
    profile = detect_repo_profile(tmp_path)
    assert "pyproject" in profile.package_managers


# ---------------------------------------------------------------------------
# Directory detection
# ---------------------------------------------------------------------------

def test_detect_source_dirs(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "lib").mkdir()
    profile = detect_repo_profile(tmp_path)
    assert "src" in profile.source_dirs
    assert "lib" in profile.source_dirs


def test_detect_test_dirs(tmp_path: Path) -> None:
    (tmp_path / "tests").mkdir()
    profile = detect_repo_profile(tmp_path)
    assert "tests" in profile.test_dirs


def test_detect_docs_dirs(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    profile = detect_repo_profile(tmp_path)
    assert "docs" in profile.docs_dirs


# ---------------------------------------------------------------------------
# Entrypoint detection
# ---------------------------------------------------------------------------

def test_detect_entrypoint_main_py(tmp_path: Path) -> None:
    _make_file(tmp_path / "main.py")
    profile = detect_repo_profile(tmp_path)
    assert "main.py" in profile.entrypoint_candidates


def test_detect_entrypoint_app_py(tmp_path: Path) -> None:
    _make_file(tmp_path / "app.py")
    profile = detect_repo_profile(tmp_path)
    assert "app.py" in profile.entrypoint_candidates


def test_detect_entrypoint_package_json(tmp_path: Path) -> None:
    _make_file(tmp_path / "package.json")
    profile = detect_repo_profile(tmp_path)
    assert "package.json scripts" in profile.entrypoint_candidates


# ---------------------------------------------------------------------------
# Test commands detection
# ---------------------------------------------------------------------------

def test_detect_test_commands_python(tmp_path: Path) -> None:
    _make_file(tmp_path / "main.py")
    profile = detect_repo_profile(tmp_path)
    assert any("pytest" in cmd for cmd in profile.test_commands)


def test_detect_test_commands_javascript(tmp_path: Path) -> None:
    _make_file(tmp_path / "index.js")
    _make_file(tmp_path / "package.json")
    profile = detect_repo_profile(tmp_path)
    assert any("npm test" in cmd for cmd in profile.test_commands)


# ---------------------------------------------------------------------------
# Risk detection
# ---------------------------------------------------------------------------

def test_detect_risk_env_file(tmp_path: Path) -> None:
    _make_file(tmp_path / ".env")
    profile = detect_repo_profile(tmp_path)
    assert any(".env" in note for note in profile.risk_notes)


def test_detect_risk_github_workflows(tmp_path: Path) -> None:
    (tmp_path / ".github" / "workflows").mkdir(parents=True)
    profile = detect_repo_profile(tmp_path)
    assert any("CI" in note for note in profile.risk_notes)


def test_detect_risk_deploy_dir(tmp_path: Path) -> None:
    (tmp_path / "deploy").mkdir()
    profile = detect_repo_profile(tmp_path)
    assert any("Deployment" in note or "deploy" in note for note in profile.risk_notes)


# ---------------------------------------------------------------------------
# Ignored directories
# ---------------------------------------------------------------------------

def test_ignored_dirs_are_not_counted(tmp_path: Path) -> None:
    """Files inside .git, __pycache__, node_modules etc. should be ignored."""
    (tmp_path / "__pycache__").mkdir()
    _make_file(tmp_path / "__pycache__" / "cached.py")
    (tmp_path / "node_modules").mkdir()
    _make_file(tmp_path / "node_modules" / "pkg.js")
    # Only real source
    _make_file(tmp_path / "app.go")
    profile = detect_repo_profile(tmp_path)
    assert profile.primary_language == "go"


# ---------------------------------------------------------------------------
# Repo name
# ---------------------------------------------------------------------------

def test_repo_name_matches_directory_name(tmp_path: Path) -> None:
    profile = detect_repo_profile(tmp_path)
    assert profile.repo_name == tmp_path.resolve().name
