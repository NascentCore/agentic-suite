"""Tests for agentic_devops.pipeline_detector — CI/CD discovery."""

from __future__ import annotations

import tempfile
from pathlib import Path

from agentic_devops.pipeline_detector import (
    detect_deploy_profile,
    detect_from_compose,
    detect_from_dockerfile,
    detect_from_k8s_manifests,
    detect_pipeline_definition,
)


class TestDetectDeployProfile:
    def test_empty_repo(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            profile = detect_deploy_profile(Path(td))
            assert profile.app_name
            assert profile.deploy_method == "custom"
            assert profile.ci_system is None
            # Should have default environments
            assert len(profile.environments) >= 1

    def test_docker_repo(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            (Path(td) / "Dockerfile").write_text("FROM python:3.12\n")
            profile = detect_deploy_profile(Path(td))
            assert profile.deploy_method == "docker"
            assert profile.artifact_type == "container_image"

    def test_github_actions(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            workflows = Path(td) / ".github" / "workflows"
            workflows.mkdir(parents=True)
            (workflows / "ci.yml").write_text("name: CI\non: push\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - run: echo test\n")
            profile = detect_deploy_profile(Path(td))
            assert profile.ci_system == "github_actions"


class TestDetectPipelineDefinition:
    def test_default_pipeline(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            pipeline = detect_pipeline_definition(Path(td))
            assert len(pipeline.stages) >= 1
            stage_names = [s.name for s in pipeline.stages]
            assert "build" in stage_names

    def test_docker_adds_build_stage(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            (Path(td) / "Dockerfile").write_text("FROM node:18\n")
            pipeline = detect_pipeline_definition(Path(td))
            stage_names = [s.name for s in pipeline.stages]
            assert "docker_build" in stage_names


class TestDockerfileDetection:
    def test_dockerfile_found(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            (Path(td) / "Dockerfile").write_text("FROM alpine\n")
            stages = detect_from_dockerfile(Path(td))
            assert len(stages) == 1
            assert stages[0].stage_type == "build"
            assert "docker build" in stages[0].commands[0]

    def test_no_dockerfile(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            stages = detect_from_dockerfile(Path(td))
            assert stages == []


class TestComposeDetection:
    def test_compose_found(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            (Path(td) / "docker-compose.yml").write_text("version: '3'\nservices:\n  app:\n    build: .\n")
            stages = detect_from_compose(Path(td))
            assert len(stages) == 1
            assert stages[0].stage_type == "deploy"
            assert stages[0].compensator_commands  # has rollback

    def test_no_compose(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            stages = detect_from_compose(Path(td))
            assert stages == []


class TestK8sDetection:
    def test_k8s_manifests(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            k8s_dir = Path(td) / "k8s"
            k8s_dir.mkdir()
            (k8s_dir / "deployment.yaml").write_text("apiVersion: apps/v1\n")
            stages = detect_from_k8s_manifests(Path(td))
            assert len(stages) == 1
            assert stages[0].requires_approval is True

    def test_no_k8s(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            stages = detect_from_k8s_manifests(Path(td))
            assert stages == []
