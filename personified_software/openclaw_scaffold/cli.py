from __future__ import annotations

import argparse
from pathlib import Path

from .generator import generate_scaffold
from .models import ScaffoldOptions


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="personified-scaffold",
        description=(
            "Generate OpenClaw-like personified scaffold files "
            "for any target repository."
        ),
    )
    parser.add_argument(
        "target_repo",
        type=Path,
        help="Path to the target repository to profile.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory for generated files (defaults to target repo root).",
    )
    parser.add_argument(
        "--no-skill-alias",
        action="store_true",
        help="Do not generate SKILL.md compatibility shim.",
    )
    parser.add_argument(
        "--include-style",
        action="store_true",
        help="Also generate STYLE.md communication style profile.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing scaffold files.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Render outputs without writing files.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    options = ScaffoldOptions(
        target_repo=args.target_repo,
        output_dir=args.output_dir,
        include_skill_alias=not args.no_skill_alias,
        include_style=args.include_style,
        overwrite=args.overwrite,
        dry_run=args.dry_run,
    )
    result = generate_scaffold(options)

    print("Scaffold generation summary")
    print(f"- target repo: {result.profile.repo_path}")
    print(f"- primary language: {result.profile.primary_language}")
    print(f"- package managers: {', '.join(result.profile.package_managers) or 'unknown'}")
    print("- artifacts:")
    for artifact in result.artifacts:
        status = "written" if artifact.written else f"skipped ({artifact.skipped_reason})"
        print(f"  - {artifact.path}: {status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
