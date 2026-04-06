from __future__ import annotations

from .detector import detect_repo_profile
from .models import RenderedArtifact, ScaffoldOptions, ScaffoldResult
from .templates import (
    render_agents,
    render_skill_alias,
    render_skills,
    render_soul,
    render_tools,
)


def generate_scaffold(options: ScaffoldOptions) -> ScaffoldResult:
    target_repo = options.target_repo.resolve()
    output_dir = options.resolved_output_dir().resolve()
    if not target_repo.exists():
        raise FileNotFoundError(f"target repo does not exist: {target_repo}")
    if not target_repo.is_dir():
        raise NotADirectoryError(f"target repo is not a directory: {target_repo}")
    output_dir.mkdir(parents=True, exist_ok=True)

    profile = detect_repo_profile(target_repo)

    outputs: dict[str, str] = {
        "SOUL.md": render_soul(profile),
        "skills.md": render_skills(profile),
        "AGENTS.md": render_agents(profile),
        "TOOLS.md": render_tools(profile),
    }
    if options.include_skill_alias:
        outputs["SKILL.md"] = render_skill_alias()

    artifacts: list[RenderedArtifact] = []
    for filename in options.output_filenames():
        content = outputs[filename]
        out_path = output_dir / filename
        existed_before = out_path.exists()

        if existed_before and not options.overwrite:
            artifacts.append(
                RenderedArtifact(
                    path=out_path,
                    content=content,
                    existed_before=True,
                    written=False,
                    skipped_reason="exists and overwrite=False",
                )
            )
            continue

        if options.dry_run:
            artifacts.append(
                RenderedArtifact(
                    path=out_path,
                    content=content,
                    existed_before=existed_before,
                    written=False,
                    skipped_reason="dry_run=True",
                )
            )
            continue

        out_path.write_text(content, encoding="utf-8")
        artifacts.append(
            RenderedArtifact(
                path=out_path,
                content=content,
                existed_before=existed_before,
                written=True,
                skipped_reason=None,
            )
        )

    return ScaffoldResult(profile=profile, artifacts=artifacts)
