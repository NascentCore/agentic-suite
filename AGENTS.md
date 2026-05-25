# Building agentic software

- [Source control](https://jorijn.com/en/blog/leaving-github-for-forgejo/): local self-contained source code management tool.
- [Pi](https://pi.dev/): minimalistic coding agent

## Cursor Cloud specific instructions

This is a pure-Python library (no web server, database, or long-running service). All state is in-memory via Pydantic models.

### Quick reference

| Action | Command |
|--------|---------|
| Install deps | `pip install -e ".[all]"` |
| Lint | `ruff check .` |
| Test (all) | `python3 -m pytest -v` |
| Test (module) | `python3 -m pytest -q amcp/` (also: `agentic_runtime/`, `agentic_devops/`, `tests/`) |
| AMCP demo | `python3 -m amcp.main demo` |
| AMCP self-test | `python3 -m amcp.main self-test` |
| Scaffold CLI | `python3 -m personified_software.openclaw_scaffold.cli /path/to/repo` |
| DevOps detect | `python3 -m agentic_devops.cli detect /path/to/repo` |
| Runtime profile | `python3 -m agentic_runtime.cli profile --app-name NAME --openapi-url URL` |

### Gotchas

- The `amcp/main.py` CLI uses relative imports; run it as `python3 -m amcp.main <cmd>` (not `python3 amcp/main.py`).
- The scaffold CLI (`personified_software.openclaw_scaffold.cli`) writes files (`SOUL.md`, `skills.md`, `TOOLS.md`, `SKILL.md`) into the target repo directory. Clean up with `git checkout -- .` or delete untracked files after testing.
- `~/.local/bin` must be on `PATH` for scripts installed by pip (e.g. `ruff`, `cyclopts`). The update script handles this via `export PATH`.
