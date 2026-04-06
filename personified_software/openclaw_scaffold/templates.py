from __future__ import annotations

from pathlib import Path

from .models import RepoProfile

_TEMPLATE_DIR = Path(__file__).parent / "template_assets"


def _load_template(name: str) -> str:
    """Load a template file from template_assets/ directory."""
    path = _TEMPLATE_DIR / name
    return path.read_text(encoding="utf-8")


def render_soul(profile: RepoProfile) -> str:
    template = _load_template("TEMPLATE_SOUL.md")
    return template.format(**profile.to_template_context()).strip() + "\n"


def render_skills(profile: RepoProfile) -> str:
    template = _load_template("TEMPLATE_SKILLS.md")
    return template.format(**profile.to_template_context()).strip() + "\n"


def render_agents(profile: RepoProfile) -> str:
    template = _load_template("TEMPLATE_AGENTS.md")
    return template.format(**profile.to_template_context()).strip() + "\n"


def render_tools(profile: RepoProfile) -> str:
    template = _load_template("TEMPLATE_TOOLS.md")
    context = profile.to_template_context()
    raw_test = (
        "\n".join(profile.test_commands) if profile.test_commands
        else "<replace-with-test-commands>"
    )
    raw_run = (
        "\n".join(profile.run_commands) if profile.run_commands
        else "<replace-with-run-commands>"
    )
    context["RAW_TEST_COMMANDS"] = raw_test
    context["RAW_RUN_COMMANDS"] = raw_run
    return template.format(**context).strip() + "\n"


def render_skill_alias() -> str:
    template = _load_template("TEMPLATE_SKILL_ALIAS.md")
    return template.strip() + "\n"


def render_scaffold_readme() -> str:
    """Render the scaffold product README (kept inline — not a per-repo template)."""
    return (
        "# OpenClaw-like Personified Scaffold\n"
        "\n"
        "This directory contains universal scaffold templates and generation tools "
        "for adapting **any repository** into an OpenClaw-like agent workspace.\n"
        "\n"
        "Generated files per target repository:\n"
        "- `SOUL.md`\n"
        "- `skills.md`\n"
        "- `AGENTS.md`\n"
        "- `TOOLS.md`\n"
        "- optional `SKILL.md` compatibility shim\n"
    )


# Keep render_product_readme as an alias for backward compatibility.
render_product_readme = render_scaffold_readme
