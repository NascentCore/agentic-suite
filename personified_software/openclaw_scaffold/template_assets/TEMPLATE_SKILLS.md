# skills.md — Repository Read/Modify Skill Contract

## Skill Name
`repo-read-modify-skill`

## Goal
Provide a standard execution contract for OpenClaw-like agents to:
1. understand this repository,
2. modify files safely,
3. validate outcomes with concrete evidence.

## Repository Profile
- Repo name: **{REPO_NAME}**
- Primary language: **{PRIMARY_LANGUAGE}**
- Additional languages: {ADDITIONAL_LANGUAGES}
- Package managers: {PACKAGE_MANAGERS}

## Input Contract
Expect:
1. user intent (bugfix / feature / refactor / docs / research),
2. constraints (risk, compatibility, timeline, testing depth),
3. optional target modules.

## Output Contract
Return:
1. changed files and rationale,
2. verification commands and observed results,
3. residual risks and suggested next actions.

## Core Capabilities
### 1) Read Repository
- Map relevant modules and interfaces before editing.
- Trace control/data flow for the requested behavior.
- Identify invariants and side effects.

### 2) Modify Repository
- Plan changes before writing code.
- Keep edits small, coherent, and reviewable.
- Preserve compatibility unless explicitly told to break it.

### 3) Validate Work
- Execute focused high-signal checks.
- Capture terminal evidence from executed commands.
- Report inconclusive results honestly.

## Standard Workflow
1. **Discover** — locate relevant files and dependencies.
2. **Model** — summarize current behavior and constraints.
3. **Plan** — define minimal change + validation steps.
4. **Implement** — edit files with strict scope control.
5. **Validate** — run targeted checks.
6. **Report** — include evidence, risks, and decisions.

## Hard Guardrails
- Do not claim completion without running planned validations.
- Do not invent commands/files/APIs that do not exist.
- Do not execute destructive operations without explicit approval.

## Suggested Test Commands
{TEST_COMMANDS}

## Suggested Run/Demo Commands
{RUN_COMMANDS}
