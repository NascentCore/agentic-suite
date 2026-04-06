from __future__ import annotations

import os
from collections import Counter
from pathlib import Path

from .models import IGNORED_DIR_NAMES, RepoProfile


EXTENSION_TO_LANGUAGE: dict[str, str] = {
    ".py": "python",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".js": "javascript",
    ".jsx": "javascript",
    ".go": "go",
    ".rs": "rust",
    ".java": "java",
    ".kt": "kotlin",
    ".rb": "ruby",
    ".php": "php",
    ".cs": "csharp",
    ".sh": "shell",
}


def detect_repo_profile(target_repo: Path) -> RepoProfile:
    language_counter = _count_languages(target_repo)
    primary_language, additional_languages = _resolve_languages(language_counter)
    package_managers = _detect_package_managers(target_repo)
    source_dirs = _detect_named_dirs(target_repo, ("src", "app", "lib"))
    test_dirs = _detect_named_dirs(target_repo, ("tests", "test", "spec"))
    docs_dirs = _detect_named_dirs(target_repo, ("docs", "doc"))
    entrypoints = _detect_entrypoints(target_repo)
    test_commands = _detect_test_commands(target_repo, primary_language, package_managers)
    run_commands = _detect_run_commands(target_repo, primary_language, package_managers)
    risk_notes = _detect_risk_notes(target_repo)

    return RepoProfile(
        repo_name=target_repo.resolve().name,
        repo_path=target_repo.resolve(),
        primary_language=primary_language,
        additional_languages=additional_languages,
        package_managers=package_managers,
        source_dirs=source_dirs,
        test_dirs=test_dirs,
        docs_dirs=docs_dirs,
        entrypoint_candidates=entrypoints,
        test_commands=test_commands,
        run_commands=run_commands,
        risk_notes=risk_notes,
    )


def _iter_repo_files(root: Path):
    ignored = set(IGNORED_DIR_NAMES)
    for current_path, dirnames, filenames in os.walk(root):
        dirnames[:] = [name for name in dirnames if name not in ignored]
        for filename in filenames:
            yield Path(current_path) / filename


def _count_languages(root: Path) -> Counter[str]:
    counter: Counter[str] = Counter()
    for file_path in _iter_repo_files(root):
        language = EXTENSION_TO_LANGUAGE.get(file_path.suffix.lower())
        if language:
            counter[language] += 1
    return counter


def _resolve_languages(counter: Counter[str]) -> tuple[str, list[str]]:
    if not counter:
        return "unknown", []
    ranked = [language for language, _ in counter.most_common()]
    return ranked[0], ranked[1:]


def _detect_package_managers(root: Path) -> list[str]:
    detected: list[str] = []
    if (root / "package.json").exists():
        detected.append("npm")
    if (root / "pnpm-lock.yaml").exists():
        detected.append("pnpm")
    if (root / "yarn.lock").exists():
        detected.append("yarn")
    if (root / "pyproject.toml").exists():
        detected.append("pyproject")
    if (root / "requirements.txt").exists() or list(root.glob("**/requirements.txt")):
        detected.append("pip")
    if (root / "go.mod").exists():
        detected.append("go")
    if (root / "Cargo.toml").exists():
        detected.append("cargo")
    return _unique(detected)


def _detect_named_dirs(root: Path, candidates: tuple[str, ...]) -> list[str]:
    names = {item.name for item in root.iterdir() if item.is_dir()}
    return [name for name in candidates if name in names]


def _detect_entrypoints(root: Path) -> list[str]:
    candidates: list[str] = []
    # Common top-level Python entry scripts.
    for rel_path in ("main.py", "app.py", "manage.py"):
        if (root / rel_path).exists():
            candidates.append(rel_path)
    # Detect __main__.py inside any immediate child package.
    for child in sorted(root.iterdir()):
        if child.is_dir() and (child / "__main__.py").exists():
            candidates.append(f"{child.name}/__main__.py")
    if (root / "package.json").exists():
        candidates.append("package.json scripts")
    return _unique(candidates)


def _detect_test_commands(
    _root: Path,
    primary_language: str,
    package_managers: list[str],
) -> list[str]:
    commands: list[str] = []
    if primary_language == "python" or "pip" in package_managers or "pyproject" in package_managers:
        commands.append("python3 -m pytest -q")
    if primary_language in {"javascript", "typescript"} and any(
        manager in package_managers for manager in ("npm", "pnpm", "yarn")
    ):
        commands.append("npm test")
    if primary_language == "go":
        commands.append("go test ./...")
    if primary_language == "rust":
        commands.append("cargo test")
    if not commands:
        commands.append("<replace-with-target-repo-test-command>")
    return commands


def _detect_run_commands(
    root: Path,
    primary_language: str,
    package_managers: list[str],
) -> list[str]:
    commands: list[str] = []
    if primary_language == "python":
        if (root / "main.py").exists():
            commands.append("python3 main.py")
        else:
            commands.append("python3 -m <module>")
    if primary_language in {"javascript", "typescript"} and any(
        manager in package_managers for manager in ("npm", "pnpm", "yarn")
    ):
        commands.append("npm run dev")
    if primary_language == "go":
        commands.append("go run .")
    if primary_language == "rust":
        commands.append("cargo run")
    if not commands:
        commands.append("<replace-with-target-repo-run-command>")
    return commands


def _detect_risk_notes(root: Path) -> list[str]:
    notes: list[str] = []
    if (root / ".env").exists():
        notes.append("Repository contains `.env`; avoid exposing secrets in logs.")
    if (root / ".github" / "workflows").exists():
        notes.append("CI workflows exist; keep command examples aligned with CI expectations.")
    if (root / "deploy").exists() or (root / "infra").exists():
        notes.append("Deployment/infrastructure directories detected; require explicit approval before changes.")
    return notes


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    deduplicated: list[str] = []
    for value in values:
        if value not in seen:
            deduplicated.append(value)
            seen.add(value)
    return deduplicated
