"""Pipeline discovery — detect CI/CD configuration from repository files.

Scans a repository for:
1. GitHub Actions workflow files (``.github/workflows/*.yml``)
2. Dockerfiles
3. Docker Compose files (``docker-compose.yml``)
4. Kubernetes manifests (``k8s/``, ``kubernetes/``, ``deploy/``)
5. Common CI config files (Jenkinsfile, .gitlab-ci.yml)

Architecture note
-----------------
Mirrors ``personified_software.openclaw_scaffold.detector`` but profiles
*deployment infrastructure* instead of code structure.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .models import (
    DeployEnvironment,
    DeployProfile,
    PipelineDefinition,
    PipelineStage,
    PipelineTrigger,
    RollbackStrategy,
    _new_id,
    _utc_now,
)


# ---------------------------------------------------------------------------
# Ignored directories (same convention as openclaw_scaffold)
# ---------------------------------------------------------------------------

IGNORED_DIR_NAMES: set[str] = {
    ".git", ".venv", "venv", "node_modules", "__pycache__",
    ".idea", ".vscode", ".cursor", ".pytest_cache", "dist", "build",
}


# ---------------------------------------------------------------------------
# Unified entry-point
# ---------------------------------------------------------------------------


def detect_deploy_profile(repo_path: Path) -> DeployProfile:
    """Scan a repository and build a ``DeployProfile``."""

    repo_path = repo_path.resolve()
    app_name = repo_path.name

    deploy_method = _detect_deploy_method(repo_path)
    ci_system = _detect_ci_system(repo_path)
    environments = _detect_environments(repo_path)
    artifact_type = _detect_artifact_type(repo_path)

    return DeployProfile(
        app_name=app_name,
        repo_path=str(repo_path),
        deploy_method=deploy_method,
        ci_system=ci_system,
        environments=environments,
        artifact_type=artifact_type,
        discovered_at=_utc_now(),
    )


def detect_pipeline_definition(repo_path: Path) -> PipelineDefinition:
    """Detect and build a ``PipelineDefinition`` from repository CI/CD config."""

    repo_path = repo_path.resolve()
    stages: list[PipelineStage] = []

    # Discover stages from various sources
    stages.extend(detect_from_dockerfile(repo_path))
    stages.extend(detect_from_github_actions(repo_path))
    stages.extend(detect_from_compose(repo_path))
    stages.extend(detect_from_k8s_manifests(repo_path))

    # If nothing found, provide a generic template
    if not stages:
        stages = _default_pipeline_stages()

    trigger = _detect_trigger(repo_path)
    rollback = RollbackStrategy()

    return PipelineDefinition(
        name=f"{repo_path.name}-pipeline",
        stages=stages,
        trigger=trigger,
        rollback_strategy=rollback,
    )


# ---------------------------------------------------------------------------
# Detection strategies
# ---------------------------------------------------------------------------

def detect_from_github_actions(repo_path: Path) -> list[PipelineStage]:
    """Parse ``.github/workflows/*.yml`` to extract pipeline stages."""

    workflows_dir = repo_path / ".github" / "workflows"
    if not workflows_dir.exists():
        return []

    stages: list[PipelineStage] = []
    for workflow_file in sorted(workflows_dir.glob("*.yml")) + sorted(workflows_dir.glob("*.yaml")):
        try:
            import yaml  # type: ignore[import-untyped]
            data = yaml.safe_load(workflow_file.read_text(encoding="utf-8"))
        except ImportError:
            # Fallback: extract job names from text
            text = workflow_file.read_text(encoding="utf-8")
            stages.extend(_parse_github_actions_text(workflow_file.name, text))
            continue
        except Exception:
            continue

        if not isinstance(data, dict):
            continue

        jobs = data.get("jobs", {})
        for job_name, job_config in jobs.items():
            if not isinstance(job_config, dict):
                continue
            steps_raw = job_config.get("steps", [])
            commands = []
            for step in steps_raw:
                if isinstance(step, dict) and "run" in step:
                    commands.append(step["run"])

            stage_type = _infer_stage_type(job_name, commands)
            stages.append(PipelineStage(
                name=job_name,
                stage_type=stage_type,
                commands=commands,
                depends_on=_extract_needs(job_config),
            ))

    return stages


def detect_from_dockerfile(repo_path: Path) -> list[PipelineStage]:
    """Detect build stage from Dockerfile presence."""

    dockerfile = repo_path / "Dockerfile"
    if not dockerfile.exists():
        # Check common alternatives
        for alt in ("Dockerfile.prod", "docker/Dockerfile"):
            if (repo_path / alt).exists():
                dockerfile = repo_path / alt
                break
        else:
            return []

    return [PipelineStage(
        name="docker_build",
        stage_type="build",
        commands=[f"docker build -t {repo_path.name}:latest -f {dockerfile.relative_to(repo_path)} ."],
    )]


def detect_from_compose(repo_path: Path) -> list[PipelineStage]:
    """Detect service topology from docker-compose.yml."""

    compose_file = None
    for candidate in ("docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"):
        path = repo_path / candidate
        if path.exists():
            compose_file = path
            break

    if compose_file is None:
        return []

    return [PipelineStage(
        name="compose_up",
        stage_type="deploy",
        commands=[f"docker compose -f {compose_file.name} up -d"],
        compensator_commands=[f"docker compose -f {compose_file.name} down"],
    )]


def detect_from_k8s_manifests(repo_path: Path) -> list[PipelineStage]:
    """Detect deploy stages from Kubernetes manifests."""

    k8s_dirs = []
    for candidate in ("k8s", "kubernetes", "deploy", "manifests"):
        path = repo_path / candidate
        if path.is_dir():
            k8s_dirs.append(path)

    if not k8s_dirs:
        return []

    stages: list[PipelineStage] = []
    for k8s_dir in k8s_dirs:
        stages.append(PipelineStage(
            name=f"k8s_apply_{k8s_dir.name}",
            stage_type="deploy",
            commands=[f"kubectl apply -f {k8s_dir.relative_to(repo_path)}/"],
            compensator_commands=[f"kubectl delete -f {k8s_dir.relative_to(repo_path)}/"],
            requires_approval=True,
        ))

    return stages


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _detect_deploy_method(repo_path: Path) -> str:
    """Infer deploy method from file presence."""
    for candidate in ("k8s", "kubernetes"):
        if (repo_path / candidate).is_dir():
            return "k8s"
    if (repo_path / "Dockerfile").exists():
        return "docker"
    if (repo_path / "serverless.yml").exists() or (repo_path / "serverless.yaml").exists():
        return "serverless"
    return "custom"


def _detect_ci_system(repo_path: Path) -> str | None:
    """Detect which CI system is configured."""
    if (repo_path / ".github" / "workflows").is_dir():
        return "github_actions"
    if (repo_path / ".gitlab-ci.yml").exists():
        return "gitlab_ci"
    if (repo_path / "Jenkinsfile").exists():
        return "jenkins"
    return None


def _detect_environments(repo_path: Path) -> list[DeployEnvironment]:
    """Detect deployment environments from common patterns."""
    envs: list[DeployEnvironment] = []

    # Check k8s namespace hints
    for env_name in ("dev", "staging", "production", "prod"):
        for base in ("k8s", "kubernetes", "deploy", "manifests", "environments"):
            if (repo_path / base / env_name).is_dir():
                protection = "restricted" if env_name in ("production", "prod") else "none"
                envs.append(DeployEnvironment(
                    name=env_name,
                    protection_level=protection,
                ))
                break

    # Default environments if none detected
    if not envs:
        envs = [
            DeployEnvironment(name="dev", protection_level="none"),
            DeployEnvironment(name="staging", protection_level="approval_required"),
            DeployEnvironment(name="production", protection_level="restricted"),
        ]

    return envs


def _detect_artifact_type(repo_path: Path) -> str:
    """Infer artifact type from repository contents."""
    if (repo_path / "Dockerfile").exists():
        return "container_image"
    if (repo_path / "Cargo.toml").exists() or (repo_path / "go.mod").exists():
        return "binary"
    if (repo_path / "package.json").exists():
        return "package"
    return "package"


def _detect_trigger(repo_path: Path) -> PipelineTrigger:
    """Detect pipeline trigger from CI config."""
    if (repo_path / ".github" / "workflows").is_dir():
        return PipelineTrigger(trigger_type="push", branch_pattern="main")
    return PipelineTrigger(trigger_type="manual")


def _infer_stage_type(job_name: str, commands: list[str]) -> str:
    """Heuristically infer stage type from job name and commands."""
    name_lower = job_name.lower()
    cmd_text = " ".join(commands).lower()

    if any(kw in name_lower for kw in ("test", "check", "lint", "validate")):
        return "test"
    if any(kw in name_lower for kw in ("build", "compile", "package")):
        return "build"
    if any(kw in name_lower for kw in ("deploy", "release", "publish")):
        return "deploy"
    if any(kw in name_lower for kw in ("scan", "security", "audit")):
        return "security_scan"
    if any(kw in name_lower for kw in ("notify", "alert", "slack")):
        return "notify"
    if any(kw in name_lower for kw in ("verify", "smoke", "health")):
        return "verify"

    # Fallback: check commands
    if any(kw in cmd_text for kw in ("pytest", "jest", "go test", "cargo test")):
        return "test"
    if any(kw in cmd_text for kw in ("docker build", "npm run build", "go build")):
        return "build"
    if any(kw in cmd_text for kw in ("kubectl", "docker push", "deploy")):
        return "deploy"

    return "build"


def _extract_needs(job_config: dict) -> list[str]:
    """Extract dependency list from GitHub Actions 'needs' field."""
    needs = job_config.get("needs", [])
    if isinstance(needs, str):
        return [needs]
    if isinstance(needs, list):
        return [str(n) for n in needs]
    return []


def _parse_github_actions_text(filename: str, text: str) -> list[PipelineStage]:
    """Fallback parser when PyYAML is not available."""
    stages: list[PipelineStage] = []
    import re
    # Very basic: find lines matching "  job_name:" under "jobs:"
    in_jobs = False
    for line in text.splitlines():
        if line.strip() == "jobs:":
            in_jobs = True
            continue
        if in_jobs and line and not line[0].isspace():
            in_jobs = False
        if in_jobs:
            match = re.match(r"^  (\w[\w-]*):", line)
            if match:
                job_name = match.group(1)
                stages.append(PipelineStage(
                    name=job_name,
                    stage_type=_infer_stage_type(job_name, []),
                ))
    return stages


def _default_pipeline_stages() -> list[PipelineStage]:
    """Provide generic pipeline stages when nothing specific is detected."""
    return [
        PipelineStage(name="build", stage_type="build", commands=["echo 'build step'"]),
        PipelineStage(name="test", stage_type="test", commands=["echo 'test step'"]),
        PipelineStage(name="deploy", stage_type="deploy", commands=["echo 'deploy step'"], requires_approval=True),
        PipelineStage(name="verify", stage_type="verify", commands=["echo 'verify step'"]),
    ]
