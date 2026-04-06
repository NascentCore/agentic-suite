"""Runtime capability discovery — detect what a running application can do.

Discovery strategies (composable):
1. **OpenAPI / Swagger** — parse spec to extract API endpoints as capabilities.
2. **CLI introspection** — parse ``--help`` output to extract sub-commands.
3. **Manual manifest** — read a hand-written YAML/JSON capability manifest.

Each strategy returns ``list[RuntimeCapability]``.  The unified entry-point
``detect_runtime_profile`` merges results from all configured strategies into a
single ``RuntimeProfile``.

Architecture note
-----------------
This mirrors ``personified_software.openclaw_scaffold.detector.detect_repo_profile``
but operates on *running software* rather than static repository files.
"""

from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import (
    RuntimeCapability,
    RuntimeDetectorConfig,
    RuntimeProfile,
    _new_id,
    _utc_now,
)

# ---------------------------------------------------------------------------
# Unified entry-point
# ---------------------------------------------------------------------------


def detect_runtime_profile(config: RuntimeDetectorConfig) -> RuntimeProfile:
    """Merge all configured discovery strategies into one ``RuntimeProfile``."""

    capabilities: list[RuntimeCapability] = []

    # 1) OpenAPI
    if config.openapi_path:
        capabilities.extend(detect_from_openapi_file(config.openapi_path))
    elif config.openapi_url:
        capabilities.extend(detect_from_openapi_url(config.openapi_url))

    # 2) CLI introspection
    if config.cli_command:
        capabilities.extend(detect_from_cli(config.cli_command))

    # 3) Manual manifest
    if config.manifest_path:
        capabilities.extend(detect_from_manifest(Path(config.manifest_path)))

    return RuntimeProfile(
        app_name=config.app_name,
        app_type=config.app_type,
        base_url=config.base_url,
        capabilities=capabilities,
        health_endpoint=config.health_endpoint,
        auth_method=config.auth_method,
        discovered_at=_utc_now(),
    )


# ---------------------------------------------------------------------------
# Strategy: OpenAPI / Swagger
# ---------------------------------------------------------------------------

_HTTP_METHOD_RISK: dict[str, str] = {
    "get": "read_only",
    "head": "read_only",
    "options": "read_only",
    "post": "bounded_write",
    "put": "bounded_write",
    "patch": "bounded_write",
    "delete": "high_impact",
}


def detect_from_openapi_file(spec_path: str) -> list[RuntimeCapability]:
    """Parse a local OpenAPI JSON/YAML file and extract capabilities."""

    path = Path(spec_path)
    if not path.exists():
        return []

    text = path.read_text(encoding="utf-8")
    if path.suffix in (".yaml", ".yml"):
        try:
            import yaml  # type: ignore[import-untyped]

            spec = yaml.safe_load(text)
        except ImportError:
            return []
    else:
        spec = json.loads(text)

    return _extract_openapi_capabilities(spec)


def detect_from_openapi_url(url: str) -> list[RuntimeCapability]:
    """Fetch an OpenAPI spec from a URL and extract capabilities.

    Falls back gracefully — returns empty list on any network error.
    """

    try:
        import urllib.request

        with urllib.request.urlopen(url, timeout=10) as resp:
            spec = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return []
    return _extract_openapi_capabilities(spec)


def _extract_openapi_capabilities(spec: dict[str, Any]) -> list[RuntimeCapability]:
    """Walk ``paths`` in an OpenAPI 3.x spec and yield capabilities."""

    capabilities: list[RuntimeCapability] = []
    paths: dict[str, Any] = spec.get("paths", {})

    for path_str, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue
        for method, operation in path_item.items():
            method_lower = method.lower()
            if method_lower not in _HTTP_METHOD_RISK:
                continue
            if not isinstance(operation, dict):
                continue

            op_id = operation.get("operationId", f"{method_lower}_{path_str}")
            summary = operation.get("summary", "")
            description = operation.get("description", summary)
            risk = _HTTP_METHOD_RISK.get(method_lower, "bounded_write")

            # Build a simplified input schema from parameters + requestBody
            input_schema = _build_input_schema(operation)
            output_schema = _build_output_schema(operation)

            capabilities.append(
                RuntimeCapability(
                    name=op_id,
                    description=description or f"{method.upper()} {path_str}",
                    category="api",
                    input_schema=input_schema,
                    output_schema=output_schema,
                    risk_level=risk,  # type: ignore[arg-type]
                    requires_approval=(risk == "high_impact"),
                    idempotent=(method_lower in ("get", "head", "options", "put")),
                    tags=operation.get("tags", []),
                )
            )

    return capabilities


