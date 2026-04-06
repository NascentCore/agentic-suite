# TEMPLATE_TOOLS.md

This is the editable source template for generated `TOOLS.md`.

Use placeholders from `models.RepoProfile.to_template_context()`:

- `{REPO_NAME}`
- `{PRIMARY_LANGUAGE}`
- `{PACKAGE_MANAGERS}`
- `{SOURCE_DIRS}`
- `{TEST_DIRS}`
- `{DOCS_DIRS}`
- `{ENTRYPOINT_CANDIDATES}`
- `{TEST_COMMANDS}`
- `{RUN_COMMANDS}`
- `{RISK_NOTES}`
- `{RAW_TEST_COMMANDS}`
- `{RAW_RUN_COMMANDS}`

---

# TOOLS.md — Command Playbook

This playbook lists practical command patterns for the current repository profile.

## Environment Check
```bash
python3 --version
```

## Suggested Test Commands
```bash
{RAW_TEST_COMMANDS}
```

## Suggested Run/Demo Commands
```bash
{RAW_RUN_COMMANDS}
```

## Troubleshooting
- If `python` is unavailable, use `python3`.
- If `pytest` is missing, install project dependencies first.
- Prefer targeted checks over full-suite runs when iterating.
