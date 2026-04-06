"""CLI entrypoint for the Agentic DevOps module.

Commands:
    detect    — Detect deploy profile and pipeline from repository.
    generate  — Generate DEVOPS_RUNBOOK.md / DEPLOY_SKILLS.md / MONITOR_CONFIG.md.
    deploy    — Execute a pipeline (dry-run by default).
    monitor   — Run health checks.
    incident  — List / diagnose / resolve incidents.
    rollback  — Rollback a deployment.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .models import DeployProfile
from .pipeline_detector import detect_deploy_profile, detect_pipeline_definition
from .templates import render_deploy_skills, render_devops_runbook, render_monitor_config


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agentic-devops",
        description="Agentic DevOps — automated build, deploy, monitor, incident response.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # -- detect -------------------------------------------------------------
    detect_cmd = sub.add_parser("detect", help="Detect deploy profile from repo.")
    detect_cmd.add_argument("repo", type=Path, help="Path to target repository.")
    detect_cmd.add_argument("--output", default=None, help="Write profile JSON to file.")

    # -- generate -----------------------------------------------------------
    gen_cmd = sub.add_parser("generate", help="Generate DevOps agent config files.")
    gen_group = gen_cmd.add_mutually_exclusive_group(required=True)
    gen_group.add_argument("--profile", type=Path, help="Path to deploy profile JSON.")
    gen_group.add_argument("--repo", type=Path, help="Path to target repository (auto-detect profile).")
    gen_cmd.add_argument("--output-dir", type=Path, default=Path("."), help="Output directory.")
    gen_cmd.add_argument("--overwrite", action="store_true", help="Overwrite existing files.")

    # -- deploy -------------------------------------------------------------
    deploy_cmd = sub.add_parser("deploy", help="Execute deployment pipeline.")
    deploy_cmd.add_argument("repo", type=Path, help="Path to target repository.")
    deploy_cmd.add_argument("--env", default="staging", help="Target environment.")
    deploy_cmd.add_argument("--dry-run", action="store_true", help="Show pipeline without executing.")

    # -- monitor ------------------------------------------------------------
    monitor_cmd = sub.add_parser("monitor", help="Run health checks.")
    monitor_cmd.add_argument("--target", required=True, help="Health check target (URL or host:port).")
    monitor_cmd.add_argument("--type", default="http", choices=["http", "tcp", "command"])
    monitor_cmd.add_argument("--iterations", type=int, default=1, help="Number of check iterations.")

    # -- rollback -----------------------------------------------------------
    rollback_cmd = sub.add_parser("rollback", help="Rollback deployment.")
    rollback_cmd.add_argument("--env", required=True, help="Target environment.")
    rollback_cmd.add_argument("--depth", type=int, default=1, help="Rollback depth.")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "detect":
        return _cmd_detect(args)
    elif args.command == "generate":
        return _cmd_generate(args)
    elif args.command == "deploy":
        return _cmd_deploy(args)
    elif args.command == "monitor":
        return _cmd_monitor(args)
    elif args.command == "rollback":
        return _cmd_rollback(args)
    return 1


# ---------------------------------------------------------------------------
# Sub-commands
# ---------------------------------------------------------------------------

def _cmd_detect(args: argparse.Namespace) -> int:
    profile = detect_deploy_profile(args.repo)
    pipeline = detect_pipeline_definition(args.repo)

    profile_json = profile.model_dump_json(indent=2)
    if args.output:
        Path(args.output).write_text(profile_json, encoding="utf-8")
        print(f"Profile written to {args.output}")
    else:
        print(profile_json)

    print(f"\nDetected: {profile.deploy_method} deployment, CI={profile.ci_system or 'none'}")
    print(f"Environments: {[e.name for e in profile.environments]}")
    print(f"Pipeline stages: {[s.name for s in pipeline.stages]}")
    return 0


def _cmd_generate(args: argparse.Namespace) -> int:
    if args.repo:
        profile = detect_deploy_profile(args.repo)
    else:
        profile_path = args.profile
        if not profile_path.exists():
            print(f"Profile not found: {profile_path}")
            return 1
        profile = DeployProfile.model_validate_json(profile_path.read_text(encoding="utf-8"))

    output_dir: Path = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    files: dict[str, str] = {
        "DEVOPS_RUNBOOK.md": render_devops_runbook(profile),
        "DEPLOY_SKILLS.md": render_deploy_skills(profile),
        "MONITOR_CONFIG.md": render_monitor_config(profile),
    }

    for name, content in files.items():
        out_path = output_dir / name
        if out_path.exists() and not args.overwrite:
            print(f"  SKIP {out_path} (exists, use --overwrite)")
            continue
        out_path.write_text(content, encoding="utf-8")
        print(f"  WROTE {out_path}")

    return 0


def _cmd_deploy(args: argparse.Namespace) -> int:
    from .pipeline_engine import PipelineEngine
    from .policy_engine import DevOpsPolicyEngine

    pipeline = detect_pipeline_definition(args.repo)

    if args.dry_run:
        print(f"Pipeline: {pipeline.name}")
        print(f"Stages ({len(pipeline.stages)}):")
        for stage in pipeline.stages:
            print(f"  - {stage.name} ({stage.stage_type})")
            for cmd in stage.commands:
                print(f"    $ {cmd}")
        return 0

    engine = PipelineEngine(policy_engine=DevOpsPolicyEngine())
    run = engine.execute_pipeline(pipeline, environment=args.env)
    print(f"Run {run.run_id}: {run.status}")
    for stage_exec in run.stages:
        print(f"  {stage_exec.stage_name}: {stage_exec.status}")
    return 0 if run.status == "succeeded" else 1


def _cmd_monitor(args: argparse.Namespace) -> int:
    from .models import HealthCheck
    from .monitor import MonitorEngine

    check = HealthCheck(
        name=f"check-{args.target}",
        check_type=args.type,
        target=args.target,
    )
    monitor = MonitorEngine(checks=[check])

    for _ in range(args.iterations):
        statuses = monitor.run_health_checks()
        for status in statuses:
            print(f"[{status.status}] {status.name}: {json.dumps(status.details)}")

    overall = monitor.evaluate_overall_health()
    print(f"\nOverall: {overall}")
    return 0


def _cmd_rollback(args: argparse.Namespace) -> int:
    from .rollback import RollbackEngine

    engine = RollbackEngine()
    result = engine.execute_rollback(args.env, args.depth)
    if result.get("success"):
        print(f"Rollback successful to: {result.get('to_version', {}).get('version_id', 'unknown')}")
        return 0
    print(f"Rollback failed: {result.get('reason', 'unknown')}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
