# personified_software

Universal OpenClaw-like scaffold toolkit for turning **any repository** into an agent-ready, personified workspace.

## What this product provides

Inside `personified_software/openclaw_scaffold/`, this product provides:

- repository profiling heuristics (`detector.py`)
- scaffold generation engine (`generator.py`)
- CLI entrypoint (`cli.py`)
- template rendering (`templates.py`)
- data models (`models.py`)
- product docs:
  - `README.md`
  - `repo_profile_checklist.md`
  - `instantiation_guide.md`

## Quick start

### 1) Dry-run against any repo

```bash
python3 -m personified_software.openclaw_scaffold.cli /path/to/target/repo --dry-run
```

### 2) Generate scaffold files

```bash
python3 -m personified_software.openclaw_scaffold.cli /path/to/target/repo
```

Generates:

- `SOUL.md`
- `skills.md`
- `AGENTS.md`
- `TOOLS.md`
- optional `SKILL.md` compatibility shim

## Example output in this repository

A generated sample is stored at:

- `personified_software/examples/generated_for_personified/`

You can inspect it as a reference for expected output shape.