def _build_input_schema(operation: dict[str, Any]) -> dict[str, Any]:
    """Derive a simplified JSON Schema from OpenAPI parameters + requestBody."""

    properties: dict[str, Any] = {}
    required: list[str] = []

    for param in operation.get("parameters", []):
        name = param.get("name", "unknown")
        schema = param.get("schema", {"type": "string"})
        properties[name] = schema
        if param.get("required"):
            required.append(name)

    # requestBody (simplified: take first media type)
    body = operation.get("requestBody", {})
    content = body.get("content", {})
    for _media_type, media_obj in content.items():
        body_schema = media_obj.get("schema", {})
        properties["body"] = body_schema
        if body.get("required"):
            required.append("body")
        break  # first media type only

    schema: dict[str, Any] = {"type": "object", "properties": properties}
    if required:
        schema["required"] = required
    return schema


def _build_output_schema(operation: dict[str, Any]) -> dict[str, Any]:
    """Derive a simplified output schema from OpenAPI responses (200/201)."""

    responses = operation.get("responses", {})
    for code in ("200", "201", "default"):
        resp = responses.get(code, {})
        content = resp.get("content", {})
        for _media_type, media_obj in content.items():
            return media_obj.get("schema", {})
    return {}


# ---------------------------------------------------------------------------
# Strategy: CLI introspection
# ---------------------------------------------------------------------------


def detect_from_cli(command: str) -> list[RuntimeCapability]:
    """Run ``<command> --help`` and parse output to discover sub-commands.

    This is a best-effort heuristic parser that handles common patterns from
    Click, Typer, argparse, and cyclopts.
    """

    try:
        result = subprocess.run(
            [*command.split(), "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        help_text = result.stdout or result.stderr
    except Exception:
        return []

    return _parse_cli_help(command, help_text)


def _parse_cli_help(command: str, help_text: str) -> list[RuntimeCapability]:
    """Heuristically extract sub-commands from CLI help text."""

    capabilities: list[RuntimeCapability] = []
    # Common patterns: "Commands:", "Available commands:", "Subcommands:"
    in_commands_section = False
    for line in help_text.splitlines():
        stripped = line.strip()
        if re.match(r"^(commands|available commands|subcommands)\s*:?\s*$", stripped, re.IGNORECASE):
            in_commands_section = True
            continue
        if in_commands_section:
            if not stripped:
                in_commands_section = False
                continue
            # Typical format: "  command_name   Description text"
            match = re.match(r"^(\S+)\s+(.*)", stripped)
            if match:
                cmd_name = match.group(1)
                cmd_desc = match.group(2).strip()
                capabilities.append(
                    RuntimeCapability(
                        name=f"{command}_{cmd_name}",
                        description=cmd_desc or f"CLI sub-command: {cmd_name}",
                        category="cli",
                        input_schema={"type": "object", "properties": {}},
                        output_schema={"type": "object", "properties": {"stdout": {"type": "string"}}},
                        risk_level="bounded_write",
                        requires_approval=False,
                        idempotent=False,
                    )
                )
    return capabilities


# ---------------------------------------------------------------------------
# Strategy: Manual manifest (YAML / JSON)
# ---------------------------------------------------------------------------

def detect_from_manifest(manifest_path: Path) -> list[RuntimeCapability]:
    """Read a hand-authored capability manifest (YAML or JSON).

    Expected format::

        capabilities:
          - name: create_user
            description: Create a new user account
            category: api
            risk_level: bounded_write
            input_schema: {type: object, properties: {username: {type: string}}}
            output_schema: {type: object, properties: {user_id: {type: string}}}
    """

    if not manifest_path.exists():
        return []

    text = manifest_path.read_text(encoding="utf-8")
    if manifest_path.suffix in (".yaml", ".yml"):
        try:
            import yaml  # type: ignore[import-untyped]

            data = yaml.safe_load(text)
        except ImportError:
            return []
    else:
        data = json.loads(text)

    raw_caps = data.get("capabilities", [])
    capabilities: list[RuntimeCapability] = []
    for raw in raw_caps:
        if not isinstance(raw, dict):
            continue
        capabilities.append(RuntimeCapability.model_validate(raw))
    return capabilities
