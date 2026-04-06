# OpenClaw-like Universal Scaffold Toolkit

This module provides a reusable scaffold generator that can adapt **any repository** into a personified, OpenClaw-like agent workspace.

## What it generates

For a target repository, the generator can produce:

- `SOUL.md` — repository identity and behavioral constitution
- `skills.md` — read/modify capability contract
- `AGENTS.md` — boot sequence and operating loop
- `TOOLS.md` — command playbook
- `SKILL.md` — optional compatibility shim pointing to `skills.md`

## Why this exists

Different repositories have different structures, languages, and command conventions.  
This toolkit profiles the target repository and injects those facts into standardized templates so agents can onboard quickly and safely.

## Quick start

From repository root:

```bash
python3 -m personified_software.openclaw_scaffold.cli /path/to/target-repo
```

Dry run (render without writing):

```bash
python3 -m personified_software.openclaw_scaffold.cli /path/to/target-repo --dry-run
```

Generate into a custom directory:

```bash
python3 -m personified_software.openclaw_scaffold.cli /path/to/target-repo --output-dir /tmp/scaffold-output
```

Do not generate compatibility alias:

```bash
python3 -m personified_software.openclaw_scaffold.cli /path/to/target-repo --no-skill-alias
```

## CLI options

- `target_repo` (required): repository path to profile.
- `--output-dir`: where to write generated files (default: target repo root).
- `--no-skill-alias`: skip `SKILL.md`.
- `--overwrite`: overwrite existing scaffold files.
- `--dry-run`: render only, do not write files.

## Internal architecture

- `models.py`: profile/result dataclasses and rendering context helpers
- `detector.py`: repository profiling heuristics
- `templates.py`: markdown templates and render functions
- `generator.py`: generation orchestration + safe write behavior
- `cli.py`: command-line interface
- `template_assets/`: reusable raw markdown template files
  - includes optional `TEMPLATE_STYLE.md` for communication-style profiles

## Notes

- The generator intentionally prefers safe defaults and explicit placeholders when confidence is low.
- If the target repository has custom build/test workflows, update generated `TOOLS.md` and `skills.md` after generation.
