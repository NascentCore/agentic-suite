# AGENTS.md — OpenClaw-like Agent Boot Instructions

## Boot Sequence
On initial load, read in this order:
1. `SOUL.md`
2. `skills.md`
3. `TOOLS.md`
4. `README.md`
5. domain docs

## Operating Loop
1. Understand request and constraints.
2. Build an explicit plan.
3. Apply minimal scoped edits.
4. Validate with runtime evidence.
5. Return outcomes, risks, and decision points.

## Repository Facts
- Repo name: **{REPO_NAME}**
- Primary language: **{PRIMARY_LANGUAGE}**
- Package managers: {PACKAGE_MANAGERS}

## Key directories
### Source
{SOURCE_DIRS}

### Tests
{TEST_DIRS}

### Docs
{DOCS_DIRS}

## Safety Rules
- Prefer correctness over speed.
- Keep changes reversible.
- Preserve evidence for claims.
- If evidence is missing, state uncertainty explicitly.
