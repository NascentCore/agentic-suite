"""Tests for personified_software.openclaw_scaffold.cli — argument parsing."""

from __future__ import annotations

from pathlib import Path

from personified_software.openclaw_scaffold.cli import build_parser


def test_parser_requires_target_repo() -> None:
    parser = build_parser()
    try:
        parser.parse_args([])
        raise AssertionError("Expected SystemExit for missing target_repo")
    except SystemExit:
        pass


def test_parser_accepts_target_repo(tmp_path: Path) -> None:
    parser = build_parser()
    args = parser.parse_args([str(tmp_path)])
    assert args.target_repo == tmp_path


def test_parser_output_dir_default_is_none(tmp_path: Path) -> None:
    parser = build_parser()
    args = parser.parse_args([str(tmp_path)])
    assert args.output_dir is None


def test_parser_output_dir_flag(tmp_path: Path) -> None:
    parser = build_parser()
    output = tmp_path / "out"
    args = parser.parse_args([str(tmp_path), "--output-dir", str(output)])
    assert args.output_dir == output


def test_parser_no_skill_alias_flag(tmp_path: Path) -> None:
    parser = build_parser()
    args = parser.parse_args([str(tmp_path), "--no-skill-alias"])
    assert args.no_skill_alias is True


def test_parser_overwrite_flag(tmp_path: Path) -> None:
    parser = build_parser()
    args = parser.parse_args([str(tmp_path), "--overwrite"])
    assert args.overwrite is True


def test_parser_dry_run_flag(tmp_path: Path) -> None:
    parser = build_parser()
    args = parser.parse_args([str(tmp_path), "--dry-run"])
    assert args.dry_run is True


def test_parser_all_flags_combined(tmp_path: Path) -> None:
    parser = build_parser()
    output = tmp_path / "out"
    args = parser.parse_args([
        str(tmp_path),
        "--output-dir", str(output),
        "--no-skill-alias",
        "--overwrite",
        "--dry-run",
    ])
    assert args.target_repo == tmp_path
    assert args.output_dir == output
    assert args.no_skill_alias is True
    assert args.overwrite is True
    assert args.dry_run is True
