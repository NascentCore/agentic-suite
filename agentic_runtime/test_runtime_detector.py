"""Tests for agentic_runtime.runtime_detector — capability discovery."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from agentic_runtime.runtime_detector import (
    _extract_openapi_capabilities,
    _parse_cli_help,
    detect_from_manifest,
    detect_from_openapi_file,
    detect_runtime_profile,
)
from agentic_runtime.models import RuntimeDetectorConfig


# ---------------------------------------------------------------------------
# OpenAPI tests
# ---------------------------------------------------------------------------

SAMPLE_OPENAPI_SPEC: dict = {
    "openapi": "3.0.0",
    "info": {"title": "Test API", "version": "1.0.0"},
    "paths": {
        "/users": {
            "get": {
                "operationId": "list_users",
                "summary": "List all users",
                "parameters": [
                    {"name": "limit", "in": "query", "schema": {"type": "integer"}, "required": False},
                ],
                "responses": {
                    "200": {
                        "content": {
                            "application/json": {
                                "schema": {"type": "array", "items": {"type": "object"}}
                            }
                        }
                    }
                },
            },
            "post": {
                "operationId": "create_user",
                "summary": "Create a user",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"type": "object", "properties": {"name": {"type": "string"}}}
                        }
                    },
                },
                "responses": {"201": {}},
            },
        },
        "/users/{id}": {
            "delete": {
                "operationId": "delete_user",
                "summary": "Delete a user",
                "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}],
                "responses": {"204": {}},
            }
        },
    },
}


class TestOpenAPIExtraction:
    def test_extracts_correct_count(self) -> None:
        caps = _extract_openapi_capabilities(SAMPLE_OPENAPI_SPEC)
        assert len(caps) == 3

    def test_risk_levels(self) -> None:
        caps = {c.name: c for c in _extract_openapi_capabilities(SAMPLE_OPENAPI_SPEC)}
        assert caps["list_users"].risk_level == "read_only"
        assert caps["create_user"].risk_level == "bounded_write"
        assert caps["delete_user"].risk_level == "high_impact"

    def test_approval_for_high_impact(self) -> None:
        caps = {c.name: c for c in _extract_openapi_capabilities(SAMPLE_OPENAPI_SPEC)}
        assert caps["delete_user"].requires_approval is True
        assert caps["list_users"].requires_approval is False

    def test_input_schema_has_parameters(self) -> None:
        caps = {c.name: c for c in _extract_openapi_capabilities(SAMPLE_OPENAPI_SPEC)}
        assert "limit" in caps["list_users"].input_schema.get("properties", {})
        assert "body" in caps["create_user"].input_schema.get("properties", {})

    def test_from_file(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
            json.dump(SAMPLE_OPENAPI_SPEC, f)
            f.flush()
            caps = detect_from_openapi_file(f.name)
        assert len(caps) == 3

    def test_missing_file_returns_empty(self) -> None:
        caps = detect_from_openapi_file("/nonexistent/path.json")
        assert caps == []


# ---------------------------------------------------------------------------
# CLI introspection tests
# ---------------------------------------------------------------------------

SAMPLE_CLI_HELP = """\
Usage: myapp [OPTIONS] COMMAND [ARGS]...

  My application CLI.

Options:
  --help  Show this message and exit.

Commands:
  serve    Start the web server
  migrate  Run database migrations
  seed     Seed initial data
"""


class TestCLIIntrospection:
    def test_parse_commands(self) -> None:
        caps = _parse_cli_help("myapp", SAMPLE_CLI_HELP)
        assert len(caps) == 3
        names = {c.name for c in caps}
        assert "myapp_serve" in names
        assert "myapp_migrate" in names
        assert "myapp_seed" in names

    def test_cli_capabilities_are_cli_category(self) -> None:
        caps = _parse_cli_help("myapp", SAMPLE_CLI_HELP)
        for cap in caps:
            assert cap.category == "cli"

    def test_empty_help(self) -> None:
        caps = _parse_cli_help("myapp", "")
        assert caps == []


# ---------------------------------------------------------------------------
# Manifest tests
# ---------------------------------------------------------------------------


class TestManifestDetection:
    def test_from_json_manifest(self) -> None:
        manifest_data = {
            "capabilities": [
                {
                    "name": "send_email",
                    "description": "Send an email",
                    "category": "message",
                    "risk_level": "bounded_write",
                    "input_schema": {"type": "object", "properties": {"to": {"type": "string"}}},
                },
                {
                    "name": "read_inbox",
                    "description": "Read inbox",
                    "category": "message",
                    "risk_level": "read_only",
                },
            ]
        }
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
            json.dump(manifest_data, f)
            f.flush()
            caps = detect_from_manifest(Path(f.name))
        assert len(caps) == 2
        assert caps[0].name == "send_email"
        assert caps[1].risk_level == "read_only"

    def test_missing_manifest(self) -> None:
        caps = detect_from_manifest(Path("/nonexistent/manifest.json"))
        assert caps == []


# ---------------------------------------------------------------------------
# Unified detect_runtime_profile
# ---------------------------------------------------------------------------


class TestDetectRuntimeProfile:
    def test_from_openapi_file(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
            json.dump(SAMPLE_OPENAPI_SPEC, f)
            f.flush()
            config = RuntimeDetectorConfig(
                app_name="test-api",
                openapi_path=f.name,
                base_url="http://localhost:8000",
            )
            profile = detect_runtime_profile(config)
        assert profile.app_name == "test-api"
        assert len(profile.capabilities) == 3
        assert profile.base_url == "http://localhost:8000"

    def test_empty_config(self) -> None:
        config = RuntimeDetectorConfig(app_name="empty-app")
        profile = detect_runtime_profile(config)
        assert profile.app_name == "empty-app"
        assert profile.capabilities == []
