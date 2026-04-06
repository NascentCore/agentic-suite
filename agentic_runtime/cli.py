"""CLI entrypoint for the Agentic Runtime module.

Commands:
    profile   — Detect runtime capabilities and output a profile.
    generate  — Generate RUNTIME_TOOLS.md / RUNTIME_SKILLS.md / RUNTIME_AGENTS.md.
    execute   — Execute a single tool invocation from the command line.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .models import RuntimeDetectorConfig, RuntimeProfile
from .runtime_detector import detect_runtime_profile
from .templates import render_runtime_agents, render_runtime_skills, render_runtime_tools


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agentic-runtime",
        description="Agentic Runtime — natural-language interface for running software.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # -- profile ------------------------------------------------------------
    profile_cmd = sub.add_parser("profile", help="Detect runtime capabilities.")
    profile_cmd.add_argument("--app-name", required=True, help="Application name.")
    profile_cmd.add_argument("--app-type", default="web_service", help="Application type.")
    profile_cmd.add_argument("--openapi-url", default=None, help="OpenAPI spec URL.")
    profile_cmd.add_argument("--openapi-path", default=None, help="OpenAPI spec local file.")
    profile_cmd.add_argument("--cli-command", default=None, help="CLI command for introspection.")
    profile_cmd.add_argument("--manifest", default=None, help="Manual capability manifest path.")
    profile_cmd.add_argument("--base-url", default=None, help="Base URL for web services.")
    profile_cmd.add_argument("--health-endpoint", default=None, help="Health check endpoint.")
    profile_cmd.add_argument("--output", default=None, help="Write profile JSON to file.")

    # -- generate -----------------------------------------------------------
    gen_cmd = sub.add_parser("generate", help="Generate runtime agent config files.")
    gen_cmd.add_argument("--profile", required=True, help="Path to runtime profile JSON.")
    gen_cmd.add_argument("--output-dir", type=Path, default=Path("."), help="Output directory.")
    gen_cmd.add_argument("--overwrite", action="store_true", help="Overwrite existing files.")

    # -- execute ------------------------------------------------------------
    exec_cmd = sub.add_parser("execute", help="Execute a single tool invocation.")
    exec_cmd.add_argument("--profile", required=True, help="Path to runtime profile JSON.")
    exec_cmd.add_argument("--tool", required=True, help="Tool name to invoke.")
    exec_cmd.add_argument("--params", default="{}", help="JSON parameters.")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "profile":
        return _cmd_profile(args)
    elif args.command == "generate":
        return _cmd_generate(args)
    elif args.command == "execute":
        return _cmd_execute(args)
    return 1


# ---------------------------------------------------------------------------
# Sub-commands
# ---------------------------------------------------------------------------

def _cmd_profile(args: argparse.Namespace) -> int:
    config = RuntimeDetectorConfig(
        app_name=args.app_name,
        app_type=args.app_type,
        openapi_url=args.openapi_url,
        openapi_path=args.openapi_path,
        cli_command=args.cli_command,
        manifest_path=args.manifest,
        base_url=args.base_url,
        health_endpoint=args.health_endpoint,
    )
    profile = detect_runtime_profile(config)

    profile_json = profile.model_dump_json(indent=2)
    if args.output:
        Path(args.output).write_text(profile_json, encoding="utf-8")
        print(f"Profile written to {args.output}")
    else:
        print(profile_json)

    print(f"\nDiscovered {len(profile.capabilities)} capabilities for '{profile.app_name}'.")
    return 0


def _cmd_generate(args: argparse.Namespace) -> int:
    profile_path = Path(args.profile)
    if not profile_path.exists():
        print(f"Profile not found: {profile_path}")
        return 1
    profile = RuntimeProfile.model_validate_json(profile_path.read_text(encoding="utf-8"))

    output_dir: Path = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    files: dict[str, str] = {
        "RUNTIME_TOOLS.md": render_runtime_tools(profile),
        "RUNTIME_SKILLS.md": render_runtime_skills(profile),
        "RUNTIME_AGENTS.md": render_runtime_agents(profile),
    }

    for name, content in files.items():
        out_path = output_dir / name
        if out_path.exists() and not args.overwrite:
            print(f"  SKIP {out_path} (exists, use --overwrite)")
            continue
        out_path.write_text(content, encoding="utf-8")
        print(f"  WROTE {out_path}")

    return 0


def _cmd_execute(args: argparse.Namespace) -> int:
    from .executor import RuntimeExecutor
    from .models import ActionRequest
    from .policy_engine import RuntimePolicyEngine
    from .tool_registry import ToolRegistry

    profile_path = Path(args.profile)
    if not profile_path.exists():
        print(f"Profile not found: {profile_path}")
        return 1
    profile = RuntimeProfile.model_validate_json(profile_path.read_text(encoding="utf-8"))

    registry = ToolRegistry(app_name=profile.app_name)
    registry.refresh_from_profile(profile)

    policy_engine = RuntimePolicyEngine()
    executor = RuntimeExecutor(registry=registry, policy_engine=policy_engine)

    tool = registry.get_by_name(args.tool)
    if tool is None:
        print(f"Tool not found: {args.tool}")
        print(f"Available: {[t.name for t in registry.tools]}")
        return 1

    params = json.loads(args.params)
    request = ActionRequest(tool_id=tool.tool_id, parameters=params)
    response = executor.execute(request)

    print(f"Status: {response.status}")
    if response.result:
        print(f"Result: {json.dumps(response.result, indent=2)}")
    if response.error:
        print(f"Error: {json.dumps(response.error, indent=2)}")
    return 0 if response.status == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
