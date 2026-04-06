# TOOLS.md — Command Playbook

This playbook lists practical command patterns for the current repository profile.

## Environment Check
```bash
python3 --version
```

## Suggested Test Commands
```bash
python3 -m pytest -q
```

## Suggested Run/Demo Commands
```bash
python3 -m <module>
```

## Troubleshooting
- If `python` is unavailable, use `python3`.
- If `pytest` is missing, install project dependencies first.
- Prefer targeted checks over full-suite runs when iterating.
