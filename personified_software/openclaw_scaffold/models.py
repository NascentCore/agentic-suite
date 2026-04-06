from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

IGNORED_DIR_NAMES: tuple[str, ...] = (
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".idea",
    ".vscode",
    ".cursor",
    ".pytest_cache",
    "dist",
    "build",
)


DEFAULT_OUTPUT_FILENAMES: tuple[str, ...] = (
    "SOUL.md",
    "skills.md",
    "AGENTS.md",
    "TOOLS.md",
)


@dataclass(slots=True)
class RepoProfile:
    repo_name: str
    repo_path: Path
    primary_language: str
    additional_languages: list[str] = field(default_factory=list)
    package_managers: list[str] = field(default_factory=list)
    source_dirs: list[str] = field(default_factory=list)
    test_dirs: list[str] = field(default_factory=list)
    docs_dirs: list[str] = field(default_factory=list)
    entrypoint_candidates: list[str] = field(default_factory=list)
    test_commands: list[str] = field(default_factory=list)
    run_commands: list[str] = field(default_factory=list)
    risk_notes: list[str] = field(default_factory=list)

    def to_template_context(self) -> dict[str, str]:
        return {
            "REPO_NAME": self.repo_name,
            "REPO_PATH": str(self.repo_path),
            "PRIMARY_LANGUAGE": self.primary_language,
            "ADDITIONAL_LANGUAGES": _join_or_default(self.additional_languages),
            "PACKAGE_MANAGERS": _join_or_default(self.package_managers),
            "SOURCE_DIRS": _as_markdown_bullets(
                self.source_dirs,
                fallback="- Unknown: profile manually.",
            ),
            "TEST_DIRS": _as_markdown_bullets(
                self.test_dirs,
                fallback="- Unknown: profile manually.",
            ),
            "DOCS_DIRS": _as_markdown_bullets(
                self.docs_dirs,
                fallback="- Unknown: profile manually.",
            ),
            "ENTRYPOINT_CANDIDATES": _as_markdown_bullets(
                self.entrypoint_candidates,
                fallback="- Unknown: identify executable entry points manually.",
            ),
            "TEST_COMMANDS": _as_markdown_bullets(
                self.test_commands,
                fallback="- Add project-specific test commands.",
            ),
            "RUN_COMMANDS": _as_markdown_bullets(
                self.run_commands,
                fallback="- Add project-specific run/demo commands.",
            ),
            "RISK_NOTES": _as_markdown_bullets(
                self.risk_notes,
                fallback="- No elevated-risk areas detected automatically.",
            ),
        }


@dataclass(slots=True)
class ScaffoldOptions:
    target_repo: Path
    output_dir: Path | None = None
    include_skill_alias: bool = True
    overwrite: bool = False
    dry_run: bool = False

    def resolved_output_dir(self) -> Path:
        return self.output_dir if self.output_dir is not None else self.target_repo

    def output_filenames(self) -> list[str]:
        files = list(DEFAULT_OUTPUT_FILENAMES)
        if self.include_skill_alias:
            files.append("SKILL.md")
        return files


@dataclass(slots=True)
class RenderedArtifact:
    path: Path
    content: str
    existed_before: bool
    written: bool
    skipped_reason: str | None = None


@dataclass(slots=True)
class ScaffoldResult:
    profile: RepoProfile
    artifacts: list[RenderedArtifact]

    @property
    def created_files(self) -> list[str]:
        return [str(artifact.path) for artifact in self.artifacts if artifact.written]

    @property
    def skipped_files(self) -> list[str]:
        return [str(artifact.path) for artifact in self.artifacts if not artifact.written]


def _join_or_default(values: list[str]) -> str:
    if not values:
        return "unknown (profile manually)"
    return ", ".join(values)


def _as_markdown_bullets(values: list[str], fallback: str) -> str:
    if not values:
        return fallback
    return "\n".join(f"- {value}" for value in values)
