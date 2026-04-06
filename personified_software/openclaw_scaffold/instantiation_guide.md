# Instantiation Guide (Any Repository)

This guide explains how to instantiate the scaffold for any target repository.

## 1) Prepare target repository profile

Collect:
- repository path and name
- primary language and package manager
- source/test/docs directories
- likely entrypoints
- test/run commands
- risk notes (secrets/deploy/infra/permissions)

Use `repo_profile_checklist.md` as the profiling worksheet.

## 2) Run scaffold generator

From this repository root:

```bash
python3 -m personified_software.openclaw_scaffold.cli /path/to/target/repo
```

Common options:

```bash
# preview only
python3 -m personified_software.openclaw_scaffold.cli /path/to/target/repo --dry-run

# output to a specific directory
python3 -m personified_software.openclaw_scaffold.cli /path/to/target/repo --output-dir /path/to/target/repo/.persona

# overwrite existing files
python3 -m personified_software.openclaw_scaffold.cli /path/to/target/repo --overwrite

# skip SKILL.md alias
python3 -m personified_software.openclaw_scaffold.cli /path/to/target/repo --no-skill-alias
```

## 3) Review generated artifacts

Expected files:
- `SOUL.md`
- `skills.md`
- `AGENTS.md`
- `TOOLS.md`
- optional `SKILL.md`

Review for correctness:
- commands exist and execute in target repo context
- directory references are real
- risk notes match repo reality

## 4) Optional refinement

Manual edits are encouraged to improve:
- mission and non-goals wording
- stricter governance rules
- team-specific runbooks and approvals

## 5) Recommended onboarding sequence for agent runtime

1. `SOUL.md`
2. `skills.md`
3. `AGENTS.md`
4. `TOOLS.md`
5. target repo `README.md` and domain docs
